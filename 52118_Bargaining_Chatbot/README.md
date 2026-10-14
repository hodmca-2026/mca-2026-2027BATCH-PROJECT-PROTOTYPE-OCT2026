# Bazaaro — Bargaining Chatbot Fashion E-Commerce

A full-stack e-commerce platform (Men's/Women's clothing) where eligible products
can be **negotiated over chat**, agreed prices are **locked in the cart with an
expiry timer** (instead of auto-charging), and the whole flow — signup/login,
catalog, negotiation, price lock, checkout, seller dashboard, and admin panel —
works end to end on a **real PostgreSQL database**.

Every piece below has been tested against the actual running backend + database,
not just written and assumed to work.

---

## What's Real vs What Needs Your Own Keys

| Feature | Status |
|---|---|
| PostgreSQL database (users, products, negotiations, locks, orders) | ✅ Real — full schema in `backend/db/schema.sql` |
| Auth (signup/login, bcrypt password hashing, JWT sessions) | ✅ Real |
| Role-based access (customer / seller / admin) | ✅ Real — enforced server-side |
| Negotiation algorithm (floor/ceiling threshold logic) | ✅ Real — this is the actual algorithm from the spec, not simplified |
| Price lock + stock reservation + expiry | ✅ Real — persisted in Postgres, background job releases expired locks |
| Seller Dashboard (add products, edit pricing, analytics) | ✅ Real |
| Admin Panel (overview, users, flag/unflag, fraud log) | ✅ Real |
| LLM-powered chat understanding + replies | ⚙️ Works out of the box on a **regex/rule-based fallback**. Add your own `OPENAI_API_KEY` in `backend/.env` to switch on real GPT-based understanding + reply generation — no code changes needed. |
| Payment gateway | ⚙️ Works out of the box in **mock mode** (instant success, no real charge). Add your own `RAZORPAY_KEY_ID` / `RAZORPAY_KEY_SECRET` (free test mode) in `backend/.env` to switch on real Razorpay Checkout — no code changes needed. |

The LLM and payment integrations are written for real API keys — I just can't create
Razorpay/OpenAI accounts or generate working keys on your behalf. Everything else
runs immediately with zero external accounts.

---

## Project Structure

```
bazaaro/
├── backend/
│   ├── db/
│   │   ├── schema.sql       Full Postgres schema
│   │   ├── pool.js          pg connection pool
│   │   └── seed.js          Demo accounts + 8-product catalog
│   ├── middleware/auth.js   JWT verification + role guard
│   ├── jobs/expireLocks.js  Background job: releases expired price locks
│   ├── routes/              auth, products, negotiate, cart, seller, admin
│   ├── utils/
│   │   ├── negotiate.js     The core deterministic pricing algorithm
│   │   ├── nlp.js           Regex-based intent/price extraction (LLM fallback)
│   │   ├── llm.js           Real OpenAI integration (gated by OPENAI_API_KEY)
│   │   ├── payment.js       Real Razorpay integration (gated by RAZORPAY keys)
│   │   ├── replies.js       Template bot replies (used when no LLM key)
│   │   └── trust.js         Trust-tier → daily negotiation limit mapping
│   └── server.js
└── frontend/
    └── src/
        ├── pages/            Home, ProductDetail, Bargain (chat), Deals,
        │                     Login, seller/SellerDashboard, admin/AdminDashboard
        ├── components/       Navbar, Hero, ProductCard, ProductImage
        ├── context/UserContext.jsx   JWT session state
        └── lib/api.js        Fetch helpers, attaches JWT to every request
```

---

## How to Run It

You need **Node.js 18+** and **PostgreSQL** installed and running.

### 1. Create the database

```bash
# Using your own postgres superuser (adjust as needed for your machine):
createuser bazaaro --pwprompt --superuser     # set password to bazaaro123, or your own
createdb bazaaro_db -O bazaaro
```

### 2. Configure environment variables

`backend/.env` is already set up for the defaults above:

```
DATABASE_URL=postgresql://bazaaro:bazaaro123@localhost:5432/bazaaro_db
JWT_SECRET=bazaaro_dev_secret_change_in_production
OPENAI_API_KEY=            # optional — leave blank for the regex fallback
RAZORPAY_KEY_ID=           # optional — leave blank for mock checkout
RAZORPAY_KEY_SECRET=
```

Edit `DATABASE_URL` if your Postgres user/password/db name differ.

### 3. Load the schema and seed demo data

```bash
cd backend
npm install
psql -U bazaaro -h localhost -d bazaaro_db -f db/schema.sql
node db/seed.js
```

This creates 3 demo accounts (password `password123` for all) and 8 products:

| Email | Role |
|---|---|
| customer@bazaaro.com | customer |
| seller@bazaaro.com | seller |
| admin@bazaaro.com | admin |

### 4. Start the backend

```bash
node server.js
```
Runs on `http://localhost:5000`. The console tells you whether LLM/payments are
running live or in fallback/mock mode based on your `.env`.

### 5. Start the frontend

```bash
cd frontend
npm install
npm run dev
```
Open `http://localhost:5173`.

---

## Try It

- **As a customer**: sign up (or log in as `customer@bazaaro.com`) → browse → open
  a product with a "Bargain Available" badge → negotiate → accept → go to **My
  Deals** → checkout before the timer runs out.
- **As a seller**: log in as `seller@bazaaro.com` → Seller Dashboard → add a
  product, edit floor/ceiling pricing, view negotiation analytics.
- **As an admin**: log in as `admin@bazaaro.com` → Admin Panel → view platform
  stats, flag/unflag a user (a flagged user is immediately blocked from logging
  in — try it).

---

## Key Design Points (carried over from the project documentation)

- **The LLM never sets the price.** `utils/llm.js` only extracts intent/price from
  the user's message and phrases the bot's reply — the actual accept/reject/
  counter-price decision always comes from the deterministic algorithm in
  `utils/negotiate.js`. If the LLM call fails or no key is set, it falls back to
  `utils/nlp.js` + `utils/replies.js` automatically, so negotiation never breaks.
- **No true "automatic purchase."** Accepting a price locks it in the cart with an
  expiry (`price_locks` table); checkout is always a separate, explicit step.
- **Floor/ceiling validation is server-side only** — never trusted from the
  frontend or from LLM output.
- **Category scope is Men's/Women's only** — `gender_category` is a DB-level
  CHECK constraint, not just a UI filter.
- **Daily negotiation limits are trust-tier based** (`utils/trust.js`), not a flat
  cap for every user — new accounts get 1/day, trusted accounts get more.

## Known Simplifications

- Redis isn't used; price-lock expiry runs on a `setInterval` job polling
  Postgres every 5 seconds (`jobs/expireLocks.js`). Functionally equivalent for
  this scale — swap in Redis + BullMQ if you need it to scale further.
- Trust scores are seeded with fixed starting values rather than recalculated by
  a scheduled job from live order/lock-abandon history — the scoring formula
  from the documentation is designed but not wired to a recompute job yet.
