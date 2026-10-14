// Real Razorpay integration, gated behind RAZORPAY_KEY_ID / RAZORPAY_KEY_SECRET in .env.
// Without keys configured, checkout uses a mock "instant success" confirmation so the
// full flow (lock -> checkout -> order) still works end to end with zero external setup.
// To go live: sign up at https://dashboard.razorpay.com (free, test mode), copy the
// test Key ID/Secret into .env, and the real order-creation + signature verification
// below activates automatically.

let razorpay = null;
const isPaymentLive = () => !!(process.env.RAZORPAY_KEY_ID && process.env.RAZORPAY_KEY_SECRET);

if (isPaymentLive()) {
  const Razorpay = require("razorpay");
  razorpay = new Razorpay({
    key_id: process.env.RAZORPAY_KEY_ID,
    key_secret: process.env.RAZORPAY_KEY_SECRET,
  });
}

/**
 * Creates a payment order for the given amount (in rupees).
 * Returns either a real Razorpay order (to be completed via Razorpay Checkout.js
 * on the frontend) or a mock order that the frontend can auto-confirm.
 */
async function createOrder(amountInRupees, receiptId) {
  if (!razorpay) {
    return {
      live: false,
      orderId: `mock_order_${receiptId}_${Date.now()}`,
      amount: amountInRupees,
      currency: "INR",
    };
  }

  const order = await razorpay.orders.create({
    amount: Math.round(amountInRupees * 100), // paise
    currency: "INR",
    receipt: String(receiptId),
  });
  return { live: true, orderId: order.id, amount: amountInRupees, currency: "INR", keyId: process.env.RAZORPAY_KEY_ID };
}

/** Verifies the payment signature Razorpay Checkout.js returns after a real payment. */
function verifySignature({ orderId, paymentId, signature }) {
  if (!razorpay) return true; // mock mode: nothing to verify
  const crypto = require("crypto");
  const expected = crypto
    .createHmac("sha256", process.env.RAZORPAY_KEY_SECRET)
    .update(`${orderId}|${paymentId}`)
    .digest("hex");
  return expected === signature;
}

module.exports = { isPaymentLive, createOrder, verifySignature };
