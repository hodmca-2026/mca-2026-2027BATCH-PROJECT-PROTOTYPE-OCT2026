"""
HR INFORMATION RETRIEVAL - INDEX BUILDER

Unit II / Unit V foundation:
- Text preprocessing
- Tokenization
- Stop-word removal
- Simple stemming
- Inverted index construction
- Term frequency
- Document frequency
- Index statistics / metadata

Input:
    extracted_documents/*.txt

Output:
    ir_artifacts/inverted_index.json
    ir_artifacts/document_term_frequencies.json
    ir_artifacts/document_frequency.json
    ir_artifacts/processed_documents.json
    ir_artifacts/index_metadata.json
"""

from pathlib import Path
from collections import Counter, defaultdict
import json
import re
from datetime import datetime, timezone


PROJECT_DIR = Path(__file__).resolve().parent
DOCUMENT_DIR = PROJECT_DIR / "extracted_documents"
IR_ARTIFACT_DIR = PROJECT_DIR / "ir_artifacts"
IR_ARTIFACT_DIR.mkdir(exist_ok=True)

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
    "our", "you", "your", "i", "me", "my",
    "any", "all"
}


# ----------------------------------------------------------
# SIMPLE STEMMER
# ----------------------------------------------------------

def simple_stem(word):
    """Transparent rule-based stemming for an academic IR project."""

    word = str(word).lower().strip()

    suffixes = [
        "ingly", "edly", "ments", "ment", "ness",
        "ing", "ers", "ies", "ed", "er", "es", "s"
    ]

    for suffix in suffixes:
        if word.endswith(suffix) and len(word) > len(suffix) + 2:
            return word[:-len(suffix)]

    return word


# ----------------------------------------------------------
# PREPROCESSING
# ----------------------------------------------------------

def preprocess_text(text):
    """
    Normalize raw text into indexed terms:
    lowercase -> punctuation removal -> tokenization ->
    stopword removal -> short-token removal -> stemming.
    """

    if not text:
        return []

    text = str(text).lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)

    processed_tokens = []

    for token in text.split():
        if token in STOPWORDS:
            continue

        if len(token) < 2:
            continue

        token = simple_stem(token)

        if token:
            processed_tokens.append(token)

    return processed_tokens


# ----------------------------------------------------------
# FILE HELPERS
# ----------------------------------------------------------

def read_document(file_path):
    return file_path.read_text(
        encoding="utf-8",
        errors="replace"
    )


def save_json(data, file_path):
    with open(
        file_path,
        "w",
        encoding="utf-8"
    ) as file:
        json.dump(
            data,
            file,
            indent=4,
            ensure_ascii=False
        )


# ----------------------------------------------------------
# INDEX CONSTRUCTION
# ----------------------------------------------------------

def build_index():
    """Create term -> document -> term-frequency inverted index."""

    documents = sorted(
        DOCUMENT_DIR.glob("*.txt")
    )

    if not documents:
        raise FileNotFoundError(
            f"No extracted TXT documents found in {DOCUMENT_DIR}"
        )

    inverted_index = defaultdict(dict)
    document_term_frequencies = {}
    processed_documents = {}
    document_statistics = {}

    for document in documents:
        text = read_document(document)
        tokens = preprocess_text(text)
        term_counts = Counter(tokens)
        document_id = document.stem

        document_term_frequencies[document_id] = dict(term_counts)
        processed_documents[document_id] = tokens

        for term, frequency in term_counts.items():
            inverted_index[term][document_id] = frequency

        document_statistics[document_id] = {
            "original_word_count": len(text.split()),
            "processed_token_count": len(tokens),
            "unique_term_count": len(term_counts)
        }

    return (
        dict(inverted_index),
        document_term_frequencies,
        processed_documents,
        document_statistics
    )


# ----------------------------------------------------------
# DOCUMENT FREQUENCY
# ----------------------------------------------------------

def calculate_document_frequency(inverted_index):
    """DF(term) = number of documents containing the term."""

    return {
        term: len(postings)
        for term, postings in inverted_index.items()
    }


# ----------------------------------------------------------
# TERM SEARCH
# ----------------------------------------------------------

def search_term(inverted_index, term):
    """Return postings for one normalized term."""

    term = simple_stem(str(term).lower())
    return inverted_index.get(term, {})


# ----------------------------------------------------------
# INDEX METADATA
# ----------------------------------------------------------

def build_metadata(
    document_term_frequencies,
    inverted_index,
    document_statistics
):
    document_count = len(
        document_term_frequencies
    )

    unique_terms = len(inverted_index)

    total_postings = sum(
        len(postings)
        for postings in inverted_index.values()
    )

    document_lengths = {
        document_id: sum(term_counts.values())
        for document_id, term_counts
        in document_term_frequencies.items()
    }

    total_tokens = sum(
        document_lengths.values()
    )

    average_document_length = (
        total_tokens / document_count
        if document_count
        else 0.0
    )

    return {
        "document_count": document_count,
        "unique_terms": unique_terms,
        "total_indexed_postings": total_postings,
        "total_processed_tokens": total_tokens,
        "average_document_length": round(
            average_document_length,
            4
        ),
        "preprocessing": [
            "lowercase",
            "punctuation removal",
            "tokenization",
            "stopword removal",
            "short-token removal",
            "rule-based stemming"
        ],
        "document_statistics": document_statistics,
        "generated_at": datetime.now(
            timezone.utc
        ).isoformat()
    }


# ----------------------------------------------------------
# MAIN
# ----------------------------------------------------------

def main():
    print("=" * 70)
    print("HR INFORMATION RETRIEVAL")
    print("TEXT PREPROCESSING + INVERTED INDEX")
    print("=" * 70)

    (
        inverted_index,
        document_term_frequencies,
        processed_documents,
        document_statistics
    ) = build_index()

    document_frequency = calculate_document_frequency(
        inverted_index
    )

    save_json(
        inverted_index,
        IR_ARTIFACT_DIR / "inverted_index.json"
    )

    save_json(
        document_term_frequencies,
        IR_ARTIFACT_DIR / "document_term_frequencies.json"
    )

    save_json(
        document_frequency,
        IR_ARTIFACT_DIR / "document_frequency.json"
    )

    save_json(
        processed_documents,
        IR_ARTIFACT_DIR / "processed_documents.json"
    )

    metadata = build_metadata(
        document_term_frequencies,
        inverted_index,
        document_statistics
    )

    save_json(
        metadata,
        IR_ARTIFACT_DIR / "index_metadata.json"
    )

    print("\n" + "=" * 70)
    print("INDEX STATISTICS")
    print("=" * 70)
    print(
        f"Number of documents     : {metadata['document_count']}"
    )
    print(
        f"Number of unique terms  : {metadata['unique_terms']}"
    )
    print(
        "Total indexed postings  : "
        f"{metadata['total_indexed_postings']}"
    )
    print(
        "Total processed tokens  : "
        f"{metadata['total_processed_tokens']}"
    )
    print(
        "Average document length : "
        f"{metadata['average_document_length']}"
    )

    print("\nSample term lookups:")

    for term in [
        "employee",
        "overtime",
        "training",
        "promotion",
        "benefits",
        "performance"
    ]:
        print(
            f"  {term:<15} -> "
            f"{search_term(inverted_index, term)}"
        )

    print("\nGenerated files:")
    print("  ir_artifacts/inverted_index.json")
    print("  ir_artifacts/document_term_frequencies.json")
    print("  ir_artifacts/document_frequency.json")
    print("  ir_artifacts/processed_documents.json")
    print("  ir_artifacts/index_metadata.json")

    print("\n" + "=" * 70)
    print("INVERTED INDEX BUILD COMPLETED")
    print("=" * 70)


if __name__ == "__main__":
    main()
