const express = require("express");
const router = express.Router();
const pool = require("../db/pool");
const { recommendSimilar } = require("../utils/recommender");

// GET /api/products?gender=men&category=Shirts
router.get("/", async (req, res) => {
  const { gender, category } = req.query;
  let query = "SELECT * FROM products WHERE 1=1";
  const params = [];
  if (gender) { params.push(gender); query += ` AND gender_category = $${params.length}`; }
  if (category) { params.push(category); query += ` AND category = $${params.length}`; }
  query += " ORDER BY created_at DESC";

  const { rows: products } = await pool.query(query, params);
  const { rows: variants } = await pool.query("SELECT * FROM product_variants");
  const { rows: ratings } = await pool.query(
    "SELECT product_id, ROUND(AVG(rating)::numeric, 1) AS avg_rating, COUNT(*) AS review_count FROM product_reviews GROUP BY product_id"
  );

  const withVariants = products.map((p) => {
    const rating = ratings.find((r) => r.product_id === p.id);
    return {
      ...p,
      listedPrice: Number(p.listed_price),
      floorPrice: Number(p.floor_price),
      ceilingPrice: Number(p.ceiling_price),
      bargainingEnabled: p.bargaining_enabled,
      gender: p.gender_category,
      fabric: p.fabric_type,
      avgRating: rating ? Number(rating.avg_rating) : null,
      reviewCount: rating ? Number(rating.review_count) : 0,
      variants: variants.filter((v) => v.product_id === p.id).map((v) => ({
        id: v.id, size: v.size, color: v.color, stock: v.stock_quantity, reserved: v.reserved_quantity,
      })),
    };
  });

  res.json(withVariants);
});

// GET /api/products/:id
router.get("/:id", async (req, res) => {
  const { rows } = await pool.query("SELECT * FROM products WHERE id = $1", [req.params.id]);
  const product = rows[0];
  if (!product) return res.status(404).json({ error: "Product not found" });

  const { rows: variants } = await pool.query("SELECT * FROM product_variants WHERE product_id = $1", [product.id]);
  const { rows: ratingRows } = await pool.query(
    "SELECT ROUND(AVG(rating)::numeric, 1) AS avg_rating, COUNT(*) AS review_count FROM product_reviews WHERE product_id = $1",
    [product.id]
  );
  const rating = ratingRows[0];

  res.json({
    ...product,
    listedPrice: Number(product.listed_price),
    floorPrice: Number(product.floor_price),
    ceilingPrice: Number(product.ceiling_price),
    bargainingEnabled: product.bargaining_enabled,
    gender: product.gender_category,
    fabric: product.fabric_type,
    avgRating: rating.avg_rating ? Number(rating.avg_rating) : null,
    reviewCount: Number(rating.review_count) || 0,
    variants: variants.map((v) => ({ id: v.id, size: v.size, color: v.color, stock: v.stock_quantity, reserved: v.reserved_quantity })),
  });
});

// GET /api/products/:id/reviews
router.get("/:id/reviews", async (req, res) => {
  const { rows } = await pool.query(
    "SELECT reviewer_name, rating, comment, verified_purchase, created_at FROM product_reviews WHERE product_id = $1 ORDER BY created_at DESC",
    [req.params.id]
  );
  res.json(rows);
});

// GET /api/products/:id/similar — content-based recommendations (IR Unit VI)
router.get("/:id/similar", async (req, res) => {
  const { rows } = await pool.query("SELECT * FROM products WHERE id = $1", [req.params.id]);
  const target = rows[0];
  if (!target) return res.status(404).json({ error: "Product not found" });

  const { rows: sameGenderProducts } = await pool.query(
    "SELECT * FROM products WHERE gender_category = $1",
    [target.gender_category]
  );

  const recommendations = recommendSimilar(target, sameGenderProducts, 4);

  const { rows: variants } = await pool.query("SELECT * FROM product_variants");
  const enriched = recommendations.map((p) => ({
    ...p,
    listedPrice: Number(p.listed_price),
    gender: p.gender_category,
    fabric: p.fabric_type,
    variants: variants.filter((v) => v.product_id === p.id),
  }));

  res.json(enriched);
});

module.exports = router;
