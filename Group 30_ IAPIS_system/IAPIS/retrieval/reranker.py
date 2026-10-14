"""
Cross-Encoder Reranker

Re-scores the top-k retrieved reports using a cross-encoder model
that jointly encodes query + document pairs for higher precision.

Course mapping: DL Unit IV — Sequence modeling over paired text.
The reranker is a small Transformer encoder that processes
(query, document) pairs as a sequence classification/regression task.
"""

import logging
from typing import List, Dict

from sentence_transformers import CrossEncoder

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
RERANKER_MODEL_NAME = "cross-encoder/ms-marco-MiniLM-L-6-v2"

# Singleton
_reranker = None


def _get_reranker() -> CrossEncoder:
    """Load the cross-encoder reranker model (singleton)."""
    global _reranker
    if _reranker is None:
        logger.info(f"Loading reranker model: {RERANKER_MODEL_NAME}")
        _reranker = CrossEncoder(RERANKER_MODEL_NAME)
        logger.info("Reranker model loaded")
    return _reranker


def rerank(
    query: str,
    candidates: List[Dict],
    top_n: int = 5,
) -> List[Dict]:
    """
    Rerank candidates using the cross-encoder model.
    
    Each candidate is scored by the cross-encoder on the (query, document) pair.
    Results are sorted by cross-encoder score descending and the top_n are returned.
    
    Args:
        query: The user's query string.
        candidates: List of dicts from hybrid_search, each with 'id', 'document', 'metadata', etc.
        top_n: Number of top results to return after reranking.
    
    Returns:
        List of candidate dicts, sorted by rerank_score descending, each annotated
        with an additional 'rerank_score' field.
    """
    if not candidates:
        return []
    
    reranker = _get_reranker()
    
    # Prepare (query, document) pairs
    pairs = []
    for candidate in candidates:
        doc_text = candidate.get("document", "")
        # Truncate to avoid exceeding model max length (~512 tokens)
        if len(doc_text) > 1500:
            doc_text = doc_text[:1500]
        pairs.append([query, doc_text])
    
    # Score all pairs
    scores = reranker.predict(pairs)
    
    # Annotate candidates with rerank scores
    scored_candidates = []
    for candidate, score in zip(candidates, scores):
        annotated = dict(candidate)
        annotated["rerank_score"] = round(float(score), 4)
        scored_candidates.append(annotated)
    
    # Sort by rerank score descending
    scored_candidates.sort(key=lambda x: x["rerank_score"], reverse=True)
    
    logger.debug(
        f"Reranked {len(candidates)} candidates for '{query}': "
        f"top score={scored_candidates[0]['rerank_score']:.4f}"
    )
    
    return scored_candidates[:top_n]


if __name__ == "__main__":
    # Quick test with dummy data
    from retrieval.hybrid_search import hybrid_search
    
    candidates = hybrid_search("overheating motor incidents", k=10)
    reranked = rerank("overheating motor incidents", candidates, top_n=5)
    
    print(f"\nReranked results for 'overheating motor incidents':")
    for r in reranked:
        print(
            f"  {r['id']}: rerank={r['rerank_score']:.4f} "
            f"hybrid={r.get('hybrid_score', 0):.6f} "
            f"— {r['metadata'].get('title', '')[:60]}"
        )
