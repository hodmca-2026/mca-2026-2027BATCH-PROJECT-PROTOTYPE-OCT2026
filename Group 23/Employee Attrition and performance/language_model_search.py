"""
Unit IV - Language Model Based Information Retrieval

Unigram / Multinomial Language Model
with Jelinek-Mercer smoothing.

Ranks HR documents using query likelihood:
    P(Query | Document)

The returned score is a LOG query-likelihood score.
Negative values are expected because log(p) < 0 for 0 < p < 1.
"""

from pathlib import Path
from collections import Counter
import json
import math
import re


PROJECT_DIR = Path(__file__).resolve().parent
IR_DIR = PROJECT_DIR / "ir_artifacts"
TF_PATH = IR_DIR / "document_term_frequencies.json"

LAMBDA = 0.8

STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by",
    "for", "from", "has", "have", "in", "is", "it",
    "of", "on", "or", "that", "the", "this", "to",
    "was", "were", "with", "will", "you", "your"
}


def stem(word):
    """Simple stemmer matching the project's indexed vocabulary."""

    for suffix in [
        "ingly", "edly", "ments", "ment", "ness",
        "ing", "ers", "ies", "ed", "er", "es", "s"
    ]:
        if len(word) > len(suffix) + 2 and word.endswith(suffix):
            return word[:-len(suffix)]

    return word


def preprocess(text):
    """Convert text into the normalized indexed terms."""

    if not text:
        return []

    text = str(text).lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)

    terms = []
    for word in text.split():
        if word in STOPWORDS or len(word) < 2:
            continue
        terms.append(stem(word))

    return [term for term in terms if term]


def load_data():
    if not TF_PATH.exists():
        raise FileNotFoundError(
            "document_term_frequencies.json not found.\n"
            "Run: python build_inverted_index.py"
        )

    with open(TF_PATH, "r", encoding="utf-8") as file:
        return json.load(file)


def build_model():
    data = load_data()

    documents = {}
    collection_frequency = Counter()
    collection_length = 0

    for document_id, terms in data.items():
        terms = {
            str(term): int(freq)
            for term, freq in terms.items()
        }

        document_length = sum(terms.values())

        documents[document_id] = {
            "terms": terms,
            "length": document_length
        }

        collection_frequency.update(terms)
        collection_length += document_length

    return documents, collection_frequency, collection_length


def smoothed_probability(term, document, collection_frequency, collection_length):
    """Jelinek-Mercer smoothed P(term | document)."""

    document_length = document["length"]

    if document_length <= 0 or collection_length <= 0:
        return 0.0

    tf = document["terms"].get(term, 0)
    document_probability = tf / document_length
    collection_probability = (
        collection_frequency.get(term, 0) / collection_length
    )

    return (
        LAMBDA * document_probability
        + (1 - LAMBDA) * collection_probability
    )


def language_model_score(query_terms, document, collection_frequency, collection_length):
    """Calculate log P(Query | Document) for a unigram language model."""

    score = 0.0

    for term in query_terms:
        probability = smoothed_probability(
            term,
            document,
            collection_frequency,
            collection_length
        )

        if probability > 0:
            score += math.log(probability)

    return score


def search(query, top_k=5):
    """Rank HR documents with query-likelihood Language Model retrieval."""

    if not query or not str(query).strip():
        return []

    documents, collection_frequency, collection_length = build_model()

    query_terms = preprocess(query)

    # Unknown query terms contribute no useful retrieval signal.
    query_terms = list(dict.fromkeys(
        term for term in query_terms
        if term in collection_frequency
    ))

    if not query_terms:
        return []

    results = []

    for document_id, document in documents.items():
        score = language_model_score(
            query_terms,
            document,
            collection_frequency,
            collection_length
        )

        matched_terms = [
            term
            for term in query_terms
            if document["terms"].get(term, 0) > 0
        ]

        results.append({
            "document_id": document_id,
            "document": document_id,
            "score": round(score, 6),
            "log_likelihood": round(score, 6),
            "score_type": "Log Query Likelihood",
            "higher_is_better": True,
            "query_terms": query_terms,
            "matched_terms": matched_terms
        })

    # Pure language-model ranking: score first.
    # Matched-term count is only a tie-breaker.
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
    print("HR LANGUAGE MODEL SEARCH")
    print("=" * 70)

    documents, _, collection_length = build_model()

    print(f"Documents loaded : {len(documents)}")
    print(f"Collection length: {collection_length}")
    print(f"Lambda           : {LAMBDA}")
    print("Score type       : Log Query Likelihood")
    print("Note             : Negative log scores are expected.")

    test_queries = [
        "promotion",
        "training",
        "overtime",
        "performance review",
        "employee benefits"
    ]

    for query in test_queries:
        print("\n" + "-" * 70)
        print(f"Query: {query}")
        print("-" * 70)

        results = search(query)

        if not results:
            print("No matching documents.")
            continue

        for rank, result in enumerate(results, start=1):
            print(
                f"{rank}. {result['document']} | "
                f"Log Likelihood: {result['score']} | "
                f"Matched: {', '.join(result['matched_terms'])}"
            )

    print("\nInteractive Search")
    print("Type 'exit' to stop.\n")

    while True:
        query = input("Enter search query: ").strip()

        if query.lower() == "exit":
            break

        results = search(query)

        if not results:
            print("No matching documents.\n")
            continue

        for rank, result in enumerate(results, start=1):
            print(
                f"{rank}. {result['document']} | "
                f"Log Likelihood: {result['score']} | "
                f"Matched: {', '.join(result['matched_terms'])}"
            )

        print()
