"""Tests for the retrieval pipeline."""

import json
import os
import pytest


# Skip if models not built yet
def _reports_exist():
    path = os.path.join(os.path.dirname(__file__), "..", "data", "reports", "reports.json")
    return os.path.exists(path)


@pytest.mark.skipif(not _reports_exist(), reason="Reports not generated yet")
def test_bm25_search_returns_results():
    """BM25 search should return non-empty results for a known query."""
    from retrieval.bm25_search import bm25_search, build_bm25
    
    reports_path = os.path.join(os.path.dirname(__file__), "..", "data", "reports", "reports.json")
    with open(reports_path, "r", encoding="utf-8") as f:
        reports = json.load(f)
    
    build_bm25(reports)
    results = bm25_search("overheating motor", k=5)
    
    assert len(results) > 0
    assert all("id" in r for r in results)
    assert all("score" in r for r in results)


@pytest.mark.skipif(not _reports_exist(), reason="Reports not generated yet")
def test_hybrid_search_returns_results():
    """Hybrid search should return non-empty results."""
    from retrieval.hybrid_search import hybrid_search
    from retrieval.embed_store import build_index
    from retrieval.bm25_search import build_bm25
    
    reports_path = os.path.join(os.path.dirname(__file__), "..", "data", "reports", "reports.json")
    with open(reports_path, "r", encoding="utf-8") as f:
        reports = json.load(f)
    
    # Ensure indices are built
    build_index(reports)
    build_bm25(reports)
    
    results = hybrid_search("overheating motor incidents", k=5)
    
    assert len(results) > 0
    assert all("id" in r for r in results)
    assert all("hybrid_score" in r for r in results)


@pytest.mark.skipif(not _reports_exist(), reason="Reports not generated yet")
def test_reranker_improves_results():
    """Reranker should reorder candidates by cross-encoder score."""
    from retrieval.hybrid_search import hybrid_search
    from retrieval.reranker import rerank
    
    candidates = hybrid_search("overheating motor incidents", k=10)
    
    if len(candidates) < 2:
        pytest.skip("Not enough candidates for reranking test")
    
    reranked = rerank("overheating motor incidents", candidates, top_n=5)
    
    assert len(reranked) > 0
    assert len(reranked) <= 5
    assert all("rerank_score" in r for r in reranked)
    
    # Scores should be sorted descending
    scores = [r["rerank_score"] for r in reranked]
    assert scores == sorted(scores, reverse=True)
