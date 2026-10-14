const express = require("express");
const router = express.Router();
const pool = require("../db/pool");
const { decide, MAX_ROUNDS } = require("../utils/negotiate");
const llm = require("../utils/llm");
const { authRequired } = require("../middleware/auth");
const { limitForTier } = require("../utils/trust");

// In-memory chat session state only (round counter, last offer) — ephemeral by nature.
// Durable records (each negotiation round, price locks) are written to PostgreSQL below.
const sessions = new Map();

const LOCK_DURATION_MS = 24 * 60 * 60 * 1000; // 24 hours, as designed in the project spec

async function getVariantWithProduct(variantId) {
  const { rows } = await pool.query(
    `SELECT pv.*, p.name AS product_name, p.floor_price, p.ceiling_price, p.bargaining_enabled, p.seller_id
     FROM product_variants pv JOIN products p ON p.id = pv.product_id
     WHERE pv.id = $1`,
    [variantId]
  );
  return rows[0];
}

// POST /api/negotiate/start  { productId, variantId }
router.post("/start", authRequired, async (req, res) => {
  const userId = req.user.id;
  const { productId, variantId } = req.body;

  const { rows: userRows } = await pool.query("SELECT trust_tier FROM users WHERE id = $1", [userId]);
  const tier = userRows[0]?.trust_tier || "basic";
  const limit = limitForTier(tier);

  // Count DISTINCT products negotiated today, not total messages — so a back-and-forth
  // chat on one product doesn't burn through the daily limit by itself.
  const { rows: countRows } = await pool.query(
    `SELECT COUNT(DISTINCT product_variant_id)::int AS count FROM negotiations
     WHERE user_id = $1 AND created_at::date = CURRENT_DATE`,
    [userId]
  );
  const { rows: alreadyToday } = await pool.query(
    `SELECT DISTINCT product_variant_id FROM negotiations
     WHERE user_id = $1 AND created_at::date = CURRENT_DATE`,
    [userId]
  );
  const alreadyNegotiatedIds = alreadyToday.map((r) => r.product_variant_id);
  const isContinuingExistingProduct = alreadyNegotiatedIds.includes(Number(variantId));

  if (!isContinuingExistingProduct && countRows[0].count >= limit) {
    return res.status(429).json({
      error: `You've used your bargaining chance on ${limit} product${limit > 1 ? "s" : ""} today. Try again tomorrow, or shop this one at the listed price.`,
      limitReached: true,
      limit,
      usedToday: countRows[0].count,
    });
  }

  const variant = await getVariantWithProduct(variantId);
  if (!variant) return res.status(404).json({ error: "Product/variant not found" });
  if (!variant.bargaining_enabled) return res.status(400).json({ error: "Bargaining is not available on this product." });
  if (variant.stock_quantity - variant.reserved_quantity <= 0) return res.status(400).json({ error: "Out of stock." });

  const sessionId = `sess_${userId}_${variantId}_${Date.now()}`;
  const botMessage = llm.greeting(variant.product_name);
  sessions.set(sessionId, {
    userId,
    productId,
    variantId,
    round: 0,
    lastBotPrice: null,
    status: "ongoing",
    messages: [{ from: "bot", text: botMessage }],
    lock: null,
  });

  res.json({
    sessionId,
    botMessage,
    listedPrice: Number(variant.ceiling_price),
    maxRounds: MAX_ROUNDS,
    llmEnabled: llm.isLlmEnabled(),
    dailyLimit: limit,
    usedToday: countRows[0].count,
    isNewProductToday: !isContinuingExistingProduct,
  });
});

// GET /api/negotiate/session/:sessionId
router.get("/session/:sessionId", authRequired, (req, res) => {
  const session = sessions.get(req.params.sessionId);
  if (!session) return res.status(404).json({ error: "Session not found or expired" });
  if (session.userId !== req.user.id) return res.status(403).json({ error: "Not your session." });
  return res.json({ messages: session.messages, status: session.status, lock: session.lock });
});

// POST /api/negotiate/message  { sessionId, message }
router.post("/message", authRequired, async (req, res) => {
  const { sessionId, message } = req.body;
  const session = sessions.get(sessionId);
  if (!session) return res.status(404).json({ error: "Session not found or expired" });
  if (session.userId !== req.user.id) return res.status(403).json({ error: "Not your session." });
  if (session.status !== "ongoing") return res.status(400).json({ error: "This negotiation has already ended." });
  session.messages.push({ from: "user", text: String(message ?? "") });

  function recordBotMessage(text) {
    session.messages.push({ from: "bot", text });
  }

  const variant = await getVariantWithProduct(session.variantId);
  const floor = Number(variant.floor_price);
  const ceiling = Number(variant.ceiling_price);

  const { intent, offeredPrice: parsedOfferedPrice } = await llm.understandMessage(message);
  const isBelowMinimumOffer =
    parsedOfferedPrice !== null && parsedOfferedPrice < ceiling * 0.1;
  const offeredPrice = isBelowMinimumOffer ? null : parsedOfferedPrice;
  const messageText = String(message ?? "").toLowerCase();
  const isClearCancellation = ["cancel", "band karo", "chhod do", "mat karo", "bye", "no deal"]
    .some((phrase) => messageText.includes(phrase));
  const isAcceptancePhrase =
    /\b(?:okay\s+de|ok\s+de|de\s+do|de\s+dijiye|done|theek\s+hai|deal|le\s+lo|confirm|ok\s+done)\b/i.test(messageText) &&
    !/\bno\s+deal\b/i.test(messageText);

  const { rows: negRows } = await pool.query(
    `INSERT INTO negotiations (user_id, product_variant_id, round_number, user_offer, status, llm_used)
     VALUES ($1,$2,$3,$4,'ongoing',$5) RETURNING id`,
    [session.userId, session.variantId, session.round, offeredPrice, llm.isLlmEnabled()]
  );
  const negotiationId = negRows[0].id;

  async function updateNegotiationStatus(status, botCounterOffer) {
    await pool.query(
      "UPDATE negotiations SET status = $1, bot_counter_offer = $2 WHERE id = $3",
      [status, botCounterOffer ?? null, negotiationId]
    );
  }

  async function finalizeAccept(price) {
    session.status = "accepted";
    const botMsg = await llm.generateReply({ decision: "accept", price, productName: variant.product_name, round: session.round });

    const client = await pool.connect();
    let lock = null;
    try {
      await client.query("BEGIN");
      const { rows: v } = await client.query("SELECT stock_quantity, reserved_quantity FROM product_variants WHERE id = $1 FOR UPDATE", [session.variantId]);
      if (v[0].stock_quantity - v[0].reserved_quantity <= 0) {
        await client.query("ROLLBACK");
        return { botMsg: "Deal ho gaya tha lekin stock khatam ho gaya. Sorry!", lock: null, failed: true };
      }
      await client.query("UPDATE product_variants SET reserved_quantity = reserved_quantity + 1 WHERE id = $1", [session.variantId]);
      const expiresAt = new Date(Date.now() + LOCK_DURATION_MS);
      const { rows: lockRows } = await client.query(
        `INSERT INTO price_locks (user_id, product_variant_id, locked_price, expires_at, status)
         VALUES ($1,$2,$3,$4,'active') RETURNING id, expires_at`,
        [session.userId, session.variantId, price, expiresAt]
      );
      await client.query("COMMIT");
      lock = { lockId: lockRows[0].id, expiresAt: lockRows[0].expires_at, price };
      session.lock = lock;
    } catch (e) {
      await client.query("ROLLBACK");
      throw e;
    } finally {
      client.release();
    }
    if (!lock) session.lock = null;
    return { botMsg, lock, failed: false };
  }

  if (isBelowMinimumOffer) {
    const botMsg = `Please poori amount batayiye, jaise ${Math.round(ceiling).toLocaleString("en-IN")}.`;
    await updateNegotiationStatus("ongoing");
    recordBotMessage(botMsg);
    return res.json({ botMessage: botMsg, status: session.status, round: session.round });
  }

  // Plain "accept" (e.g. "ok deal") without restating a number -> accept the bot's last offer
  if (
    offeredPrice === null &&
    !isClearCancellation &&
    (intent === "accept" || isAcceptancePhrase) &&
    session.lastBotPrice !== null &&
    session.lastBotPrice !== undefined
  ) {
    const { botMsg, lock, failed } = await finalizeAccept(session.lastBotPrice);
    await updateNegotiationStatus(failed ? "failed" : "accepted", session.lastBotPrice);
    session.status = failed ? "failed" : "accepted";
    recordBotMessage(botMsg);
    return res.json({
      botMessage: botMsg,
      decision: "accept",
      price: session.lastBotPrice,
      round: session.round,
      maxRounds: MAX_ROUNDS,
      status: failed ? "failed" : "accepted",
      lock,
    });
  }

  const isPricePushback =
    !isClearCancellation &&
    (intent === "question" || intent === "reject" || offeredPrice === null) &&
    (offeredPrice !== null ||
      /\b(?:kam|km|nahi|costly|expensive|cheaper|lower|lowest|less|reduce|discount|sasta|mehenga|pricey)\b|come\s+(?:down|to)|too\s+(?:much|high)|high\s+price|isse\s+(?:kam|km)|kitne\s+mein/i.test(messageText));

  if (
    offeredPrice !== null &&
    !isPricePushback &&
    !isClearCancellation &&
    session.lastBotPrice !== null &&
    session.lastBotPrice !== undefined &&
    offeredPrice >= session.lastBotPrice
  ) {
    const acceptedPrice = session.lastBotPrice;
    const { botMsg, lock, failed } = await finalizeAccept(acceptedPrice);
    await updateNegotiationStatus(failed ? "failed" : "accepted", acceptedPrice);
    session.status = failed ? "failed" : "accepted";
    recordBotMessage(botMsg);
    return res.json({
      botMessage: botMsg,
      decision: "accept",
      price: acceptedPrice,
      round: session.round,
      maxRounds: MAX_ROUNDS,
      status: session.status,
      lock,
    });
  }

  if (offeredPrice !== null && offeredPrice >= ceiling) {
    const botMsg = "Ye listed price hi humara best price hai. Chahein to ise confirm karein ya kam offer karein.";
    await updateNegotiationStatus("ongoing", ceiling);
    recordBotMessage(botMsg);
    return res.json({
      botMessage: botMsg,
      decision: "counter",
      price: ceiling,
      round: session.round,
      maxRounds: MAX_ROUNDS,
      status: "ongoing",
      lock: null,
    });
  }

  if (!isPricePushback && (intent === "question" || intent === "reject" || offeredPrice === null)) {
    let botMsg;
    if (intent === "reject") {
      if (isClearCancellation) {
        session.status = "rejected";
        botMsg = llm.rejectAck();
        await updateNegotiationStatus("rejected");
      } else {
        session.status = "ongoing";
        botMsg = "Theek hai, ek number batayiye jo aap dena chahti hain.";
        await updateNegotiationStatus("ongoing");
      }
    } else {
      botMsg = await llm.questionReply(message, variant.product_name);
      await updateNegotiationStatus("ongoing");
    }
    recordBotMessage(botMsg);
    return res.json({ botMessage: botMsg, status: session.status, round: session.round });
  }

  const previousPrice = session.lastBotPrice;
  const offerBaseline = offeredPrice ?? floor - 1;
  const result = decide(offerBaseline, floor, ceiling, session.round);
  if (offeredPrice === null && previousPrice !== null && previousPrice !== undefined && result.price > previousPrice) {
    result.price = previousPrice;
  }
  session.round += 1;
  session.lastBotPrice = result.price;

  let botMsg = await llm.generateReply({
    decision: result.decision,
    price: result.price,
    productName: variant.product_name,
    round: session.round - 1,
    previousPrice,
  });
  recordBotMessage(botMsg);
  let lock = null;

  if (result.decision === "accept") {
    const outcome = await finalizeAccept(result.price);
    botMsg = outcome.botMsg;
    session.messages[session.messages.length - 1].text = botMsg;
    lock = outcome.lock;
    if (outcome.failed) session.status = "failed";
    await updateNegotiationStatus(outcome.failed ? "failed" : "accepted", result.price);
  } else {
    await updateNegotiationStatus("ongoing", result.price);
  }

  res.json({
    botMessage: botMsg,
    decision: result.decision,
    price: result.price,
    round: session.round,
    maxRounds: MAX_ROUNDS,
    status: session.status,
    lock,
  });
});

module.exports = router;
