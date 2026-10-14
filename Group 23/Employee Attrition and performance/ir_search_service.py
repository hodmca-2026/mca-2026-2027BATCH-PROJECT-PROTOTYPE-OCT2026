"""
TF-IDF ranked retrieval service for the HR Information Retrieval system.

The implementation uses the project's inverted index and document-term
frequency artifacts. Scores are term-weighted TF-IDF retrieval scores and
are only intended to be compared within the TF-IDF model.
"""

from pathlib import Path
from collections import Counter
import json
import math
import re


PROJECT_DIR = Path(__file__).resolve().parent
IR_DIR = PROJECT_DIR / "ir_artifacts"

INDEX_PATH = IR_DIR / "inverted_index.json"
TF_PATH = IR_DIR / "document_term_frequencies.json"

STOPWORDS = {
    "a", "an", "the", "and", "or", "but",
    "if", "then", "than", "for", "from",
    "to", "of", "in", "on", "at", "by",
    "with", "about", "as", "into", "through",
    "during", "before", "after", "above",
    "below", "between", "is", "are", "was",
    "were", "be", "been", "being", "has",
    "have", "had", "do", "does", "did",
    "will", "would", "should", "could",
    "may", "might", "must", "can",
    "this", "that", "these", "those",
    "it", "its", "they", "their", "them",
    "he", "she", "his", "her", "we",
    "our", "you", "your", "i", "me", "my"
}


def simple_stem(word):
    """Apply the same transparent stemming logic used by the index."""

    word = str(word).lower().strip()

    suffixes = [
        "ingly", "edly", "ments", "ment", "ness",
        "ing", "ers", "ies", "ed", "er", "es", "s"
    ]

    for suffix in suffixes:
        if word.endswith(suffix) and len(word) > len(suffix) + 2:
            return word[:-len(suffix)]

    return word


def preprocess_query(query):
    """Convert a user query into the normalized indexed terms."""

    if query is None:
        return []

    query = re.sub(r"[^a-z0-9\s]", " ", str(query).lower())

    terms = []
    for token in query.split():
        if token in STOPWORDS or len(token) < 2:
            continue

        token = simple_stem(token)
        if token:
            terms.append(token)

    return terms


def load_json(path):
    if not path.exists():
        raise FileNotFoundError(
            f"Missing IR artifact: {path}\n"
            "Run build_inverted_index.py first."
        )

    with open(path, "r", encoding="utf-8") as file:
        return json.load(file)


def _load_artifacts():
    index = load_json(INDEX_PATH)
    term_frequencies = load_json(TF_PATH)
    return index, term_frequencies


def tfidf_search(query, top_k=5):
    """Rank HR documents using term-weighted TF-IDF retrieval."""

    index, term_frequencies = _load_artifacts()

    query_terms = preprocess_query(query)

    if not query_terms:
        return []

    documents = list(term_frequencies.keys())
    total_docs = len(documents)

    if total_docs == 0:
        return []

    query_count = Counter(query_terms)
    scores = Counter()
    matched_terms_by_document = {}

    for term, query_frequency in query_count.items():
        postings = index.get(term, {})

        if not postings:
            continue

        document_frequency = len(postings)

        idf = math.log(
            total_docs / document_frequency
        ) if document_frequency else 0.0

        for document_id, term_frequency in postings.items():
            tf_weight = 1 + math.log(max(int(term_frequency), 1))

            scores[document_id] += (
                query_frequency
                * tf_weight
                * idf
            )

            matched_terms_by_document.setdefault(
                document_id,
                set()
            ).add(term)

    results = []

    for document_id, score in scores.items():
        matched_terms = sorted(
            matched_terms_by_document.get(
                document_id,
                set()
            )
        )

        results.append({
            "document_id": document_id,
            "document": document_id,
            "score": round(float(score), 6),
            "score_type": "TF-IDF Retrieval Score",
            "higher_is_better": True,
            "query_terms": list(dict.fromkeys(query_terms)),
            "matched_terms": matched_terms
        })

    results.sort(
        key=lambda item: (
            item["score"],
            len(item["matched_terms"])
        ),
        reverse=True
    )

    try:
        top_k = int(top_k)
    except (TypeError, ValueError):
        top_k = 5

    top_k = max(1, min(top_k, 50))

    return results[:top_k]


if __name__ == "__main__":
    print("=" * 70)
    print("HR INFORMATION RETRIEVAL - TF-IDF")
    print("=" * 70)

    test_queries = [
        "overtime",
        "employee benefits",
        "training",
        "performance review",
        "promotion",
        "manager support",
        "work life balance"
    ]

    for query in test_queries:
        print("\n" + "=" * 70)
        print(f"QUERY: {query}")
        print("=" * 70)

        results = tfidf_search(query, top_k=5)

        if not results:
            print("No matching documents found.")
            continue

        for rank, result in enumerate(results, start=1):
            print(
                f"{rank}. {result['document']} | "
                f"TF-IDF Score: {result['score']:.4f} | "
                f"Matched: {', '.join(result['matched_terms'])}"
            )
