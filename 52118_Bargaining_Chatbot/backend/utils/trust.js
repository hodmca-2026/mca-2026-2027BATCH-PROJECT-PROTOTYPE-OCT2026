const TIER_LIMITS = {
  new: 3,
  basic: 5,
  trusted: 8,
  premium: 15,
};

function limitForTier(tier) {
  return TIER_LIMITS[tier] ?? TIER_LIMITS.basic;
}

module.exports = { TIER_LIMITS, limitForTier };
