const express = require("express");
const router = express.Router();
const pool = require("../db/pool");
const { authRequired } = require("../middleware/auth");
const payment = require("../utils/payment");

// GET /api/cart/locks — active/recent price locks for the logged-in user
router.get("/locks", authRequired, async (req, res) => {
  const { rows } = await pool.query(
    `SELECT pl.*, p.name AS product_name, p.listed_price
     FROM price_locks pl
     JOIN product_variants pv ON pv.id = pl.product_variant_id
     JOIN products p ON p.id = pv.product_id
     WHERE pl.user_id = $1
     ORDER BY pl.created_at DESC LIMIT 20`,
    [req.user.id]
  );
  res.json(rows.map((r) => ({
    lockId: r.id,
    productId: r.product_variant_id,
    productName: r.product_name,
    price: Number(r.locked_price),
    expiresAt: new Date(r.expires_at).getTime(),
    status: r.status,
  })));
});

// POST /api/cart/checkout/create-order  { lockId }
// Creates a payment order (real Razorpay order if keys configured, else a mock order)
router.post("/checkout/create-order", authRequired, async (req, res) => {
  const { lockId } = req.body;
  const { rows } = await pool.query("SELECT * FROM price_locks WHERE id = $1 AND user_id = $2", [lockId, req.user.id]);
  const lock = rows[0];
  if (!lock) return res.status(404).json({ error: "Lock not found" });
  if (lock.status === "expired") return res.status(400).json({ error: "This locked price has expired." });
  if (lock.status === "purchased") return res.status(400).json({ error: "Already purchased." });

  const order = await payment.createOrder(Number(lock.locked_price), lockId);
  res.json(order);
});

// POST /api/cart/checkout/confirm  { lockId, orderId, paymentId, signature }
router.post("/checkout/confirm", authRequired, async (req, res) => {
  const { lockId, orderId, paymentId, signature } = req.body;

  const { rows } = await pool.query("SELECT * FROM price_locks WHERE id = $1 AND user_id = $2", [lockId, req.user.id]);
  const lock = rows[0];
  if (!lock) return res.status(404).json({ error: "Lock not found" });
  if (lock.status !== "active") return res.status(400).json({ error: "This lock is no longer active." });

  if (payment.isPaymentLive()) {
    const valid = payment.verifySignature({ orderId, paymentId, signature });
    if (!valid) return res.status(400).json({ error: "Payment verification failed." });
  }

  const client = await pool.connect();
  try {
    await client.query("BEGIN");
    await client.query("UPDATE price_locks SET status = 'purchased' WHERE id = $1", [lockId]);
    const { rows: variantRows } = await client.query("SELECT product_id FROM product_variants WHERE id = $1", [lock.product_variant_id]);
    const { rows: productRows } = await client.query("SELECT listed_price FROM products WHERE id = $1", [variantRows[0].product_id]);

    await client.query(
      `INSERT INTO orders (user_id, product_variant_id, price_lock_id, final_price, original_price, was_negotiated, payment_provider, payment_order_id, payment_status, order_status)
       VALUES ($1,$2,$3,$4,$5,true,$6,$7,'paid','placed')`,
      [req.user.id, lock.product_variant_id, lockId, lock.locked_price, productRows[0].listed_price, payment.isPaymentLive() ? "razorpay" : "mock", orderId]
    );
    await client.query("COMMIT");
  } catch (e) {
    await client.query("ROLLBACK");
    throw e;
  } finally {
    client.release();
  }

  res.json({ success: true, message: "Order placed successfully!", finalPrice: Number(lock.locked_price) });
});

// GET /api/cart/orders — order history for the logged-in user
router.get("/orders", authRequired, async (req, res) => {
  const { rows } = await pool.query(
    `SELECT o.*, p.name AS product_name
     FROM orders o
     JOIN product_variants pv ON pv.id = o.product_variant_id
     JOIN products p ON p.id = pv.product_id
     WHERE o.user_id = $1 ORDER BY o.created_at DESC`,
    [req.user.id]
  );
  res.json(rows);
});

// ===================== Regular (non-negotiated) cart =====================

// GET /api/cart/items — regular cart items (added via "Add to Cart", not bargained)
router.get("/items", authRequired, async (req, res) => {
  const { rows } = await pool.query(
    `SELECT ci.id AS cart_item_id, ci.quantity, pv.id AS variant_id, pv.size, pv.color,
            pv.stock_quantity, pv.reserved_quantity, p.id AS product_id, p.name, p.listed_price
     FROM cart_items ci
     JOIN product_variants pv ON pv.id = ci.product_variant_id
     JOIN products p ON p.id = pv.product_id
     WHERE ci.user_id = $1
     ORDER BY ci.created_at DESC`,
    [req.user.id]
  );
  res.json(rows.map((r) => ({
    cartItemId: r.cart_item_id,
    productId: r.product_id,
    variantId: r.variant_id,
    name: r.name,
    size: r.size,
    color: r.color,
    price: Number(r.listed_price),
    quantity: r.quantity,
    inStock: r.stock_quantity - r.reserved_quantity > 0,
  })));
});

// POST /api/cart/items  { variantId, quantity }
router.post("/items", authRequired, async (req, res) => {
  const { variantId, quantity = 1 } = req.body;
  if (!variantId) return res.status(400).json({ error: "variantId is required" });

  const { rows: v } = await pool.query("SELECT * FROM product_variants WHERE id = $1", [variantId]);
  if (!v[0]) return res.status(404).json({ error: "Variant not found" });
  if (v[0].stock_quantity - v[0].reserved_quantity <= 0) {
    return res.status(400).json({ error: "Out of stock." });
  }

  await pool.query(
    `INSERT INTO cart_items (user_id, product_variant_id, quantity)
     VALUES ($1,$2,$3)
     ON CONFLICT (user_id, product_variant_id)
     DO UPDATE SET quantity = cart_items.quantity + EXCLUDED.quantity`,
    [req.user.id, variantId, quantity]
  );
  res.json({ success: true });
});

// PUT /api/cart/items/:id  { quantity }
router.put("/items/:id", authRequired, async (req, res) => {
  const { quantity } = req.body;
  if (!quantity || quantity < 1) return res.status(400).json({ error: "quantity must be at least 1" });
  const { rowCount } = await pool.query(
    "UPDATE cart_items SET quantity = $1 WHERE id = $2 AND user_id = $3",
    [quantity, req.params.id, req.user.id]
  );
  if (!rowCount) return res.status(404).json({ error: "Cart item not found" });
  res.json({ success: true });
});

// DELETE /api/cart/items/:id
router.delete("/items/:id", authRequired, async (req, res) => {
  await pool.query("DELETE FROM cart_items WHERE id = $1 AND user_id = $2", [req.params.id, req.user.id]);
  res.json({ success: true });
});

// POST /api/cart/items/:id/checkout/create-order — checkout a regular (non-bargained) cart item
router.post("/items/:id/checkout/create-order", authRequired, async (req, res) => {
  const { rows } = await pool.query(
    `SELECT ci.*, p.listed_price FROM cart_items ci
     JOIN product_variants pv ON pv.id = ci.product_variant_id
     JOIN products p ON p.id = pv.product_id
     WHERE ci.id = $1 AND ci.user_id = $2`,
    [req.params.id, req.user.id]
  );
  const item = rows[0];
  if (!item) return res.status(404).json({ error: "Cart item not found" });

  const total = Number(item.listed_price) * item.quantity;
  const order = await payment.createOrder(total, `cart_${item.id}`);
  res.json(order);
});

// POST /api/cart/items/:id/checkout/confirm  { orderId, paymentId, signature }
router.post("/items/:id/checkout/confirm", authRequired, async (req, res) => {
  const { orderId, paymentId, signature } = req.body;
  const { rows } = await pool.query(
    `SELECT ci.*, p.listed_price FROM cart_items ci
     JOIN product_variants pv ON pv.id = ci.product_variant_id
     JOIN products p ON p.id = pv.product_id
     WHERE ci.id = $1 AND ci.user_id = $2`,
    [req.params.id, req.user.id]
  );
  const item = rows[0];
  if (!item) return res.status(404).json({ error: "Cart item not found" });

  if (payment.isPaymentLive()) {
    const valid = payment.verifySignature({ orderId, paymentId, signature });
    if (!valid) return res.status(400).json({ error: "Payment verification failed." });
  }

  const total = Number(item.listed_price) * item.quantity;
  await pool.query(
    `INSERT INTO orders (user_id, product_variant_id, final_price, original_price, was_negotiated, payment_provider, payment_order_id, payment_status, order_status)
     VALUES ($1,$2,$3,$3,false,$4,$5,'paid','placed')`,
    [req.user.id, item.product_variant_id, total, payment.isPaymentLive() ? "razorpay" : "mock", orderId]
  );
  await pool.query("DELETE FROM cart_items WHERE id = $1", [item.id]);

  res.json({ success: true, message: "Order placed successfully!", finalPrice: total });
});

// ===================== Wishlist =====================

// GET /api/cart/wishlist
router.get("/wishlist", authRequired, async (req, res) => {
  const { rows } = await pool.query(
    `SELECT w.id AS wishlist_id, p.id AS product_id, p.name, p.listed_price, p.category, p.gender_category
     FROM wishlist_items w JOIN products p ON p.id = w.product_id
     WHERE w.user_id = $1 ORDER BY w.created_at DESC`,
    [req.user.id]
  );
  res.json(rows.map((r) => ({
    wishlistId: r.wishlist_id,
    productId: r.product_id,
    name: r.name,
    price: Number(r.listed_price),
    category: r.category,
    gender: r.gender_category,
  })));
});

// POST /api/cart/wishlist  { productId }
router.post("/wishlist", authRequired, async (req, res) => {
  const { productId } = req.body;
  if (!productId) return res.status(400).json({ error: "productId is required" });
  await pool.query(
    `INSERT INTO wishlist_items (user_id, product_id) VALUES ($1,$2) ON CONFLICT DO NOTHING`,
    [req.user.id, productId]
  );
  res.json({ success: true });
});

// DELETE /api/cart/wishlist/:productId
router.delete("/wishlist/:productId", authRequired, async (req, res) => {
  await pool.query("DELETE FROM wishlist_items WHERE user_id = $1 AND product_id = $2", [req.user.id, req.params.productId]);
  res.json({ success: true });
});

module.exports = router;
