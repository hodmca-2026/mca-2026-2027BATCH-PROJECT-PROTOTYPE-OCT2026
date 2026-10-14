// Real LLM integration for the negotiation chat.
// If OPENAI_API_KEY is set in .env, this calls the OpenAI API for:
//   1) understanding the user's message (intent + offered price)
//   2) phrasing the bot's decision in natural language
// If no key is set, or the API call fails/times out, it falls back to the
// regex-based logic in utils/nlp.js and utils/replies.js — negotiation never breaks.
//
// IMPORTANT: The LLM never decides the price. It only reads input into
// structured data and turns a decision into words. The actual accept/reject/
// counter-price logic always comes from utils/negotiate.js.

const fallbackNlp = require("./nlp");
const fallbackReplies = require("./replies");

let openai = null;
if (process.env.OPENAI_API_KEY) {
  const OpenAI = require("openai");
  openai = new OpenAI({ apiKey: process.env.OPENAI_API_KEY });
}

const isLlmEnabled = () => !!openai;

async function understandMessage(message) {
  if (!openai) return fallbackNlp.extract(message);

  try {
    const completion = await openai.chat.completions.create({
      model: "gpt-4o-mini",
      response_format: { type: "json_object" },
      messages: [
        {
          role: "system",
          content:
            "You extract structured data from a customer's chat message during a price negotiation. " +
            'Respond ONLY with JSON: { "intent": "offer"|"accept"|"reject"|"question", "offeredPrice": number|null }',
        },
        { role: "user", content: message },
      ],
      temperature: 0,
    });
    const parsed = JSON.parse(completion.choices[0].message.content);
    if (!parsed.intent) throw new Error("Malformed LLM response");
    return { intent: parsed.intent, offeredPrice: parsed.offeredPrice ?? null };
  } catch (e) {
    console.warn("LLM understanding call failed, falling back to regex:", e.message);
    return fallbackNlp.extract(message);
  }
}

async function generateReply({ decision, price, productName, round, previousPrice }) {
  if (!openai) return fallbackReplies.reply({ decision, price, productName, round, previousPrice });

  try {
    const completion = await openai.chat.completions.create({
      model: "gpt-4o-mini",
      messages: [
        {
          role: "system",
          content:
            "You are a friendly shopkeeper bot negotiating the price of a fashion item with a customer. " +
            "Reply in 1-2 short, casual Hinglish sentences confirming the given decision and price. " +
            "For a counter, if the price is below the previous bot price, say you lowered it; if it is the same or higher, say this is your best price or cannot be lowered further. " +
            "Never invent a different price than the one given.",
        },
        {
          role: "user",
          content: `Product: ${productName}. Decision: ${decision}. Price: ₹${price}. Previous bot price: ${previousPrice ?? "none"}.`,
        },
      ],
      temperature: 0.7,
    });
    return completion.choices[0].message.content.trim();
  } catch (e) {
    console.warn("LLM generation call failed, falling back to template:", e.message);
    return fallbackReplies.reply({ decision, price, productName, round, previousPrice });
  }
}

async function answerQuestion(message, productName) {
  if (!openai) return fallbackReplies.questionReply(message);

  try {
    const completion = await openai.chat.completions.create({
      model: "gpt-4o-mini",
      messages: [
        {
          role: "system",
          content:
            `You are a friendly shopkeeper bot for "${productName}" on a fashion e-commerce site. ` +
            "The customer asked a question during a price negotiation (about size, fabric, delivery, returns, etc). " +
            "Answer briefly and helpfully in 1-2 casual Hinglish sentences, then gently prompt them for a price offer. " +
            "Do not invent specific policy numbers you aren't given — keep it general and friendly.",
        },
        { role: "user", content: message },
      ],
      temperature: 0.6,
    });
    return completion.choices[0].message.content.trim();
  } catch (e) {
    console.warn("LLM question-answer call failed, falling back to template:", e.message);
    return fallbackReplies.questionReply(message);
  }
}

module.exports = {
  isLlmEnabled,
  understandMessage,
  generateReply,
  greeting: fallbackReplies.greeting,
  questionReply: answerQuestion,
  rejectAck: fallbackReplies.rejectAck,
};
