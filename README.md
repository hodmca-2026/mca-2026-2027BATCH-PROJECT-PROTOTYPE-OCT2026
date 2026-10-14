# PhishGuard – Phishing Website Detection Using Machine Learning

PhishGuard is a cybersecurity demonstration that classifies submitted URLs with the existing Random Forest model and supplements its result with URL security checks and local Information Retrieval (IR) analysis.

## Technologies

- Python, FastAPI, Uvicorn, Pydantic
- scikit-learn, pandas, NumPy, joblib, tldextract
- SQLite
- HTML, CSS, and JavaScript
- Existing Random Forest model: `models/random_forest_url_final.joblib`

TF-IDF uses the project's existing scikit-learn dependency; PageRank is implemented locally. Sumit's URL feature extractor uses `tldextract` with its bundled suffix snapshot, so feature extraction does not fetch a suffix list from the network.

## Team Responsibilities

- Chandan: frontend, IR integration, testing, and documentation.
- Raj: backend, database, DNS/SSL, and security implementation.
- Sumit: dataset, Random Forest model, ML feature extraction, and training.

## Architecture

1. The API validates and normalizes the submitted URL.
2. Existing feature extraction and the Random Forest produce the primary ML evidence.
3. DNS, TLS, and URL-security checks provide technical evidence; DNS/TLS connections reject non-public address resolutions, and TLS connects to the validated address while verifying the hostname certificate.
4. The existing risk engine calculates the risk result. IR does not replace Random Forest or change that score.
5. Supporting IR calculations analyze URL terms, rank the URL in a project graph, and retrieve similar historical URLs.
6. The response, including `ir_analysis`, is stored in the existing SQLite scan history and displayed by the frontend.

Random Forest remains the primary phishing classifier. IR supplies supporting retrieval, ranking, and recommendation evidence only.

## Information Retrieval

The project has no source dataset in `Data/`; the IR corpus therefore uses the existing `scan_history` table in `db.sqlite3`. The IR service opens the database read-only, normalizes URLs, and excludes malformed or hostless records. It does not visit submitted URLs. The corpus/index and fitted language-model counts are cached; changing scan history changes the corpus cache key.

### Unit IV: Multinomial Language Model

`Backend/ir/language_model.py` tokenizes the hostname, path, and query of URLs. It builds separate phishing and legitimate multinomial term distributions from labeled scan history, applies additive (Laplace) smoothing, and calculates a phishing likelihood from the observed terms and class priors. Reported suspicious terms are query tokens whose smoothed probability is higher in the phishing history than the legitimate history. Labels that are not clearly phishing/high-risk or legitimate/low-risk are excluded from this model.

This score is corpus-dependent supporting evidence, not the Random Forest prediction or a calibrated real-world probability.

### Unit V: Project-Level PageRank

`Backend/ir/pagerank.py` uses a custom PageRank implementation. Nodes are normalized URLs from scan history plus the submitted URL. An undirected project relationship edge is added when URLs share the same host or parent/subdomain relationship, or when their non-generic URL-token Jaccard similarity is at least 0.25. PageRank uses damping 0.85, uniform initialization, dangling-node redistribution, and iterative convergence.

**The PageRank implementation is a project-level URL/domain graph ranking model and is not Google's live PageRank.** The project has no collected hyperlink graph and does not crawl the web.

### Unit VI: Content-Based Recommendation

`Backend/ir/content_recommender.py` builds a cached scikit-learn TF-IDF index over normalized historical URLs. Its URL tokenizer provides word unigrams and bigrams; cosine similarity ranks the top three positive-similarity historical URLs. The exact normalized input URL is excluded. Recommendations always come from scan history; the system does not invent or fetch results.

### Historical URL Retrieval

`Backend/ir/inverted_index.py` builds a cached inverted index from valid scan-history records. Posting lists contain sorted document IDs, with each document ID mapped to its normalized URL record. Document-level query likelihood uses a Laplace-smoothed unigram model and ranks OR-matched records by log likelihood. DAAT traverses posting lists directly: OR returns records matching any distinct query term, while AND requires every distinct term. DAAT ranks with cosine TF-IDF and uses normalized URL and document ID as deterministic tie-breakers. The API exposes index counts, query-likelihood results, DAAT results, and the ranking method as additive fields under `ir_analysis`.

These retrieval scores describe historical URL-string matching only. Query likelihood and cosine similarity are not fused together, and neither retrieval nor PageRank changes the phishing risk score.

If a component cannot run, its `status` is `unavailable`; the scan endpoint still returns the existing ML/security/risk result. No IR score is added to the risk formula.

## Workflow

```text
URL input
	-> validation and feature extraction
	-> Random Forest (primary classifier)
	-> DNS / SSL / URL security checks
	-> existing risk engine
	-> IR support: language model + project PageRank + TF-IDF retrieval
	-> API response, SQLite history, security report
```

IR operates on URL strings and local SQLite records only. It does not execute JavaScript, fetch page contents, or automatically visit submitted URLs.

## Project Structure

```text
Backend/
	ir/
		content_recommender.py
		inverted_index.py
		ir_service.py
		language_model.py
		pagerank.py
		url_text.py
	main.py
	database.py
	risk_engine.py
	security/
	utils/
Frontend/
	index.html
	script.js
	style.css
	assets/phishguard-logo.png
models/
	random_forest_url_final.joblib
Test/
```

The existing local PhishGuard logo is preserved and used with the black-and-gold interface.

## Installation and Run

From the repository root in PowerShell:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

Start the backend:

```powershell
uvicorn Backend.main:app --reload --host 127.0.0.1 --port 8000
```

In a second terminal, serve the frontend:

```powershell
cd Frontend
python -m http.server 5501 --bind 127.0.0.1
```

Open `http://127.0.0.1:5501`. The scan endpoint is `POST http://127.0.0.1:8000/api/v1/scan`; history is `GET http://127.0.0.1:8000/api/v1/history`.

## Deployment

`render.yaml` defines a Render Python web service and static frontend. The API build retrieves the existing Random Forest through Git LFS, installs `requirements.txt`, and mounts a persistent disk for `db.sqlite3`. The static build substitutes the API service host into `Frontend/api-config.js`, so production does not call localhost. The same API config defaults to localhost for development.

The Blueprint has not been deployed or externally verified. Deployment requires an authorized Render account/service creation; no Render CLI or account credentials were available in the implementation environment. Do not treat the local deployment configuration as a live deployment.

## API Response

The scan response retains its existing fields and adds `ir_analysis`:

```json
{
	"classification": "legitimate",
	"risk_score": 13.0,
	"confidence": 0.78,
	"ml": {"classification": "legitimate"},
	"dns": {"resolves": true},
	"ssl": {"valid": true},
	"url_security": {},
	"ir_analysis": {
		"status": "available",
		"corpus_size": 5,
		"language_model": {
			"status": "available",
			"score": 0.004484,
			"suspicious_terms": []
		},
		"pagerank": {
			"status": "available",
			"score": 0.04545455,
			"rank": 4,
			"ranking_type": "project-level URL/domain graph ranking"
		},
		"content_recommendations": {
			"status": "available",
			"recommendations": [
				{"url": "http://example.com", "similarity": 0.500491},
				{"url": "https://example.com", "similarity": 0.500491},
				{"url": "https://paypal-login-security.example.com", "similarity": 0.201474}
			]
		}
	}
}
```

The values above illustrate the response shape from a local run; scores and recommendations are calculated from the current scan history and will vary as that history changes.

## Testing

```powershell
python -m pytest Test -q
```

The tests cover the model feature contract and Sumit-aligned feature values, scan endpoint and invalid-history behavior, private-address DNS/TLS blocking, IR tokenization, smoothed language-model scoring, graph ranking, TF-IDF retrieval, inverted-index and DAAT retrieval, and IR/API failure isolation. API tests use temporary SQLite databases and mocked DNS/TLS results; controlled synthetic URLs are not opened as websites.

## Limitations

- IR quality depends on the size and label quality of local scan history. The current database is small and is not a substitute for the original training dataset.
- PageRank is relative to the constructed project graph and is not a web-wide authority metric.
- URL-only TF-IDF similarity does not inspect page content, redirects, or actual hyperlinks.
- DNS and TLS results reflect the network environment and may be unavailable even for a legitimate domain.

## Frontend Result States

- Invalid input such as `hello` is rejected with a validation message. The result, confidence, URL features, DNS/SSL checks, IR panel, and report are cleared, and the input is not added to browser history.
- A new scan clears the previous result while it is running. If the backend is unavailable or returns an error, the result/report show an unavailable state instead of retaining old scan data.
- The ML classification and overall security verdict are separate. For example, the Random Forest may say `legitimate` while the combined risk assessment says `phishing`; the report explains that difference using the returned risk score and scan evidence.
- Backend scan history is persisted in SQLite and exposed through `GET /api/v1/history`. The current frontend dashboard and table use browser-local history in `localStorage`; they are not automatically hydrated from that endpoint on each page load. The Clear History button clears that browser-local view, not the SQLite database.

## Future Scope

- Collect a larger, reviewed and clearly labeled project URL corpus to improve the supporting language-model estimates and similarity results.
- Evaluate the Random Forest and IR signals on held-out data; calibrate reported probabilities before presenting them as real-world confidence estimates.
- If a verified project hyperlink dataset becomes available, compare its graph ranking with the documented URL/domain relationship graph.
- Add an explicit, approved synchronization workflow between backend scan history and browser history without changing existing history-clearing semantics.
- Improve accessibility and usability testing across additional browsers and screen-reader configurations.
