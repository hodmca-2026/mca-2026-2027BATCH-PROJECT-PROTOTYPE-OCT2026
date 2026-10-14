require("dotenv").config();
const express = require("express");
const cors = require("cors");

const authRouter = require("./routes/auth");
const productsRouter = require("./routes/products");
const negotiateRouter = require("./routes/negotiate");
const cartRouter = require("./routes/cart");
const sellerRouter = require("./routes/seller");
const adminRouter = require("./routes/admin");
const { startLockExpiryJob } = require("./jobs/expireLocks");
const llm = require("./utils/llm");
const payment = require("./utils/payment");

const app = express();
app.use(cors());
app.use(express.json());

app.use("/api/auth", authRouter);
app.use("/api/products", productsRouter);
app.use("/api/negotiate", negotiateRouter);
app.use("/api/cart", cartRouter);
app.use("/api/seller", sellerRouter);
app.use("/api/admin", adminRouter);

app.get("/api/health", (req, res) => res.json({
  status: "ok",
  llmEnabled: llm.isLlmEnabled(),
  paymentLive: payment.isPaymentLive(),
}));

const PORT = process.env.PORT || 5000;
app.listen(PORT, () => {
  console.log(`Bazaaro backend running on http://localhost:${PORT}`);
  console.log(`LLM: ${llm.isLlmEnabled() ? "LIVE (OpenAI)" : "fallback (regex-based)"}`);
  console.log(`Payments: ${payment.isPaymentLive() ? "LIVE (Razorpay)" : "mock mode"}`);
  startLockExpiryJob();
});
