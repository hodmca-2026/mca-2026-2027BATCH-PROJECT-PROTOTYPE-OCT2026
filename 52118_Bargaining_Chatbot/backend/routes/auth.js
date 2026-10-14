const express = require("express");
const bcrypt = require("bcryptjs");
const jwt = require("jsonwebtoken");
const pool = require("../db/pool");

const router = express.Router();

function signToken(user) {
  return jwt.sign(
    { id: user.id, name: user.name, email: user.email, role: user.role },
    process.env.JWT_SECRET,
    { expiresIn: "7d" }
  );
}

// POST /api/auth/signup  { name, email, password, phone, role }
// role defaults to 'customer'; only 'customer' or 'seller' can self-register (admin is seeded manually)
router.post("/signup", async (req, res) => {
  const { name, email, password, phone, role } = req.body;
  if (!name || !email || !password) {
    return res.status(400).json({ error: "Name, email and password are required." });
  }
  const safeRole = role === "seller" ? "seller" : "customer";

  try {
    const existing = await pool.query("SELECT id FROM users WHERE email = $1", [email]);
    if (existing.rows.length > 0) {
      return res.status(409).json({ error: "An account with this email already exists." });
    }

    const hash = await bcrypt.hash(password, 10);
    const { rows } = await pool.query(
      `INSERT INTO users (name, email, phone, password_hash, role)
       VALUES ($1,$2,$3,$4,$5) RETURNING id, name, email, role, trust_score, trust_tier`,
      [name, email, phone || null, hash, safeRole]
    );
    const user = rows[0];
    const token = signToken(user);
    res.status(201).json({ token, user });
  } catch (e) {
    console.error(e);
    res.status(500).json({ error: "Signup failed. Please try again." });
  }
});

// POST /api/auth/login  { email, password }
router.post("/login", async (req, res) => {
  const { email, password } = req.body;
  if (!email || !password) return res.status(400).json({ error: "Email and password are required." });

  try {
    const { rows } = await pool.query("SELECT * FROM users WHERE email = $1", [email]);
    const user = rows[0];
    if (!user) return res.status(401).json({ error: "Invalid email or password." });

    const match = await bcrypt.compare(password, user.password_hash);
    if (!match) return res.status(401).json({ error: "Invalid email or password." });

    if (user.is_flagged) {
      return res.status(403).json({ error: "This account has been flagged for review. Contact support." });
    }

    const token = signToken(user);
    delete user.password_hash;
    res.json({ token, user });
  } catch (e) {
    console.error(e);
    res.status(500).json({ error: "Login failed. Please try again." });
  }
});

// GET /api/auth/me  (requires token)
router.get("/me", require("../middleware/auth").authRequired, async (req, res) => {
  const { rows } = await pool.query(
    "SELECT id, name, email, role, trust_score, trust_tier FROM users WHERE id = $1",
    [req.user.id]
  );
  res.json(rows[0]);
});

module.exports = router;
