"""
Hybrid Search — Reciprocal Rank Fusion of Dense + BM25 Retrieval

Combines dense (neural embedding) search with BM25 (statistical language model)
search using Reciprocal Rank Fusion (RRF).

This implements "ranking with language models" (BM25 = probabilistic LM side)
fused with the neural embedding side, per IR Unit IV.

The alpha parameter controls the weighting: higher alpha favors dense results.
"""

import logging
from typing import List, Dict

from retrieval.embed_store import dense_search
from retrieval.bm25_search import bm25_search

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# RRF constant (standard value from the literature)
RRF_K = 60


def hybrid_search(
    query: str,
    k: int = 10,
    alpha: float = 0.5,
    dense_k: int = 20,
    bm25_k: int = 20,
) -> List[Dict]:
    """
    Hybrid search combining dense and BM25 retrieval via Reciprocal Rank Fusion.
    
    RRF score for each document = alpha * (1 / (RRF_K + dense_rank))
                                 + (1-alpha) * (1 / (RRF_K + bm25_rank))
    
    Documents appearing in only one result set get 0 contribution from the other.
    
    Args:
        query: Natural language query string.
        k: Number of final results to return.
        alpha: Weight for dense search (0.0 = BM25 only, 1.0 = dense only).
        dense_k: Number of candidates to fetch from dense search.
        bm25_k: Number of candidates to fetch from BM25 search.
    
    Returns:
        List of dicts: [{id, hybrid_score, dense_score, bm25_score, document, metadata}, ...]
        sorted by hybrid_score descending.
    """
    # Fetch candidates from both retrievers
    dense_results = dense_search(query, k=dense_k)
    bm25_results = bm25_search(query, k=bm25_k)
    
    # Build rank maps
    dense_rank = {}
    dense_scores = {}
    dense_docs = {}
    dense_meta = {}
    for rank, result in enumerate(dense_results):
        doc_id = result["id"]
        dense_rank[doc_id] = rank + 1
        dense_scores[doc_id] = result["score"]
        dense_docs[doc_id] = result.get("document", "")
        dense_meta[doc_id] = result.get("metadata", {})
    
    bm25_rank = {}
    bm25_scores = {}
    bm25_docs = {}
    bm25_meta = {}
    for rank, result in enumerate(bm25_results):
        doc_id = result["id"]
        bm25_rank[doc_id] = rank + 1
        bm25_scores[doc_id] = result["score"]
        bm25_docs[doc_id] = result.get("document", "")
        bm25_meta[doc_id] = result.get("metadata", {})
    
    # Compute RRF scores for all unique document IDs
    all_ids = set(dense_rank.keys()) | set(bm25_rank.keys())
    
    rrf_scores = {}
    for doc_id in all_ids:
        dense_contribution = 0.0
        bm25_contribution = 0.0
        
        if doc_id in dense_rank:
            dense_contribution = alpha * (1.0 / (RRF_K + dense_rank[doc_id]))
        
        if doc_id in bm25_rank:
            bm25_contribution = (1.0 - alpha) * (1.0 / (RRF_K + bm25_rank[doc_id]))
        
        rrf_scores[doc_id] = dense_contribution + bm25_contribution
    
    # Sort by RRF score
    sorted_ids = sorted(rrf_scores.keys(), key=lambda x: rrf_scores[x], reverse=True)
    
    # Build output
    results = []
    for doc_id in sorted_ids[:k]:
        # Prefer metadata from whichever retriever had it
        metadata = dense_meta.get(doc_id, bm25_meta.get(doc_id, {}))
        document = dense_docs.get(doc_id, bm25_docs.get(doc_id, ""))
        
        results.append({
            "id": doc_id,
            "hybrid_score": round(rrf_scores[doc_id], 6),
            "dense_score": dense_scores.get(doc_id, 0.0),
            "bm25_score": bm25_scores.get(doc_id, 0.0),
            "document": document,
            "metadata": metadata,
        })
    
    logger.debug(
        f"Hybrid search for '{query}': {len(dense_results)} dense + "
        f"{len(bm25_results)} BM25 -> {len(results)} fused results"
    )
    
    return results


if __name__ == "__main__":
    # Quick test
    results = hybrid_search("overheating motor incidents", k=5)
    print(f"\nHybrid search: 'overheating motor incidents' -> {len(results)} results")
    for r in results:
        print(
            f"  {r['id']}: hybrid={r['hybrid_score']:.6f} "
            f"dense={r['dense_score']:.4f} bm25={r['bm25_score']:.4f} "
            f"— {r['metadata'].get('title', '')[:60]}"
        )
