-- Bazaaro full schema (PostgreSQL)
-- Run: psql -U postgres -d bazaaro -f schema.sql

DROP TABLE IF EXISTS orders, price_locks, negotiations, product_variants, products, fraud_flags, users, cart_items, wishlist_items, product_reviews CASCADE;

CREATE TABLE users (
  id SERIAL PRIMARY KEY,
  name VARCHAR(120) NOT NULL,
  email VARCHAR(160) UNIQUE NOT NULL,
  phone VARCHAR(20),
  password_hash TEXT NOT NULL,
  role VARCHAR(20) NOT NULL DEFAULT 'customer',
  email_verified BOOLEAN DEFAULT FALSE,
  phone_verified BOOLEAN DEFAULT FALSE,
  trust_score INT DEFAULT 40,
  trust_tier VARCHAR(20) DEFAULT 'new',
  is_flagged BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE products (
  id SERIAL PRIMARY KEY,
  seller_id INT REFERENCES users(id) ON DELETE CASCADE,
  name VARCHAR(160) NOT NULL,
  description TEXT,
  gender_category VARCHAR(10) NOT NULL CHECK (gender_category IN ('men', 'women')),
  category VARCHAR(80),
  fabric_type VARCHAR(80),
  listed_price NUMERIC(10,2) NOT NULL,
  floor_price NUMERIC(10,2) NOT NULL,
  ceiling_price NUMERIC(10,2) NOT NULL,
  bargaining_enabled BOOLEAN DEFAULT TRUE,
  created_at TIMESTAMP DEFAULT NOW(),
  CHECK (floor_price <= ceiling_price)
);

CREATE TABLE product_variants (
  id SERIAL PRIMARY KEY,
  product_id INT REFERENCES products(id) ON DELETE CASCADE,
  size VARCHAR(20),
  color VARCHAR(40),
  stock_quantity INT NOT NULL DEFAULT 0,
  reserved_quantity INT NOT NULL DEFAULT 0
);

CREATE TABLE negotiations (
  id SERIAL PRIMARY KEY,
  user_id INT REFERENCES users(id) ON DELETE CASCADE,
  product_variant_id INT REFERENCES product_variants(id) ON DELETE CASCADE,
  round_number INT DEFAULT 0,
  user_offer NUMERIC(10,2),
  bot_counter_offer NUMERIC(10,2),
  status VARCHAR(20) DEFAULT 'ongoing',
  llm_used BOOLEAN DEFAULT FALSE,
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE price_locks (
  id SERIAL PRIMARY KEY,
  user_id INT REFERENCES users(id) ON DELETE CASCADE,
  product_variant_id INT REFERENCES product_variants(id) ON DELETE CASCADE,
  negotiation_id INT REFERENCES negotiations(id),
  locked_price NUMERIC(10,2) NOT NULL,
  quantity_reserved INT DEFAULT 1,
  created_at TIMESTAMP DEFAULT NOW(),
  expires_at TIMESTAMP NOT NULL,
  status VARCHAR(20) DEFAULT 'active'
);

CREATE TABLE orders (
  id SERIAL PRIMARY KEY,
  user_id INT REFERENCES users(id) ON DELETE CASCADE,
  product_variant_id INT REFERENCES product_variants(id),
  price_lock_id INT REFERENCES price_locks(id),
  final_price NUMERIC(10,2) NOT NULL,
  original_price NUMERIC(10,2),
  was_negotiated BOOLEAN DEFAULT FALSE,
  payment_provider VARCHAR(30),
  payment_order_id VARCHAR(120),
  payment_status VARCHAR(20) DEFAULT 'pending',
  order_status VARCHAR(20) DEFAULT 'placed',
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE fraud_flags (
  id SERIAL PRIMARY KEY,
  user_id INT REFERENCES users(id) ON DELETE CASCADE,
  reason VARCHAR(200),
  created_at TIMESTAMP DEFAULT NOW()
);

-- Regular (non-negotiated) cart — for items added at listed price via "Add to Cart"
CREATE TABLE cart_items (
  id SERIAL PRIMARY KEY,
  user_id INT REFERENCES users(id) ON DELETE CASCADE,
  product_variant_id INT REFERENCES product_variants(id) ON DELETE CASCADE,
  quantity INT NOT NULL DEFAULT 1,
  created_at TIMESTAMP DEFAULT NOW(),
  UNIQUE(user_id, product_variant_id)
);

CREATE TABLE wishlist_items (
  id SERIAL PRIMARY KEY,
  user_id INT REFERENCES users(id) ON DELETE CASCADE,
  product_id INT REFERENCES products(id) ON DELETE CASCADE,
  created_at TIMESTAMP DEFAULT NOW(),
  UNIQUE(user_id, product_id)
);

-- Product reviews (seeded with sample data; real review-writing not exposed yet)
CREATE TABLE product_reviews (
  id SERIAL PRIMARY KEY,
  product_id INT REFERENCES products(id) ON DELETE CASCADE,
  reviewer_name VARCHAR(80) NOT NULL,
  rating INT NOT NULL CHECK (rating BETWEEN 1 AND 5),
  comment TEXT,
  verified_purchase BOOLEAN DEFAULT TRUE,
  created_at TIMESTAMP DEFAULT NOW()
);
