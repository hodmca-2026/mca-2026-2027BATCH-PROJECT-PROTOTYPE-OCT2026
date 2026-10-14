// Seeds the database with demo accounts and the Men's/Women's product catalog.
// Run with: node db/seed.js
require("dotenv").config();
const bcrypt = require("bcryptjs");
const pool = require("./pool");

const DEMO_PASSWORD = "password123";

async function seed() {
  const hash = await bcrypt.hash(DEMO_PASSWORD, 10);

  console.log("Seeding users...");
  const { rows: users } = await pool.query(
    `INSERT INTO users (name, email, phone, password_hash, role, email_verified, trust_score, trust_tier)
     VALUES
       ('Demo Seller', 'seller@bazaaro.com', '9990000001', $1, 'seller', true, 80, 'trusted'),
       ('Demo Admin', 'admin@bazaaro.com', '9990000002', $1, 'admin', true, 100, 'premium'),
       ('Demo Customer', 'customer@bazaaro.com', '9990000003', $1, 'customer', true, 60, 'basic')
     RETURNING id, role`,
    [hash]
  );
  const seller = users.find((u) => u.role === "seller");
  console.log("Users created:", users.map((u) => u.role).join(", "));

  console.log("Seeding products...");
  const products = [
    ["Handloom Cotton Kurta", "Breathable handloom cotton kurta with mandarin collar.", "men", "Ethnic Wear", "Cotton", 1899, 1200, 1899, true,
      [["M", "Indigo", 8], ["L", "Indigo", 5], ["XL", "Rust", 2]]],
    ["Tailored Linen Shirt", "Slim-fit linen shirt, breathable and crease-resistant.", "men", "Shirts", "Linen", 2499, 1700, 2499, true,
      [["S", "Sand", 6], ["M", "Sand", 10], ["L", "Charcoal", 1]]],
    ["Straight Fit Denim", "Mid-rise straight fit denim, versatile wash.", "men", "Jeans", "Denim", 2199, 1750, 2199, false,
      [["32", "Indigo Wash", 12], ["34", "Indigo Wash", 9]]],
    ["Quilted Bomber Jacket", "Lightweight quilted bomber, ribbed cuffs.", "men", "Jackets", "Polyester Blend", 3499, 2300, 3499, true,
      [["M", "Olive", 3], ["XXL", "Olive", 6]]],
    ["Embroidered Anarkali Kurti", "Flowing Anarkali kurti with thread embroidery.", "women", "Ethnic Wear", "Georgette", 2799, 1900, 2799, true,
      [["S", "Emerald", 4], ["M", "Emerald", 7], ["L", "Wine", 2]]],
    ["Wrap Midi Dress", "Flattering wrap-style midi dress, tie waist.", "women", "Dresses", "Crepe", 2999, 2100, 2999, true,
      [["XS", "Terracotta", 5], ["S", "Terracotta", 9]]],
    ["High-Rise Wide Leg Trouser", "Tailored waistband, side pockets.", "women", "Trousers", "Cotton Blend", 2299, 1600, 2299, true,
      [["28", "Beige", 6], ["30", "Black", 8]]],
    ["Zari-Border Cotton Saree", "Handwoven cotton silk saree, contrast zari border.", "women", "Ethnic Wear", "Cotton Silk", 3999, 2600, 3999, true,
      [["Free Size", "Mustard", 3]]],
  ];

  for (const [name, desc, gender, category, fabric, listed, floor, ceiling, bargEnabled, variants] of products) {
    const { rows } = await pool.query(
      `INSERT INTO products (seller_id, name, description, gender_category, category, fabric_type, listed_price, floor_price, ceiling_price, bargaining_enabled)
       VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10) RETURNING id`,
      [seller.id, name, desc, gender, category, fabric, listed, floor, ceiling, bargEnabled]
    );
    const productId = rows[0].id;
    for (const [size, color, stock] of variants) {
      await pool.query(
        `INSERT INTO product_variants (product_id, size, color, stock_quantity) VALUES ($1,$2,$3,$4)`,
        [productId, size, color, stock]
      );
    }
  }

  console.log(`Seeded ${products.length} products with variants.`);

  console.log("Seeding reviews...");
  const { rows: allProducts } = await pool.query("SELECT id, category FROM products");
  const reviewPool = [
    { rating: 5, comment: "Fabric quality bahut acchi hai, expected se better. Fit bhi perfect tha." },
    { rating: 4, comment: "Achha product hai, thoda delivery slow thi but overall satisfied." },
    { rating: 5, comment: "Bargaining karke sasta mil gaya aur quality bhi top-notch. Highly recommend." },
    { rating: 3, comment: "Theek hai, but color photo se thoda different laga in person." },
    { rating: 5, comment: "Second time order kiya hai is seller se, consistent quality milti hai." },
    { rating: 4, comment: "Size chart accurate tha, M size perfectly fit hua." },
    { rating: 2, comment: "Stitching thoda loose tha ek jagah, baaki sab theek." },
    { rating: 5, comment: "Bahut hi comfortable fabric hai, poore din pehen sakte ho." },
  ];
  const names = ["Rohan S.", "Priya M.", "Amit K.", "Sneha R.", "Vikram T.", "Anjali D.", "Karan P.", "Meera J."];

  for (const p of allProducts) {
    const reviewCount = 3 + Math.floor(Math.random() * 3); // 3-5 reviews per product
    for (let i = 0; i < reviewCount; i++) {
      const r = reviewPool[Math.floor(Math.random() * reviewPool.length)];
      const name = names[Math.floor(Math.random() * names.length)];
      await pool.query(
        `INSERT INTO product_reviews (product_id, reviewer_name, rating, comment, verified_purchase)
         VALUES ($1,$2,$3,$4,true)`,
        [p.id, name, r.rating, r.comment]
      );
    }
  }
  console.log("Reviews seeded.");

  console.log("\nDemo logins (password for all: password123):");
  console.log("  seller@bazaaro.com   (role: seller)");
  console.log("  admin@bazaaro.com    (role: admin)");
  console.log("  customer@bazaaro.com (role: customer)");

  await pool.end();
}

seed().catch((e) => {
  console.error(e);
  process.exit(1);
});
