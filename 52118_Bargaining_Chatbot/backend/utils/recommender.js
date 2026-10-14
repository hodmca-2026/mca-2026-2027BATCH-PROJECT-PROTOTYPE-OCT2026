// Content-Based Recommender System (IR Unit VI: "content based recommendation")
//
// Technique: builds a numeric feature vector per product from its attributes
// (gender match, category match, fabric match, normalized price closeness),
// then ranks candidate products by COSINE SIMILARITY to the target product —
// the same core vector-space-model technique used in classic IR ranking.

function buildFeatureVector(product, allCategories, allFabrics, priceRange) {
  const vec = [];

  // one-hot: gender (2 dims)
  vec.push(product.gender_category === "men" ? 1 : 0);
  vec.push(product.gender_category === "women" ? 1 : 0);

  // one-hot: category
  for (const c of allCategories) vec.push(product.category === c ? 1 : 0);

  // one-hot: fabric
  for (const f of allFabrics) vec.push(product.fabric_type === f ? 1 : 0);

  // normalized price (0..1) — closeness in price matters for "similar" products
  const { min, max } = priceRange;
  const norm = max > min ? (product.listed_price - min) / (max - min) : 0.5;
  vec.push(norm);

  return vec;
}

function cosineSimilarity(a, b) {
  let dot = 0, magA = 0, magB = 0;
  for (let i = 0; i < a.length; i++) {
    dot += a[i] * b[i];
    magA += a[i] * a[i];
    magB += b[i] * b[i];
  }
  if (magA === 0 || magB === 0) return 0;
  return dot / (Math.sqrt(magA) * Math.sqrt(magB));
}

/**
 * @param {object} target - the product the user is currently viewing
 * @param {object[]} candidates - all other products to rank against
 * @param {number} topN - how many recommendations to return
 */
function recommendSimilar(target, candidates, topN = 4) {
  const others = candidates.filter((p) => p.id !== target.id);
  if (others.length === 0) return [];

  const allCategories = [...new Set([target, ...others].map((p) => p.category))];
  const allFabrics = [...new Set([target, ...others].map((p) => p.fabric_type))];
  const prices = [target, ...others].map((p) => Number(p.listed_price));
  const priceRange = { min: Math.min(...prices), max: Math.max(...prices) };

  const targetVec = buildFeatureVector(target, allCategories, allFabrics, priceRange);

  const scored = others.map((p) => ({
    product: p,
    score: cosineSimilarity(targetVec, buildFeatureVector(p, allCategories, allFabrics, priceRange)),
  }));

  scored.sort((a, b) => b.score - a.score);
  return scored.slice(0, topN).map((s) => ({ ...s.product, similarity: Number(s.score.toFixed(3)) }));
}

module.exports = { recommendSimilar, cosineSimilarity, buildFeatureVector };
