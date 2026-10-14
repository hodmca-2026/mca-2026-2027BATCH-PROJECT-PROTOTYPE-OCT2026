const express = require("express");
const router = express.Router();
const pool = require("../db/pool");
const { authRequired, requireRole } = require("../middleware/auth");

router.use(authRequired, requireRole("seller"));

// GET /api/seller/products/stats — per-product performance for this seller
router.get("/products/stats", async (req, res) => {
  const { rows } = await pool.query(
    `SELECT p.id AS "productId",
            p.name,
            p.ceiling_price AS ceiling,
            p.floor_price AS floor,
            COALESCE(v.stock, 0)::int AS stock,
            COALESCE(v.reserved, 0)::int AS reserved,
            COALESCE(n.negotiations, 0)::int AS negotiations,
            COALESCE(n.accepted, 0)::int AS accepted,
            COALESCE(o.orders, 0)::int AS orders
     FROM products p
     LEFT JOIN (
       SELECT product_id,
              SUM(stock_quantity) AS stock,
              SUM(reserved_quantity) AS reserved
       FROM product_variants
       GROUP BY product_id
     ) v ON v.product_id = p.id
     LEFT JOIN (
       SELECT pv.product_id,
              COUNT(n.id) AS negotiations,
              COUNT(n.id) FILTER (WHERE n.status = 'accepted') AS accepted
       FROM product_variants pv
       LEFT JOIN negotiations n ON n.product_variant_id = pv.id
       GROUP BY pv.product_id
     ) n ON n.product_id = p.id
     LEFT JOIN (
       SELECT pv.product_id, COUNT(o.id) AS orders
       FROM product_variants pv
       LEFT JOIN orders o
         ON o.product_variant_id = pv.id AND o.payment_status = 'paid'
       GROUP BY pv.product_id
     ) o ON o.product_id = p.id
     WHERE p.seller_id = $1
     ORDER BY p.created_at DESC`,
    [req.user.id]
  );
  res.json(rows);
});

// GET /api/seller/products — this seller's own catalog
router.get("/products", async (req, res) => {
  const { rows: products } = await pool.query("SELECT * FROM products WHERE seller_id = $1 ORDER BY created_at DESC", [req.user.id]);
  const { rows: variants } = await pool.query(
    `SELECT pv.* FROM product_variants pv JOIN products p ON p.id = pv.product_id WHERE p.seller_id = $1`,
    [req.user.id]
  );
  res.json(products.map((p) => ({
    ...p,
    variants: variants.filter((v) => v.product_id === p.id),
  })));
});

// POST /api/seller/products — create a new product (+ variants)
router.post("/products", async (req, res) => {
  const { name, description, gender_category, category, fabric_type, listed_price, floor_price, ceiling_price, bargaining_enabled, variants } = req.body;

  if (!["men", "women"].includes(gender_category)) {
    return res.status(400).json({ error: "gender_category must be 'men' or 'women'." });
  }
  if (Number(floor_price) > Number(ceiling_price)) {
    return res.status(400).json({ error: "Floor price cannot be greater than ceiling price." });
  }

  const client = await pool.connect();
  try {
    await client.query("BEGIN");
    const { rows } = await client.query(
      `INSERT INTO products (seller_id, name, description, gender_category, category, fabric_type, listed_price, floor_price, ceiling_price, bargaining_enabled)
       VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10) RETURNING id`,
      [req.user.id, name, description, gender_category, category, fabric_type, listed_price, floor_price, ceiling_price, bargaining_enabled ?? true]
    );
    const productId = rows[0].id;
    for (const v of variants || []) {
      await client.query(
        "INSERT INTO product_variants (product_id, size, color, stock_quantity) VALUES ($1,$2,$3,$4)",
        [productId, v.size, v.color, v.stock || 0]
      );
    }
    await client.query("COMMIT");
    res.status(201).json({ id: productId });
  } catch (e) {
    await client.query("ROLLBACK");
    res.status(500).json({ error: "Could not create product." });
  } finally {
    client.release();
  }
});

// PUT /api/seller/products/:id/pricing — update floor/ceiling price & bargaining toggle
router.put("/products/:id/pricing", async (req, res) => {
  const { floor_price, ceiling_price, bargaining_enabled } = req.body;
  const { rows: owned } = await pool.query("SELECT id FROM products WHERE id = $1 AND seller_id = $2", [req.params.id, req.user.id]);
  if (!owned[0]) return res.status(404).json({ error: "Product not found." });

  if (Number(floor_price) > Number(ceiling_price)) {
    return res.status(400).json({ error: "Floor price cannot be greater than ceiling price." });
  }

  await pool.query(
    "UPDATE products SET floor_price = $1, ceiling_price = $2, bargaining_enabled = $3 WHERE id = $4",
    [floor_price, ceiling_price, bargaining_enabled, req.params.id]
  );
  res.json({ success: true });
});

// GET /api/seller/analytics — negotiation + order stats for this seller's products
router.get("/analytics", async (req, res) => {
  const { rows: negotiationStats } = await pool.query(
    `SELECT COUNT(*)::int AS total_negotiations,
            COUNT(*) FILTER (WHERE n.status = 'accepted')::int AS accepted,
            ROUND(AVG(n.user_offer), 2) AS avg_offer
     FROM negotiations n
     JOIN product_variants pv ON pv.id = n.product_variant_id
     JOIN products p ON p.id = pv.product_id
     WHERE p.seller_id = $1`,
    [req.user.id]
  );

  const { rows: orderStats } = await pool.query(
    `SELECT COUNT(*)::int AS total_orders,
            COALESCE(SUM(o.final_price), 0) AS revenue,
            COALESCE(SUM(o.original_price - o.final_price), 0) AS total_discount_given
     FROM orders o
     JOIN product_variants pv ON pv.id = o.product_variant_id
     JOIN products p ON p.id = pv.product_id
     WHERE p.seller_id = $1 AND o.payment_status = 'paid'`,
    [req.user.id]
  );

  res.json({ ...negotiationStats[0], ...orderStats[0] });
});

module.exports = router;
