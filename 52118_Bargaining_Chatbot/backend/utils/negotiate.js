// Deterministic threshold-based negotiation algorithm.
// This is the ONLY place a price decision is made. An LLM (if wired in later)
// is only ever allowed to read the user's message into { intent, offeredPrice }
// and to phrase the reply in natural language — never to pick the price itself.

const CONCESSION_RATES = [0.5, 0.3, 0.15]; // shrinks each round -> bot "gives in" less over time
const DROP_LADDER = [0.5, 0.8, 1.0];
const MAX_ROUNDS = 4;

/**
 * @param {number} offeredPrice - what the user proposed
 * @param {number} floorPrice - seller's minimum acceptable price
 * @param {number} ceilingPrice - the listed price
 * @param {number} round - 0-indexed round number
 * @returns {{ decision: 'accept'|'counter'|'reject_final', price: number, roundsLeft: number }}
 */
function decide(offeredPrice, floorPrice, ceilingPrice, round) {
  if (offeredPrice >= ceilingPrice) {
    return { decision: "accept", price: ceilingPrice, roundsLeft: MAX_ROUNDS - round };
  }

  if (round >= MAX_ROUNDS) {
    // Out of rounds — bot holds firm at floor price as the final offer.
    return { decision: "reject_final", price: floorPrice, roundsLeft: 0 };
  }

  if (offeredPrice < floorPrice) {
    const counter = Math.max(
      floorPrice,
      Math.round(ceilingPrice - (ceilingPrice - floorPrice) * (DROP_LADDER[round] ?? 1.0))
    );
    return { decision: "counter", price: counter, roundsLeft: MAX_ROUNDS - round - 1 };
  }

  // Somewhere between floor and ceiling — meet partway, conceding less each round.
  const gap = ceilingPrice - offeredPrice;
  const rate = CONCESSION_RATES[round] ?? 0.1;
  const counter = Math.round(offeredPrice + gap * rate);

  return { decision: "counter", price: counter, roundsLeft: MAX_ROUNDS - round - 1 };
}

module.exports = { decide, MAX_ROUNDS, CONCESSION_RATES };
