# ==========================================================
# search_hr_documents.py
#
# HR Information Retrieval Search Engine
#
# Implements:
#   1. Boolean Retrieval
#   2. TF-IDF
#   3. Vector Space Model
#   4. Cosine Similarity
#
# Uses the inverted index created by:
#   build_inverted_index.py
# ==========================================================

from pathlib import Path
import json
import math
import re
from collections import defaultdict, Counter


# ==========================================================
# PATHS
# ==========================================================

PROJECT_DIR = Path(__file__).resolve().parent

IR_ARTIFACT_DIR = PROJECT_DIR / "ir_artifacts"

INDEX_PATH = (
    IR_ARTIFACT_DIR / "inverted_index.json"
)

DF_PATH = (
    IR_ARTIFACT_DIR / "document_frequency.json"
)

DOCUMENT_TF_PATH = (
    IR_ARTIFACT_DIR / "document_term_frequencies.json"
)

PROCESSED_DOCS_PATH = (
    IR_ARTIFACT_DIR / "processed_documents.json"
)


# ==========================================================
# STOPWORDS
# ==========================================================

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
    "our", "you", "your", "i", "me",
    "my"
}


# ==========================================================
# TEXT PREPROCESSING
# ==========================================================

def simple_stem(word):
    """
    Apply the same simple stemming approach
    used when creating the inverted index.
    """

    suffixes = [
        "ingly",
        "edly",
        "ments",
        "ment",
        "ness",
        "ing",
        "ers",
        "ies",
        "ed",
        "er",
        "es",
        "s"
    ]

    for suffix in suffixes:

        if (
            word.endswith(suffix)
            and len(word) > len(suffix) + 2
        ):

            word = word[
                :-len(suffix)
            ]

            break

    return word


def preprocess_query(query):
    """
    Convert a user query into normalized terms.
    """

    query = query.lower()

    query = re.sub(
        r"[^a-z0-9\s]",
        " ",
        query
    )

    tokens = query.split()

    processed = []

    for token in tokens:

        if token in STOPWORDS:
            continue

        if len(token) < 2:
            continue

        token = simple_stem(token)

        if token:
            processed.append(token)

    return processed


# ==========================================================
# LOAD ARTIFACTS
# ==========================================================

def load_json(file_path):
    """
    Load JSON artifact.
    """

    if not file_path.exists():

        raise FileNotFoundError(
            f"Required IR artifact not found:\n"
            f"{file_path}\n\n"
            "Run build_inverted_index.py first."
        )

    with open(
        file_path,
        "r",
        encoding="utf-8"
    ) as file:

        return json.load(file)


print("=" * 70)
print("HR INFORMATION RETRIEVAL SEARCH ENGINE")
print("=" * 70)

print("\nLoading IR index...")

INVERTED_INDEX = load_json(
    INDEX_PATH
)

DOCUMENT_FREQUENCY = load_json(
    DF_PATH
)

DOCUMENT_TERM_FREQUENCIES = load_json(
    DOCUMENT_TF_PATH
)

PROCESSED_DOCUMENTS = load_json(
    PROCESSED_DOCS_PATH
)

DOCUMENTS = sorted(
    DOCUMENT_TERM_FREQUENCIES.keys()
)

TOTAL_DOCUMENTS = len(
    DOCUMENTS
)

print(
    f"Loaded {TOTAL_DOCUMENTS} documents."
)

print(
    f"Loaded {len(INVERTED_INDEX)} unique terms."
)


# ==========================================================
# BOOLEAN RETRIEVAL
# ==========================================================

def get_documents_for_term(term):
    """
    Return documents containing a term.
    """

    term = simple_stem(
        term.lower()
    )

    postings = INVERTED_INDEX.get(
        term,
        {}
    )

    return set(
        postings.keys()
    )


def boolean_and(term1, term2):
    """
    Return documents containing BOTH terms.
    """

    docs1 = get_documents_for_term(
        term1
    )

    docs2 = get_documents_for_term(
        term2
    )

    return docs1.intersection(
        docs2
    )


def boolean_or(term1, term2):
    """
    Return documents containing EITHER term.
    """

    docs1 = get_documents_for_term(
        term1
    )

    docs2 = get_documents_for_term(
        term2
    )

    return docs1.union(
        docs2
    )


def boolean_not(term):
    """
    Return documents NOT containing a term.
    """

    matching_docs = get_documents_for_term(
        term
    )

    return set(DOCUMENTS).difference(
        matching_docs
    )


# ==========================================================
# BOOLEAN QUERY PARSER
# ==========================================================

def boolean_search(query):
    """
    Basic Boolean query support.

    Examples:

        overtime AND policy
        overtime OR compensation
        NOT leave
    """

    query = query.strip()

    # ------------------------------------------------------
    # AND
    # ------------------------------------------------------

    if re.search(
        r"\s+AND\s+",
        query,
        flags=re.IGNORECASE
    ):

        parts = re.split(
            r"\s+AND\s+",
            query,
            flags=re.IGNORECASE
        )

        if len(parts) >= 2:

            result = None

            for part in parts:

                terms = preprocess_query(
                    part
                )

                if not terms:
                    continue

                current_docs = (
                    get_documents_for_term(
                        terms[0]
                    )
                )

                if result is None:

                    result = current_docs

                else:

                    result = result.intersection(
                        current_docs
                    )

            return result or set()

    # ------------------------------------------------------
    # OR
    # ------------------------------------------------------

    if re.search(
        r"\s+OR\s+",
        query,
        flags=re.IGNORECASE
    ):

        parts = re.split(
            r"\s+OR\s+",
            query,
            flags=re.IGNORECASE
        )

        result = set()

        for part in parts:

            terms = preprocess_query(
                part
            )

            for term in terms:

                result.update(
                    get_documents_for_term(
                        term
                    )
                )

        return result

    # ------------------------------------------------------
    # NOT
    # ------------------------------------------------------

    if query.upper().startswith("NOT "):

        remaining = query[4:]

        terms = preprocess_query(
            remaining
        )

        result = set(DOCUMENTS)

        for term in terms:

            result = result.intersection(
                boolean_not(term)
            )

        return result

    # ------------------------------------------------------
    # SINGLE TERM / NORMAL QUERY
    # ------------------------------------------------------

    terms = preprocess_query(
        query
    )

    if not terms:
        return set()

    result = set()

    for term in terms:

        result.update(
            get_documents_for_term(
                term
            )
        )

    return result


# ==========================================================
# TF-IDF
# ==========================================================

def calculate_idf(term):
    """
    Calculate inverse document frequency.

    IDF(t) = log(N / DF(t))

    A smoothed version is used to avoid
    division by zero.
    """

    df = int(
        DOCUMENT_FREQUENCY.get(
            term,
            0
        )
    )

    if df == 0:
        return 0.0

    return math.log(
        (TOTAL_DOCUMENTS + 1)
        /
        (df + 1)
    ) + 1


def calculate_tf(term_frequency):
    """
    Calculate logarithmic term frequency.

    TF = 1 + log(tf)
    """

    if term_frequency <= 0:
        return 0.0

    return 1 + math.log(
        term_frequency
    )


def tfidf_weight(
    term,
    term_frequency
):
    """
    TF-IDF weight.
    """

    tf = calculate_tf(
        term_frequency
    )

    idf = calculate_idf(
        term
    )

    return tf * idf


# ==========================================================
# VECTOR BUILDING
# ==========================================================

def create_query_vector(query):
    """
    Create TF-IDF vector for query.
    """

    terms = preprocess_query(
        query
    )

    term_counts = Counter(
        terms
    )

    vector = {}

    for term, frequency in term_counts.items():

        vector[term] = tfidf_weight(
            term,
            frequency
        )

    return vector


def create_document_vector(
    document_id,
    vocabulary
):
    """
    Create TF-IDF vector for a document.
    """

    term_frequencies = (
        DOCUMENT_TERM_FREQUENCIES.get(
            document_id,
            {}
        )
    )

    vector = {}

    for term in vocabulary:

        frequency = term_frequencies.get(
            term,
            0
        )

        if frequency > 0:

            vector[term] = tfidf_weight(
                term,
                frequency
            )

        else:

            vector[term] = 0.0

    return vector


# ==========================================================
# COSINE SIMILARITY
# ==========================================================

def cosine_similarity(
    vector_a,
    vector_b
):
    """
    Calculate cosine similarity between
    two sparse vectors represented as dictionaries.
    """

    vocabulary = set(
        vector_a.keys()
    ).union(
        vector_b.keys()
    )

    if not vocabulary:
        return 0.0

    dot_product = 0.0

    magnitude_a = 0.0
    magnitude_b = 0.0

    for term in vocabulary:

        value_a = vector_a.get(
            term,
            0.0
        )

        value_b = vector_b.get(
            term,
            0.0
        )

        dot_product += (
            value_a * value_b
        )

        magnitude_a += (
            value_a * value_a
        )

        magnitude_b += (
            value_b * value_b
        )

    magnitude_a = math.sqrt(
        magnitude_a
    )

    magnitude_b = math.sqrt(
        magnitude_b
    )

    if (
        magnitude_a == 0
        or magnitude_b == 0
    ):

        return 0.0

    return (
        dot_product
        /
        (
            magnitude_a
            *
            magnitude_b
        )
    )


# ==========================================================
# TF-IDF RANKED SEARCH
# ==========================================================

def tfidf_search(
    query,
    candidate_documents=None
):
    """
    Rank documents using:
        TF-IDF + Cosine Similarity
    """

    query_vector = create_query_vector(
        query
    )

    if not query_vector:

        return []

    vocabulary = set(
        query_vector.keys()
    )

    # If Boolean filtering has already been
    # applied, rank only those candidates.
    if candidate_documents is None:

        candidate_documents = DOCUMENTS

    results = []

    for document_id in candidate_documents:

        document_vector = (
            create_document_vector(
                document_id,
                vocabulary
            )
        )

        score = cosine_similarity(
            query_vector,
            document_vector
        )

        if score > 0:

            results.append(
                {
                    "document": document_id,
                    "score": score,
                }
            )

    results.sort(
        key=lambda item: item["score"],
        reverse=True
    )

    return results


# ==========================================================
# DISPLAY SEARCH RESULTS
# ==========================================================

def display_results(
    results,
    limit=10
):
    """
    Display ranked search results.
    """

    if not results:

        print(
            "\nNo matching documents found."
        )

        return

    print("\n" + "=" * 70)
    print("SEARCH RESULTS")
    print("=" * 70)

    for rank, result in enumerate(
        results[:limit],
        start=1
    ):

        document = result[
            "document"
        ]

        score = result[
            "score"
        ]

        print(
            f"\n{rank}. {document}"
        )

        print(
            f"   Relevance: "
            f"{score:.4f}"
        )


# ==========================================================
# COMBINED SEARCH
# ==========================================================

def search(
    query,
    mode="tfidf"
):
    """
    Main search function.

    Modes:
        boolean
        tfidf
    """

    if mode == "boolean":

        documents = boolean_search(
            query
        )

        return [
            {
                "document": document,
                "score": 1.0
            }
            for document
            in sorted(documents)
        ]

    if mode == "tfidf":

        return tfidf_search(
            query
        )

    raise ValueError(
        "Unsupported search mode. "
        "Use 'boolean' or 'tfidf'."
    )


# ==========================================================
# INTERACTIVE SEARCH
# ==========================================================

def interactive_search():

    print("\n" + "=" * 70)
    print("INTERACTIVE HR SEARCH")
    print("=" * 70)

    print(
        "\nExamples:"
    )

    print(
        "  overtime"
    )

    print(
        "  overtime AND compensation"
    )

    print(
        "  training OR development"
    )

    print(
        "  NOT leave"
    )

    print(
        "\nType 'exit' to stop."
    )

    while True:

        print("\n" + "-" * 70)

        query = input(
            "Enter query: "
        ).strip()

        if query.lower() == "exit":

            break

        if not query:

            print(
                "Please enter a query."
            )

            continue

        # --------------------------------------------------
        # Boolean query
        # --------------------------------------------------

        if re.search(
            r"\bAND\b|\bOR\b|\bNOT\b",
            query,
            flags=re.IGNORECASE
        ):

            results = search(
                query,
                mode="boolean"
            )

            print(
                "\nBoolean retrieval results:"
            )

            display_results(
                results
            )

        # --------------------------------------------------
        # Ranked search
        # --------------------------------------------------

        else:

            results = search(
                query,
                mode="tfidf"
            )

            print(
                "\nTF-IDF ranked results:"
            )

            display_results(
                results
            )


# ==========================================================
# MAIN
# ==========================================================

if __name__ == "__main__":

    print(
        "\nIR search engine ready."
    )

    # ------------------------------------------------------
    # Automatic test queries
    # ------------------------------------------------------

    test_queries = [
        "overtime",
        "training",
        "employee benefits",
        "performance review",
    ]

    for query in test_queries:

        print(
            "\n" + "=" * 70
        )

        print(
            f"TEST QUERY: {query}"
        )

        print(
            "=" * 70
        )

        results = tfidf_search(
            query
        )

        display_results(
            results
        )

    # ------------------------------------------------------
    # Interactive mode
    # ------------------------------------------------------

    interactive_search()