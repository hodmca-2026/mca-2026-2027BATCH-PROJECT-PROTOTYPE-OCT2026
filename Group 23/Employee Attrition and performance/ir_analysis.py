"""
IR ANALYSIS MODULE

Unit IV + Unit V + Unit VI support for the HR knowledge system.

Implemented concepts:
- Language-model passage retrieval
- Multi-model ranking comparison
- Precision@K / Recall@K / F1 / MRR evaluation
- Rule-based information extraction from HR policy text
- Retrieval fusion using Reciprocal Rank Fusion (RRF)

This module operates on the project's extracted HR document collection.
"""

from pathlib import Path
from collections import Counter
import math
import re

from bm25_search import bm25_search
from ir_search_service import tfidf_search
from language_model_search import search as language_model_search


PROJECT_DIR = Path(__file__).resolve().parent
DOCUMENT_DIR = PROJECT_DIR / "extracted_documents"

LAMBDA = 0.8
RRF_K = 60

STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by",
    "for", "from", "has", "have", "in", "is", "it",
    "of", "on", "or", "that", "the", "this", "to",
    "was", "were", "with", "will", "you", "your"
}


# ----------------------------------------------------------
# TEXT PREPROCESSING
# ----------------------------------------------------------

def stem(word):
    """Use the same transparent rule-based stemming style as the index."""

    suffixes = [
        "ingly", "edly", "ments", "ment", "ness",
        "ing", "ers", "ies", "ed", "er", "es", "s"
    ]

    for suffix in suffixes:
        if len(word) > len(suffix) + 2 and word.endswith(suffix):
            return word[:-len(suffix)]

    return word


def preprocess(text):
    if not text:
        return []

    text = str(text).lower()
    text = re.sub(r"[^a-z0-9\s]", " ", text)

    terms = []
    for token in text.split():
        if token in STOPWORDS or len(token) < 2:
            continue
        token = stem(token)
        if token:
            terms.append(token)

    return terms


# ----------------------------------------------------------
# DOCUMENT / PASSAGE LOADING
# ----------------------------------------------------------

def load_documents():
    """Load the actual extracted HR documents."""

    if not DOCUMENT_DIR.exists():
        return {}

    documents = {}

    for path in sorted(DOCUMENT_DIR.glob("*.txt")):
        try:
            documents[path.stem] = path.read_text(
                encoding="utf-8",
                errors="replace"
            )
        except OSError:
            continue

    return documents


def split_passages(text, max_words=70):
    """
    Split a policy document into passages.

    Blank-line paragraphs are preferred. Long paragraphs are then split into
    sentence groups / word chunks so passage ranking remains meaningful.
    """

    if not text or not text.strip():
        return []

    paragraphs = [
        p.strip()
        for p in re.split(r"\n\s*\n", text)
        if p.strip()
    ]

    passages = []

    for paragraph in paragraphs:
        words = paragraph.split()

        if len(words) <= max_words:
            passages.append(paragraph)
            continue

        sentences = [
            s.strip()
            for s in re.split(r"(?<=[.!?])\s+", paragraph)
            if s.strip()
        ]

        current = []
        current_count = 0

        for sentence in sentences:
            sentence_words = sentence.split()

            if current and current_count + len(sentence_words) > max_words:
                passages.append(" ".join(current))
                current = []
                current_count = 0

            current.append(sentence)
            current_count += len(sentence_words)

        if current:
            passages.append(" ".join(current))

    if not passages:
        passages = [text.strip()]

    return passages


# ----------------------------------------------------------
# LANGUAGE MODEL PASSAGE RETRIEVAL
# ----------------------------------------------------------

def search_passages(query, top_k=5):
    """
    Rank passages using a Unigram / Multinomial query-likelihood model.

    Jelinek-Mercer smoothing is used exactly as in the document-level
    Language Model, making this a direct Unit IV passage-retrieval extension.
    """

    query_terms = preprocess(query)
    if not query_terms:
        return []

    documents = load_documents()
    if not documents:
        return []

    passages = []
    collection_frequency = Counter()
    collection_length = 0

    for document_id, text in documents.items():
        for passage_number, passage_text in enumerate(
            split_passages(text),
            start=1
        ):
            terms = preprocess(passage_text)
            term_frequency = Counter(terms)

            if not terms:
                continue

            passage = {
                "document": document_id,
                "passage_id": passage_number,
                "text": passage_text,
                "terms": term_frequency,
                "length": len(terms)
            }

            passages.append(passage)
            collection_frequency.update(terms)
            collection_length += len(terms)

    if not passages or collection_length == 0:
        return []

    query_terms = [
        term for term in query_terms
        if term in collection_frequency
    ]

    if not query_terms:
        return []

    results = []

    for passage in passages:
        score = 0.0
        matched_terms = []

        for term in query_terms:
            tf = passage["terms"].get(term, 0)

            if tf > 0:
                matched_terms.append(term)

            doc_probability = tf / passage["length"]
            collection_probability = (
                collection_frequency[term] / collection_length
            )

            probability = (
                LAMBDA * doc_probability
                + (1 - LAMBDA) * collection_probability
            )

            if probability > 0:
                score += math.log(probability)

        if matched_terms:
            results.append({
                "document": passage["document"],
                "passage_id": passage["passage_id"],
                "score": round(score, 6),
                "matched_terms": matched_terms,
                "text": passage["text"]
            })

    results.sort(
        key=lambda item: (
            item["score"],
            len(item["matched_terms"])
        ),
        reverse=True
    )

    return results[:max(1, int(top_k))]


# ----------------------------------------------------------
# MULTI-MODEL RANKING COMPARISON
# ----------------------------------------------------------

def _rank_map(results):
    ranking = {}

    for rank, result in enumerate(results, start=1):
        document_id = result.get(
            "document_id",
            result.get("document")
        )

        if not document_id:
            continue

        ranking[document_id] = {
            "rank": rank,
            "score": float(result.get("score", 0.0))
        }

    return ranking


def compare_retrieval_methods(query, top_k=5):
    """
    Compare BM25, TF-IDF and Language Model rankings.

    Scores are kept separate because raw scores from different retrieval
    models are not directly comparable. Rank positions and method agreement
    are the fair cross-model comparison signals.
    """

    bm25_results = bm25_search(query, top_k=top_k)
    tfidf_results = tfidf_search(query, top_k=top_k)
    language_results = language_model_search(query, top_k=top_k)

    bm25_rank = _rank_map(bm25_results)
    tfidf_rank = _rank_map(tfidf_results)
    language_rank = _rank_map(language_results)

    all_documents = set(
        bm25_rank
    ) | set(
        tfidf_rank
    ) | set(
        language_rank
    )

    comparison = []

    for document_id in all_documents:
        entries = [
            ("BM25", bm25_rank.get(document_id)),
            ("TF-IDF", tfidf_rank.get(document_id)),
            ("Language Model", language_rank.get(document_id))
        ]

        present = [entry for _, entry in entries if entry]

        best_rank = min(
            entry["rank"]
            for entry in present
        ) if present else 999

        agreement = len(present)

        rrf_score = sum(
            1 / (RRF_K + entry["rank"])
            for entry in present
        )

        comparison.append({
            "document": document_id,
            "bm25_rank": (
                bm25_rank[document_id]["rank"]
                if document_id in bm25_rank else None
            ),
            "bm25_score": (
                round(bm25_rank[document_id]["score"], 6)
                if document_id in bm25_rank else None
            ),
            "tfidf_rank": (
                tfidf_rank[document_id]["rank"]
                if document_id in tfidf_rank else None
            ),
            "tfidf_score": (
                round(tfidf_rank[document_id]["score"], 6)
                if document_id in tfidf_rank else None
            ),
            "language_model_rank": (
                language_rank[document_id]["rank"]
                if document_id in language_rank else None
            ),
            "language_model_score": (
                round(language_rank[document_id]["score"], 6)
                if document_id in language_rank else None
            ),
            "method_agreement": agreement,
            "best_rank": best_rank,
            "rrf_score": round(rrf_score, 8)
        })

    comparison.sort(
        key=lambda item: (
            -item["method_agreement"],
            item["best_rank"],
            -item["rrf_score"]
        )
    )

    return {
        "bm25": bm25_results,
        "tfidf": tfidf_results,
        "language_model": language_results,
        "comparison": comparison[:max(5, int(top_k))]
    }


# ----------------------------------------------------------
# CURATED EVALUATION SET
# ----------------------------------------------------------

# These are transparent domain relevance judgments, not model-generated
# labels. They are intended for academic IR evaluation and can be edited by
# an HR/domain expert later.
BENCHMARK_QUERIES = {
    "overtime policy": ["overtime_policy"],
    "promotion policy": ["promotion_guidelines"],
    "performance review": [
        "performance_review",
        "appraisal_policy",
        "performance_policy"
    ],
    "employee benefits": [
        "employee_benefits",
        "health_insurance",
        "retirement_benefits",
        "employee_assistance"
    ],
    "training": [
        "training_policy",
        "technical_training",
        "leadership_training",
        "skill_development"
    ],
    "annual leave": ["annual_leave", "leave_policy"],
    "sick leave": ["sick_leave", "leave_policy"],
    "employee assistance": ["employee_assistance"],
    "compensation": [
        "compensation_policy",
        "salary_policy",
        "bonus_policy"
    ],
    "leadership training": ["leadership_training"]
}


def _evaluate_single(retrieved, relevant_documents, k=5):
    relevant = set(relevant_documents)
    retrieved_ids = [
        item.get("document_id", item.get("document"))
        for item in retrieved[:k]
    ]

    retrieved_ids = [doc for doc in retrieved_ids if doc]

    hits = sum(
        1 for doc in retrieved_ids
        if doc in relevant
    )

    precision = hits / k if k else 0.0
    recall = hits / len(relevant) if relevant else 0.0

    if precision + recall:
        f1 = (2 * precision * recall) / (precision + recall)
    else:
        f1 = 0.0

    reciprocal_rank = 0.0
    for rank, doc in enumerate(retrieved_ids, start=1):
        if doc in relevant:
            reciprocal_rank = 1 / rank
            break

    return {
        "precision_at_k": round(precision, 4),
        "recall_at_k": round(recall, 4),
        "f1": round(f1, 4),
        "mrr": round(reciprocal_rank, 4),
        "relevant_hits": hits,
        "retrieved": retrieved_ids
    }


def evaluate_retrieval(k=5):
    """Evaluate all retrieval models on the curated HR benchmark."""

    methods = {
        "BM25": bm25_search,
        "TF-IDF": tfidf_search,
        "Language Model": language_model_search
    }

    query_results = []
    aggregate = {}

    for method_name, search_function in methods.items():
        metrics = []

        for query, relevant_docs in BENCHMARK_QUERIES.items():
            try:
                retrieved = search_function(query, top_k=k)
            except Exception:
                retrieved = []

            result = _evaluate_single(
                retrieved,
                relevant_docs,
                k=k
            )

            metrics.append(result)

            query_results.append({
                "query": query,
                "method": method_name,
                "precision_at_k": result["precision_at_k"],
                "recall_at_k": result["recall_at_k"],
                "f1": result["f1"],
                "mrr": result["mrr"]
            })

        count = len(metrics) or 1

        aggregate[method_name] = {
            "precision_at_k": round(
                sum(item["precision_at_k"] for item in metrics) / count,
                4
            ),
            "recall_at_k": round(
                sum(item["recall_at_k"] for item in metrics) / count,
                4
            ),
            "f1": round(
                sum(item["f1"] for item in metrics) / count,
                4
            ),
            "mrr": round(
                sum(item["mrr"] for item in metrics) / count,
                4
            )
        }

    return {
        "k": k,
        "benchmark_queries": len(BENCHMARK_QUERIES),
        "judgement_type": "Curated domain relevance judgments",
        "methods": aggregate,
        "query_results": query_results
    }


# ----------------------------------------------------------
# INFORMATION EXTRACTION FROM HR POLICY TEXT
# ----------------------------------------------------------

POLICY_TERMS = {
    "eligibility": ["eligible", "eligibility", "qualify", "qualification"],
    "approval": ["approval", "approve", "approved", "manager approval"],
    "limit": ["limit", "maximum", "minimum", "cap"],
    "requirement": ["required", "requirement", "must", "should"],
    "benefit": ["benefit", "insurance", "allowance", "reimbursement"],
    "development": ["training", "development", "skill", "learning"],
    "career": ["promotion", "career", "progression", "recognition"],
    "workload": ["overtime", "workload", "hours", "work life", "burnout"]
}


def extract_information(document_id):
    """Extract transparent, rule-based facts from an HR policy document."""

    documents = load_documents()
    text = documents.get(document_id, "")

    if not text:
        return {
            "document": document_id,
            "available": False,
            "entities": [],
            "numeric_facts": [],
            "key_sentences": []
        }

    lowered = text.lower()
    entities = []

    for label, terms in POLICY_TERMS.items():
        if any(term in lowered for term in terms):
            entities.append(label)

    numeric_patterns = [
        r"\b\d+(?:\.\d+)?\s*(?:days?|hours?|months?|years?)\b",
        r"\b\d+(?:\.\d+)?\s*%",
        r"(?:rs\.?|₹|inr)\s*\d[\d,]*(?:\.\d+)?"
    ]

    numeric_facts = []
    for pattern in numeric_patterns:
        numeric_facts.extend(
            match.group(0)
            for match in re.finditer(
                pattern,
                text,
                flags=re.IGNORECASE
            )
        )

    numeric_facts = list(dict.fromkeys(numeric_facts))[:10]

    sentences = [
        sentence.strip()
        for sentence in re.split(r"(?<=[.!?])\s+", text)
        if sentence.strip()
    ]

    key_sentences = []
    trigger_terms = [
        "eligible", "eligibility", "approval", "required",
        "limit", "maximum", "minimum", "allowance", "review",
        "training", "promotion", "overtime", "benefit"
    ]

    for sentence in sentences:
        sentence_lower = sentence.lower()
        if any(term in sentence_lower for term in trigger_terms):
            key_sentences.append(sentence)

    return {
        "document": document_id,
        "available": True,
        "entities": entities,
        "numeric_facts": numeric_facts,
        "key_sentences": key_sentences[:5]
    }


# ----------------------------------------------------------
# FULL IR ANALYSIS RESPONSE
# ----------------------------------------------------------

def build_ir_analysis(query, top_k=5, selected_method="bm25"):
    """Build the data consumed by the enhanced HR Knowledge UI."""

    comparison_data = compare_retrieval_methods(
        query,
        top_k=top_k
    )

    selected_results = comparison_data.get(selected_method, [])

    passages = search_passages(
        query,
        top_k=top_k
    )

    top_document = None
    if selected_results:
        top_document = selected_results[0].get(
            "document_id",
            selected_results[0].get("document")
        )

    extraction = (
        extract_information(top_document)
        if top_document
        else {
            "document": None,
            "available": False,
            "entities": [],
            "numeric_facts": [],
            "key_sentences": []
        }
    )

    evaluation = evaluate_retrieval(k=5)

    return {
        "comparison": comparison_data["comparison"],
        "model_results": {
            "bm25": comparison_data["bm25"],
            "tfidf": comparison_data["tfidf"],
            "language_model": comparison_data["language_model"]
        },
        "passages": passages,
        "information_extraction": extraction,
        "evaluation": evaluation,
        "score_notes": {
            "BM25": "Higher BM25 score indicates stronger relevance within BM25.",
            "TF-IDF": "Higher TF-IDF retrieval score indicates stronger term-weighted relevance within TF-IDF.",
            "Language Model": "Higher log query-likelihood is better; negative values are expected because log(probability) is negative for probabilities below 1."
        },
        "selected_method": selected_method
    }
