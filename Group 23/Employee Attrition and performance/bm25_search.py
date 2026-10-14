"""
BM25 ranked retrieval for the HR Information Retrieval system.

Uses the project's inverted index, document frequency and term-frequency
artifacts. BM25 is a probabilistic ranking model that considers term
frequency, inverse document frequency and document-length normalization.
"""

from pathlib import Path
import json
import math
import re


PROJECT_DIR = Path(__file__).resolve().parent
IR_ARTIFACT_DIR = PROJECT_DIR / "ir_artifacts"

INVERTED_INDEX_PATH = IR_ARTIFACT_DIR / "inverted_index.json"
DOCUMENT_FREQUENCY_PATH = IR_ARTIFACT_DIR / "document_frequency.json"
DOCUMENT_TF_PATH = IR_ARTIFACT_DIR / "document_term_frequencies.json"

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

K1 = 1.5
B = 0.75


def simple_stem(word):
    """Apply the project's transparent rule-based stemming logic."""

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


def load_artifacts():
    inverted_index = load_json(INVERTED_INDEX_PATH)
    document_frequency = load_json(DOCUMENT_FREQUENCY_PATH)
    document_term_frequencies = load_json(DOCUMENT_TF_PATH)

    documents = sorted(document_term_frequencies.keys())

    document_lengths = {
        document_id: sum(term_frequencies.values())
        for document_id, term_frequencies
        in document_term_frequencies.items()
    }

    total_documents = len(documents)
    average_document_length = (
        sum(document_lengths.values()) / total_documents
        if total_documents else 0.0
    )

    return (
        inverted_index,
        document_frequency,
        document_term_frequencies,
        document_lengths,
        total_documents,
        average_document_length
    )


(
    INVERTED_INDEX,
    DOCUMENT_FREQUENCY,
    DOCUMENT_TERM_FREQUENCIES,
    DOCUMENT_LENGTHS,
    TOTAL_DOCUMENTS,
    AVG_DOCUMENT_LENGTH
) = load_artifacts()


def calculate_bm25_idf(term):
    """BM25 inverse document frequency."""

    df = DOCUMENT_FREQUENCY.get(term, 0)

    if df <= 0 or TOTAL_DOCUMENTS <= 0:
        return 0.0

    return math.log(
        1
        + (
            TOTAL_DOCUMENTS
            - df
            + 0.5
        )
        / (
            df
            + 0.5
        )
    )


def bm25_term_score(term, document_id):
    """Calculate the BM25 contribution of one term for one document."""

    document_terms = DOCUMENT_TERM_FREQUENCIES.get(
        document_id,
        {}
    )

    tf = int(document_terms.get(term, 0))

    if tf <= 0 or AVG_DOCUMENT_LENGTH <= 0:
        return 0.0

    idf = calculate_bm25_idf(term)
    document_length = DOCUMENT_LENGTHS.get(document_id, 0)

    normalization = (
        1
        - B
        + B * (
            document_length / AVG_DOCUMENT_LENGTH
        )
    )

    denominator = (
        tf
        + K1 * normalization
    )

    if denominator <= 0:
        return 0.0

    return idf * (
        (tf * (K1 + 1)) / denominator
    )


def bm25_search(query, top_k=5):
    """Rank HR documents using BM25."""

    try:
        top_k = int(top_k)
    except (TypeError, ValueError):
        top_k = 5

    top_k = max(1, min(top_k, 50))

    query_terms = list(dict.fromkeys(
        preprocess_query(query)
    ))

    if not query_terms:
        return []

    candidate_documents = set()

    for term in query_terms:
        candidate_documents.update(
            INVERTED_INDEX.get(term, {}).keys()
        )

    if not candidate_documents:
        return []

    scored = []

    for document_id in candidate_documents:
        score = 0.0
        matched_terms = []
        term_scores = {}

        for term in query_terms:
            contribution = bm25_term_score(
                term,
                document_id
            )

            if contribution > 0:
                matched_terms.append(term)
                term_scores[term] = round(
                    contribution,
                    6
                )

            score += contribution

        if score <= 0:
            continue

        scored.append({
            "document_id": document_id,
            "document": document_id,
            "score": round(score, 6),
            "score_type": "BM25 Relevance Score",
            "higher_is_better": True,
            "query_terms": query_terms,
            "matched_terms": matched_terms,
            "term_scores": term_scores,
            "document_length": DOCUMENT_LENGTHS.get(
                document_id,
                0
            )
        })

    scored.sort(
        key=lambda item: (
            item["score"],
            len(item["matched_terms"])
        ),
        reverse=True
    )

    return scored[:top_k]


if __name__ == "__main__":
    print("=" * 70)
    print("HR INFORMATION RETRIEVAL - BM25")
    print("=" * 70)
    print(f"Documents          : {TOTAL_DOCUMENTS}")
    print(f"Unique terms       : {len(INVERTED_INDEX)}")
    print(f"k1                 : {K1}")
    print(f"b                  : {B}")
    print(f"Average doc length : {AVG_DOCUMENT_LENGTH:.2f}")

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
        print("\n" + "-" * 70)
        print(f"QUERY: {query}")
        print("-" * 70)

        results = bm25_search(query, top_k=5)

        if not results:
            print("No matching documents found.")
            continue

        for rank, result in enumerate(results, start=1):
            print(
                f"{rank}. {result['document']} | "
                f"BM25: {result['score']:.4f} | "
                f"Matched: {', '.join(result['matched_terms'])}"
            )
