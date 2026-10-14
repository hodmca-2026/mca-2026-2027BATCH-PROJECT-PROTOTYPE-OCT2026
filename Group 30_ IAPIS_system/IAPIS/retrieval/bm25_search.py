"""
BM25 Sparse Retrieval

Implements BM25Okapi-based keyword retrieval over the report corpus.
Persists the tokenized index with pickle for fast reloads.

Course mapping: IR Unit IV — ranking with language models, BM25 represents the
classical probabilistic/statistical language model approach.
"""

import json
import os
import pickle
import re
import logging
from typing import List, Dict

from rank_bm25 import BM25Okapi

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
BM25_PERSIST_PATH = os.path.join(
    os.path.dirname(__file__), "..", "models_store", "bm25.pkl"
)

# Simple stop words for tokenization
STOP_WORDS = {
    "the", "a", "an", "is", "was", "were", "are", "been", "be", "have", "has",
    "had", "do", "does", "did", "will", "would", "could", "should", "may",
    "might", "shall", "can", "need", "must", "and", "or", "but", "if", "then",
    "else", "when", "while", "of", "at", "by", "for", "with", "about", "to",
    "from", "in", "on", "into", "it", "its", "this", "that", "these", "those",
    "i", "me", "my", "we", "our", "you", "your", "he", "him", "his", "she",
    "her", "they", "them", "their", "not", "no", "nor", "so", "as", "up",
    "out", "just", "than", "too", "very", "also",
}

# Module-level cache
_bm25 = None
_corpus_docs = None
_report_map = None


def _tokenize(text: str) -> List[str]:
    """Simple tokenizer: lowercase, split on non-alphanumeric, remove stop words."""
    tokens = re.findall(r'[a-z0-9]+', text.lower())
    return [t for t in tokens if t not in STOP_WORDS and len(t) > 1]


def build_bm25(reports: List[dict], persist_path: str = None) -> BM25Okapi:
    """
    Build a BM25 index from the reports corpus and persist it.
    
    Args:
        reports: List of report dicts with 'id', 'title', 'text'.
        persist_path: Path to save the pickled index.
    
    Returns:
        BM25Okapi instance.
    """
    global _bm25, _corpus_docs, _report_map
    
    if persist_path is None:
        persist_path = BM25_PERSIST_PATH
    
    # Tokenize each report's title + text
    corpus_tokens = []
    doc_list = []
    report_map = {}
    
    for report in reports:
        combined = f"{report.get('title', '')} {report.get('text', '')}"
        tokens = _tokenize(combined)
        corpus_tokens.append(tokens)
        doc_list.append(combined)
        report_map[len(corpus_tokens) - 1] = report
    
    # Build BM25
    bm25 = BM25Okapi(corpus_tokens)
    
    # Persist
    os.makedirs(os.path.dirname(persist_path), exist_ok=True)
    with open(persist_path, "wb") as f:
        pickle.dump({
            "bm25": bm25,
            "corpus_docs": doc_list,
            "report_map": report_map,
        }, f)
    
    _bm25 = bm25
    _corpus_docs = doc_list
    _report_map = report_map
    
    logger.info(f"Built BM25 index over {len(corpus_tokens)} documents -> {persist_path}")
    return bm25


def _load_bm25(persist_path: str = None):
    """Load the persisted BM25 index."""
    global _bm25, _corpus_docs, _report_map
    
    if _bm25 is not None:
        return _bm25, _corpus_docs, _report_map
    
    if persist_path is None:
        persist_path = BM25_PERSIST_PATH
    
    if not os.path.exists(persist_path):
        raise FileNotFoundError(
            f"BM25 index not found at {persist_path}. Run build_bm25() first."
        )
    
    with open(persist_path, "rb") as f:
        data = pickle.load(f)
    
    _bm25 = data["bm25"]
    _corpus_docs = data["corpus_docs"]
    _report_map = data["report_map"]
    
    logger.info(f"Loaded BM25 index ({len(_corpus_docs)} documents)")
    return _bm25, _corpus_docs, _report_map


def bm25_search(query: str, k: int = 10, persist_path: str = None) -> List[Dict]:
    """
    Search the BM25 index.
    
    Args:
        query: Natural language query string.
        k: Number of results to return.
    
    Returns:
        List of dicts: [{id, score, document, metadata}, ...] sorted by BM25 score (descending).
    """
    bm25, corpus_docs, report_map = _load_bm25(persist_path)
    
    query_tokens = _tokenize(query)
    if not query_tokens:
        return []
    
    scores = bm25.get_scores(query_tokens)
    
    # Get top-k indices
    top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:k]
    
    results = []
    for idx in top_indices:
        if scores[idx] <= 0:
            continue
        
        report = report_map.get(idx, {})
        results.append({
            "id": report.get("id", f"DOC-{idx}"),
            "score": round(float(scores[idx]), 4),
            "document": corpus_docs[idx],
            "metadata": {
                "title": report.get("title", ""),
                "type": report.get("type", ""),
                "equipment": report.get("equipment", ""),
                "hazard_type": report.get("hazard_type", ""),
                "location": report.get("location", ""),
                "date": report.get("date", ""),
                "severity": report.get("severity", ""),
                "source": report.get("source", ""),
            },
        })
    
    return results


if __name__ == "__main__":
    reports_path = os.path.join(os.path.dirname(__file__), "..", "data", "reports", "reports.json")
    
    if not os.path.exists(reports_path):
        print(f"Reports file not found: {reports_path}")
        print("Run scripts/generate_synthetic_reports.py first.")
    else:
        with open(reports_path, "r", encoding="utf-8") as f:
            reports = json.load(f)
        
        build_bm25(reports)
        
        # Quick test
        results = bm25_search("overheating motor", k=3)
        print(f"\nTest query: 'overheating motor' -> {len(results)} results")
        for r in results:
            print(f"  {r['id']}: score={r['score']:.4f} — {r['metadata'].get('title', '')[:80]}")
