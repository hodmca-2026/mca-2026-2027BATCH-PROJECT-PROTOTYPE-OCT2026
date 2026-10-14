from Backend.ir.content_recommender import recommend_similar_urls
from Backend.ir import ir_service
from Backend.ir.inverted_index import (
    build_inverted_index,
    get_postings,
    retrieve_daat,
    retrieve_query_likelihood,
)
from Backend.ir.language_model import score_url_language_model
from Backend.ir.pagerank import calculate_project_pagerank
from Backend.ir.url_text import tokenize_url


CORPUS = [
    {"url": "https://paypal-login.example/verify", "classification": "phishing"},
    {"url": "https://account-secure.example/signin", "classification": "phishing"},
    {"url": "https://library.example/catalog", "classification": "legitimate"},
    {"url": "https://news.example/article", "classification": "legitimate"},
]


def test_url_tokenizer_extracts_domain_and_path_terms():
    assert tokenize_url("https://paypal-login.example/verify-account") == [
        "paypal", "login", "example", "verify", "account"
    ]


def test_multinomial_language_model_uses_labeled_corpus_and_smoothing():
    result = score_url_language_model("https://paypal-login.example/verify", CORPUS)
    assert result["status"] == "available"
    assert 0 < result["score"] < 1
    assert "login" in result["suspicious_terms"]
    assert result["training_documents"] == 4


def test_language_model_laplace_smoothing_handles_unseen_query_terms():
    result = score_url_language_model("https://never-seen-term.example/login", CORPUS)
    assert result["status"] == "available"
    assert 0 < result["score"] < 1
    assert result["term_probabilities"]["never"]["phishing"] > 0
    assert result["term_probabilities"]["never"]["legitimate"] > 0
    expected_phishing_probability = 2 / (8 + 15)
    assert result["term_probabilities"]["login"]["phishing"] == expected_phishing_probability


def test_language_model_training_cache_is_not_mutated_by_query_terms():
    known_query = "https://paypal-login.example/verify"
    baseline = score_url_language_model(known_query, CORPUS)
    score_url_language_model("https://brand-new-token.example", CORPUS)
    after_unseen_query = score_url_language_model(known_query, CORPUS)
    assert after_unseen_query == baseline


def test_project_pagerank_calculates_graph_rank():
    result = calculate_project_pagerank(
        "https://paypal-login.example/verify-account",
        [record["url"] for record in CORPUS],
    )
    assert result["status"] == "available"
    assert 0 < result["score"] <= 1
    assert 1 <= result["rank"] <= result["graph_nodes"]
    assert result["ranking_type"] == "project-level URL/domain graph ranking"


def test_project_pagerank_reports_insufficient_graph():
    result = calculate_project_pagerank("https://isolated.example", [])
    assert result["status"] == "unavailable"
    assert result["message"] == "Insufficient graph data."
    assert result["graph_nodes"] == 1
    assert result["graph_edges"] == 0


def test_project_pagerank_handles_a_disconnected_dangling_target():
    result = calculate_project_pagerank(
        "https://isolated.example/unique-path",
        ["https://one.example/shared", "https://two.example/shared"],
    )
    assert result["status"] == "available"
    assert result["graph_edges"] == 1
    assert 0 < result["score"] <= 1


def test_tfidf_recommender_returns_only_corpus_urls():
    corpus_urls = [record["url"] for record in CORPUS]
    result = recommend_similar_urls("https://paypal-security.example/login", corpus_urls)
    recommendations = result["recommendations"]
    assert result["status"] == "available"
    assert recommendations
    assert all(item["url"] in corpus_urls for item in recommendations)
    assert all(0 < item["similarity"] <= 1 for item in recommendations)
    assert len(recommendations) <= 3


def test_tfidf_recommender_excludes_normalized_current_url():
    result = recommend_similar_urls(
        "https://same.example/",
        ["https://same.example", "https://same.example/"],
    )
    assert result["recommendations"] == []


def test_tfidf_recommender_returns_only_positive_similarities_in_order():
    result = recommend_similar_urls(
        "https://paypal-login.example/verify",
        [record["url"] for record in CORPUS],
    )
    similarities = [item["similarity"] for item in result["recommendations"]]
    assert similarities
    assert all(score > 0 for score in similarities)
    assert similarities == sorted(similarities, reverse=True)


def test_tfidf_recommender_breaks_equal_scores_by_normalized_url():
    result = recommend_similar_urls(
        "https://target.example/login",
        ["https://c.example/login", "https://b.example/login"],
    )
    urls = [item["url"] for item in result["recommendations"]]
    assert urls == ["https://b.example/login", "https://c.example/login"]


def test_tfidf_recommender_handles_empty_corpus_and_unknown_terms():
    assert recommend_similar_urls("https://unknown.invalid/path", []) == {
        "status": "available",
        "recommendations": [],
    }
    result = recommend_similar_urls(
        "https://unknown.invalid/path",
        ["https://known.example/other"],
    )
    assert result["recommendations"] == []


def test_inverted_index_builds_sorted_unique_postings_for_duplicate_records():
    duplicate_url = "https://echo.echo.example/echo"
    index = build_inverted_index(
        [(duplicate_url, "phishing"), (duplicate_url, "phishing")]
    )
    assert get_postings(index, "echo") == (1, 2)
    assert get_postings(index, "example") == (1, 2)
    assert index.documents[1].url == index.documents[2].url
    assert index.documents[1].document_id != index.documents[2].document_id


def test_inverted_index_handles_empty_documents_and_missing_terms():
    index = build_inverted_index([])
    assert index.documents == {}
    assert index.postings == {}
    assert get_postings(index, "missing") == ()


def test_document_query_likelihood_ranks_matching_history_records():
    index = build_inverted_index(CORPUS)
    result = retrieve_query_likelihood(index, "https://paypal-login.example/verify")
    scores = [item["score"] for item in result["results"]]
    assert result["status"] == "available"
    assert result["scoring_method"] == "smoothed unigram document query likelihood"
    assert result["results"][0]["url"] == CORPUS[0]["url"]
    assert scores == sorted(scores, reverse=True)
    assert all(item["score_type"] == "log_query_likelihood" for item in result["results"])


def test_document_query_likelihood_smooths_unseen_terms_and_handles_empty_queries():
    index = build_inverted_index(CORPUS)
    unseen_result = retrieve_query_likelihood(index, ["not-in-corpus"])
    assert unseen_result["results"] == []
    assert unseen_result["unknown_terms"] == ["corpus", "in", "not"]
    empty_result = retrieve_query_likelihood(index, [])
    assert empty_result["results"] == []
    assert empty_result["status"] == "available"


def test_daat_or_and_modes_repeated_terms_and_unknown_terms():
    index = build_inverted_index(CORPUS)
    or_result = retrieve_daat(index, ["login", "verify", "login"], match_mode="OR")
    and_result = retrieve_daat(index, ["login", "verify"], match_mode="AND")
    unknown_and = retrieve_daat(index, ["login", "unknown"], match_mode="AND")
    unknown_or = retrieve_daat(index, ["login", "unknown"], match_mode="OR")

    assert or_result["match_mode"] == "OR"
    assert or_result["results"]
    assert or_result["results"][0]["url"] == CORPUS[0]["url"]
    assert all(item["score_type"] == "cosine_similarity" for item in or_result["results"])
    assert [item["url"] for item in and_result["results"]] == [CORPUS[0]["url"]]
    assert unknown_and["results"] == []
    assert unknown_or["results"]
    assert unknown_or["unknown_terms"] == ["unknown"]
    assert retrieve_daat(index, [], match_mode="OR")["results"] == []


def test_daat_ties_are_deterministic_and_empty_history_is_safe():
    duplicate_url = "https://repeat.example/login"
    index = build_inverted_index(
        [(duplicate_url, "phishing"), (duplicate_url, "legitimate")]
    )
    results = retrieve_daat(index, "https://repeat.example/login")["results"]
    assert [item["document_id"] for item in results] == [1, 2]
    assert retrieve_daat(build_inverted_index([]), "https://repeat.example/login")["status"] == "unavailable"
    assert retrieve_query_likelihood(build_inverted_index([]), "https://repeat.example/login")["status"] == "unavailable"


def test_ir_service_keeps_other_components_when_one_fails(monkeypatch):
    records = (
        ("https://paypal-login.example/verify", "phishing"),
        ("https://library.example/catalog", "legitimate"),
    )
    monkeypatch.setattr(ir_service, "_database_signature", lambda: (2, 2))
    monkeypatch.setattr(ir_service, "_load_history", lambda signature: records)

    def fail_language_model(*args):
        raise RuntimeError("simulated language-model failure")

    monkeypatch.setattr(ir_service, "score_url_language_model", fail_language_model)
    result = ir_service.analyze_url_with_ir("https://paypal-login.example/account")

    assert result["language_model"]["status"] == "unavailable"
    assert result["pagerank"]["status"] == "available"
    assert result["content_recommendations"]["status"] == "available"
    assert result["inverted_index"]["status"] == "available"
    assert result["document_retrieval"]["status"] == "available"
    assert result["query_likelihood"]["status"] == "available"
    assert result["relevance_ranking"]["score_fusion"] is False
