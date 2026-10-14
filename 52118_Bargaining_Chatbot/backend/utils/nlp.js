// NLP intent/price extraction.
// Numbers are extracted with regex (unambiguous — no need for a classifier).
// For text without a number, intent is classified using the multinomial
// Naive Bayes language model (utils/languageModel.js) instead of a fixed
// keyword list — this generalizes to phrasings never explicitly listed.
// This entire module is the LLM's fallback path (see Project_Build_Prompt_LLM.md);
// it runs standalone when no OPENAI_API_KEY is configured.

const { model } = require("./languageModel");

function extract(message) {
  const text = message.toLowerCase().trim();

  const numberMatch = text.match(/\d+(\.\d+)?/);
  const offeredPrice = numberMatch ? parseFloat(numberMatch[0]) : null;

  if (offeredPrice !== null) {
    return { intent: "offer", offeredPrice, method: "regex" };
  }

  const { label, scores } = model.classify(text);
  return { intent: label || "question", offeredPrice: null, method: "naive_bayes", scores };
}

module.exports = { extract };
