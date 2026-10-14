const express = require("express");
const router = express.Router();
const pool = require("../db/pool");
const { authRequired, requireRole } = require("../middleware/auth");

router.use(authRequired, requireRole("admin"));

// GET /api/admin/overview — platform-wide bargaining health metrics
router.get("/overview", async (req, res) => {
  const { rows: users } = await pool.query("SELECT COUNT(*)::int AS total_users, COUNT(*) FILTER (WHERE role='seller')::int AS sellers, COUNT(*) FILTER (WHERE is_flagged)::int AS flagged FROM users");
  const { rows: negotiations } = await pool.query("SELECT COUNT(*)::int AS total, COUNT(*) FILTER (WHERE status='accepted')::int AS accepted FROM negotiations");
  const { rows: orders } = await pool.query("SELECT COUNT(*)::int AS total_orders, COALESCE(SUM(final_price),0) AS gmv FROM orders WHERE payment_status='paid'");
  res.json({ ...users[0], ...negotiations[0], ...orders[0] });
});

// GET /api/admin/users — all users with basic trust/fraud info
router.get("/users", async (req, res) => {
  const { rows } = await pool.query(
    "SELECT id, name, email, role, trust_score, trust_tier, is_flagged, created_at FROM users ORDER BY created_at DESC"
  );
  res.json(rows);
});

// GET /api/admin/fraud-flags
router.get("/fraud-flags", async (req, res) => {
  const { rows } = await pool.query(
    `SELECT f.*, u.name, u.email FROM fraud_flags f JOIN users u ON u.id = f.user_id ORDER BY f.created_at DESC`
  );
  res.json(rows);
});

// POST /api/admin/users/:id/flag  { reason }
router.post("/users/:id/flag", async (req, res) => {
  const { reason } = req.body;
  await pool.query("UPDATE users SET is_flagged = true WHERE id = $1", [req.params.id]);
  await pool.query("INSERT INTO fraud_flags (user_id, reason) VALUES ($1, $2)", [req.params.id, reason || "Manually flagged by admin"]);
  res.json({ success: true });
});

// POST /api/admin/users/:id/unflag
router.post("/users/:id/unflag", async (req, res) => {
  await pool.query("UPDATE users SET is_flagged = false WHERE id = $1", [req.params.id]);
  res.json({ success: true });
});

// GET /api/admin/negotiations — recent negotiations across the platform
router.get("/negotiations", async (req, res) => {
  const { rows } = await pool.query(
    `SELECT n.*, u.name AS user_name, p.name AS product_name
     FROM negotiations n
     JOIN users u ON u.id = n.user_id
     JOIN product_variants pv ON pv.id = n.product_variant_id
     JOIN products p ON p.id = pv.product_id
     ORDER BY n.created_at DESC LIMIT 50`
  );
  res.json(rows);
});

module.exports = router;
