const BASE = "/api";

function getToken() {
  return localStorage.getItem("bazaaro_token");
}

async function req(path, options = {}) {
  const token = getToken();
  const res = await fetch(`${BASE}${path}`, {
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    ...options,
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) {
    if (res.status === 401) {
      localStorage.removeItem("bazaaro_token");
      localStorage.removeItem("bazaaro_user");
      window.location.assign("/login");
    }
    const err = new Error(data.error || "Something went wrong");
    err.data = data; // preserves fields like limitReached, dailyLimit, usedToday
    err.status = res.status;
    throw err;
  }
  return data;
}

export const api = {
  // auth
  signup: (body) => req("/auth/signup", { method: "POST", body: JSON.stringify(body) }),
  login: (body) => req("/auth/login", { method: "POST", body: JSON.stringify(body) }),
  me: () => req("/auth/me"),

  // catalog
  getProducts: (params = {}) => {
    const qs = new URLSearchParams(params).toString();
    return req(`/products${qs ? `?${qs}` : ""}`);
  },
  getProduct: (id) => req(`/products/${id}`),
  getSimilarProducts: (id) => req(`/products/${id}/similar`),
  getReviews: (id) => req(`/products/${id}/reviews`),

  // regular cart (non-negotiated)
  getCartItems: () => req("/cart/items"),
  addToCart: (variantId, quantity = 1) => req("/cart/items", { method: "POST", body: JSON.stringify({ variantId, quantity }) }),
  updateCartItem: (cartItemId, quantity) => req(`/cart/items/${cartItemId}`, { method: "PUT", body: JSON.stringify({ quantity }) }),
  removeCartItem: (cartItemId) => req(`/cart/items/${cartItemId}`, { method: "DELETE" }),
  createCartItemOrder: (cartItemId) => req(`/cart/items/${cartItemId}/checkout/create-order`, { method: "POST" }),
  confirmCartItemOrder: (cartItemId, body) => req(`/cart/items/${cartItemId}/checkout/confirm`, { method: "POST", body: JSON.stringify(body) }),

  // wishlist
  getWishlist: () => req("/cart/wishlist"),
  addToWishlist: (productId) => req("/cart/wishlist", { method: "POST", body: JSON.stringify({ productId }) }),
  removeFromWishlist: (productId) => req(`/cart/wishlist/${productId}`, { method: "DELETE" }),

  // negotiation
  startNegotiation: (body) => req("/negotiate/start", { method: "POST", body: JSON.stringify(body) }),
  getNegotiationSession: (sessionId) => req(`/negotiate/session/${encodeURIComponent(sessionId)}`),
  sendMessage: (body) => req("/negotiate/message", { method: "POST", body: JSON.stringify(body) }),

  // cart / checkout
  getLocks: () => req("/cart/locks"),
  createPaymentOrder: (lockId) => req("/cart/checkout/create-order", { method: "POST", body: JSON.stringify({ lockId }) }),
  confirmCheckout: (body) => req("/cart/checkout/confirm", { method: "POST", body: JSON.stringify(body) }),
  getOrders: () => req("/cart/orders"),

  // seller
  sellerProducts: () => req("/seller/products"),
  sellerProductStats: () => req("/seller/products/stats"),
  sellerCreateProduct: (body) => req("/seller/products", { method: "POST", body: JSON.stringify(body) }),
  sellerUpdatePricing: (id, body) => req(`/seller/products/${id}/pricing`, { method: "PUT", body: JSON.stringify(body) }),
  sellerAnalytics: () => req("/seller/analytics"),

  // admin
  adminOverview: () => req("/admin/overview"),
  adminUsers: () => req("/admin/users"),
  adminFraudFlags: () => req("/admin/fraud-flags"),
  adminFlagUser: (id, reason) => req(`/admin/users/${id}/flag`, { method: "POST", body: JSON.stringify({ reason }) }),
  adminUnflagUser: (id) => req(`/admin/users/${id}/unflag`, { method: "POST" }),
  adminNegotiations: () => req("/admin/negotiations"),
};
