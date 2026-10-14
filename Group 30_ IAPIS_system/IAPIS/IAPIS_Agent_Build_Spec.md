# IAPIS — Agent Build Specification
### Industrial Accident Prevention Intelligence System
**Document type:** Implementation-ready technical PRD for an autonomous coding agent (e.g. Claude Code)
**Goal:** Give the agent everything it needs to scaffold, implement, test, and run this project with no further clarification needed.

---

## 0. How to Use This Document (instructions to the agent)

Build the project in the **exact phase order** in Section 6. After each phase, run the phase's acceptance test before moving to the next. Do not skip ahead. Keep every component CPU-only and free-tier — never introduce a paid API, a GPU-only dependency, or a hosted paid vector DB. If a required package is unavailable, substitute the nearest free/open-source equivalent and note the substitution in `CHANGELOG.md`.

All commands below assume Python 3.10+ on Linux, working directory `iapis/`.

---

## 1. System Summary

A Retrieval-Augmented Generation (RAG) system for industrial safety. User asks a natural-language question → system retrieves similar historical incident/near-miss reports (hybrid BM25 + dense vector search) → reranks with a cross-encoder → detects risk patterns (recurrence count, LSTM sensor-drift flag, autoencoder anomaly flag) → generates a grounded safety recommendation via a free LLM API → (optional) accepts a photo and runs YOLOv8 PPE detection. Delivered as a Streamlit app backed by a FastAPI service layer.

---

## 2. Non-Negotiable Constraints

| Constraint | Value |
|---|---|
| Compute | CPU-only must work end-to-end (GPU optional speed-up only, never required) |
| Cost | $0 — every package, model, dataset, and API must have a free tier sufficient for the demo |
| RAM | Must run within 8GB RAM |
| Data | No PII; no proprietary company data; only synthetic + public OSHA data |
| Models on disk | Combined footprint of all local models ≤ 600MB |
| Response latency | Retrieval + rerank ≤ 5s on CPU for a corpus of ≤500 documents |
| LLM calls | Only retrieved text snippets + user query are sent externally, never raw files/images |

---

## 3. Tech Stack & Exact Dependencies

Create `requirements.txt`:

```
fastapi==0.115.0
uvicorn[standard]==0.30.6
streamlit==1.38.0
sentence-transformers==3.1.1
rank-bm25==0.2.2
chromadb==0.5.5
spacy==3.7.6
torch==2.4.1
scikit-learn==1.5.2
pandas==2.2.2
numpy==1.26.4
pydantic==2.9.2
python-dotenv==1.0.1
requests==2.32.3
beautifulsoup4==4.12.3
groq==0.11.0
google-generativeai==0.8.3
ultralytics==8.3.0
Pillow==10.4.0
pytest==8.3.3
```

After creating the file, the agent must run:
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

### Model choices (fixed — do not substitute without noting why)
- Embedding model: `sentence-transformers/all-MiniLM-L6-v2` (~80MB)
- Reranker: `cross-encoder/ms-marco-MiniLM-L-6-v2` (~90MB)
- NER: spaCy `en_core_web_sm` (~13MB)
- LSTM: custom, PyTorch, <1MB (trained from scratch on synthetic data)
- Autoencoder: custom, PyTorch, <1MB (trained from scratch)
- CV (optional): `yolov8n.pt` via `ultralytics` (~6MB)
- LLM (external API, free tier): **Groq** (`llama-3.1-8b-instant`) primary, **Gemini** (`gemini-1.5-flash`) fallback

### Required environment variables — create `.env.example`
```
GROQ_API_KEY=your_key_here
GEMINI_API_KEY=your_key_here
LLM_PROVIDER=groq   # or "gemini"
```
Agent must load these via `python-dotenv` and must NEVER hardcode keys. If neither key is present, the recommendation module must fall back to a template-based (non-LLM) summary — the pipeline must not crash.

---

## 4. Repository Structure (create exactly this layout)

```
iapis/
├── .env.example
├── requirements.txt
├── README.md
├── CHANGELOG.md
├── data/
│   ├── raw/
│   │   └── osha_scraped.json
│   ├── reports/
│   │   └── reports.json
│   ├── sensor_logs.csv
│   └── maintenance_logs.csv
├── scripts/
│   ├── generate_synthetic_reports.py
│   ├── generate_synthetic_sensor_data.py
│   └── scrape_osha.py
├── ingestion/
│   ├── __init__.py
│   ├── schema.py
│   ├── preprocess.py
│   └── ner_extract.py
├── retrieval/
│   ├── __init__.py
│   ├── embed_store.py
│   ├── bm25_search.py
│   ├── hybrid_search.py
│   └── reranker.py
├── risk_models/
│   ├── __init__.py
│   ├── lstm_drift.py
│   ├── autoencoder_anomaly.py
│   └── recurrence_rank.py
├── recommend/
│   ├── __init__.py
│   ├── llm_client.py
│   └── prompt_templates.py
├── cv_branch/
│   ├── __init__.py
│   └── ppe_detect.py
├── api/
│   ├── __init__.py
│   ├── main.py
│   └── models.py
├── app.py
├── tests/
│   ├── test_ingestion.py
│   ├── test_retrieval.py
│   ├── test_risk_models.py
│   └── test_api.py
└── models_store/          # saved .pt / chroma persistence, gitignored
```

---

## 5. Data Schemas (must match exactly — downstream modules depend on these field names)

### 5.1 `data/reports/reports.json` — list of report objects
```json
{
  "id": "RPT-0001",
  "type": "accident | near_miss | maintenance_log",
  "title": "Motor M-12 overheating causing smoke event",
  "text": "Full free-text narrative of what happened...",
  "equipment": "induction motor",
  "hazard_type": "overheating",
  "location": "Building 3, Line 2",
  "date": "2024-03-14",
  "severity": "low | medium | high | critical",
  "source": "synthetic | osha"
}
```
Required fields: `id, type, title, text`. All others optional but should be populated when known (NER will fill `equipment`/`hazard_type` if missing).

### 5.2 `data/sensor_logs.csv` (for LSTM)
```
timestamp,equipment_id,temperature_c,vibration_mm_s,rpm
2024-01-01T00:00:00,M-12,58.2,1.1,1450
2024-01-01T01:00:00,M-12,59.0,1.2,1448
...
```
Must contain ≥3 distinct `equipment_id` values, ≥30 days hourly data each, with at least 2 injected "drift" windows per equipment (gradual temperature ramp over 6–12 hours to a threshold that would trigger an alert) and normal noise elsewhere.

### 5.3 `data/maintenance_logs.csv` (for Autoencoder)
```
log_id,equipment_id,vibration_rms,temp_delta,oil_pressure,run_hours_since_service,is_anomalous_label
LOG-0001,M-12,0.8,3.2,45.1,120,0
```
`is_anomalous_label` is ONLY for evaluation (0/1), must never be fed as a model input feature. ~10% of rows should be synthetically injected anomalies (label=1).

---

## 6. Build Phases & Acceptance Criteria

### Phase 0 — Scaffold
- Create the full directory tree from Section 4 (empty `__init__.py` files where noted).
- Create `.env.example`, `requirements.txt`, `README.md` with setup instructions.
- **Accept when:** `pip install -r requirements.txt` succeeds with no errors.

### Phase 1 — Synthetic Data Generation
- `scripts/generate_synthetic_reports.py`: generate 60–80 report objects matching schema 5.1, covering ≥5 equipment types (motors, conveyors, forklifts, electrical panels, compressors) and all 3 `type` values. If an LLM key is available, use it to generate varied narratives; otherwise use templated string generation with randomized parameters so it works with zero API keys.
- `scripts/generate_synthetic_sensor_data.py`: generate `sensor_logs.csv` and `maintenance_logs.csv` per schemas 5.2/5.3 using `numpy` (sine-wave baseline + gaussian noise + injected linear drift/anomaly segments).
- `scripts/scrape_osha.py`: fetch https://www.osha.gov/severe-injury-reports (or equivalent public listing page), extract 10–15 summaries with `requests` + `BeautifulSoup4`, map into schema 5.1 with `"source": "osha"`, `"type": "accident"`. Must handle request failures gracefully (retry once, then skip — never crash the pipeline if OSHA site is unreachable; fall back to synthetic-only corpus with a logged warning).
- **Accept when:** `data/reports/reports.json` has ≥60 entries, `sensor_logs.csv` and `maintenance_logs.csv` exist and pass a pandas schema check (columns present, no NaNs).

### Phase 2 — Ingestion & NLP Preprocessing (IR Unit IV)
- `ingestion/schema.py`: pydantic model `Report` matching 5.1.
- `ingestion/preprocess.py`: function `clean_text(text: str) -> str` (lowercase, strip boilerplate headers/footers, collapse whitespace); function `chunk_text(text: str, max_tokens: int = 200) -> list[str]` for any report longer than the embedding model's comfortable window.
- `ingestion/ner_extract.py`: function `extract_entities(text: str) -> dict` using spaCy — extract equipment-like nouns and hazard keywords via a small keyword/entity-ruler pattern list (e.g. `["motor","conveyor","forklift","panel","compressor","overheat","fire","fall","spill","electrical shock"]`) layered on top of spaCy's NER. Populate missing `equipment`/`hazard_type` fields in reports that lack them.
- **Accept when:** running `python -m ingestion.preprocess` on `reports.json` produces a cleaned, entity-enriched JSON with 100% of reports having non-null `equipment` and `hazard_type`.

### Phase 3 — Retrieval Core (IR Unit IV & V)
- `retrieval/embed_store.py`:
  - `build_index(reports: list[dict]) -> None` — embeds each report's `title + text` with `all-MiniLM-L6-v2`, upserts into a local ChromaDB persistent collection at `models_store/chroma/`.
  - `dense_search(query: str, k: int = 10) -> list[dict]` — returns `[{id, score, report}]`.
- `retrieval/bm25_search.py`:
  - `build_bm25(reports: list[dict]) -> BM25Okapi` — tokenized corpus index (persist with pickle to `models_store/bm25.pkl`).
  - `bm25_search(query: str, k: int = 10) -> list[dict]`.
- `retrieval/hybrid_search.py`:
  - `hybrid_search(query: str, k: int = 10, alpha: float = 0.5) -> list[dict]` — Reciprocal Rank Fusion or weighted-score fusion of dense + BM25 results; `alpha` weights dense vs sparse. Document this as implementing "ranking with language models" (BM25 = probabilistic LM side) fused with the neural embedding side, per IR Unit IV.
- `retrieval/reranker.py`:
  - `rerank(query: str, candidates: list[dict], top_n: int = 5) -> list[dict]` using `cross-encoder/ms-marco-MiniLM-L-6-v2`; returns candidates sorted by cross-encoder score, each annotated with `rerank_score`.
- **Accept when:** `pytest tests/test_retrieval.py` passes: (a) hybrid_search returns non-empty results for a known query, (b) a hand-labeled query/relevant-doc pair appears in the top-5 after rerank but was outside top-5 in bm25-only search (demonstrates rerank adds value on at least one test case).

### Phase 4 — Risk Pattern Detection

**4a. LSTM sensor-drift model (DL Unit IV)** — `risk_models/lstm_drift.py`
- `class DriftLSTM(nn.Module)`: input size 3 (temperature, vibration, rpm), 1–2 LSTM layers, hidden size 32, followed by a linear head predicting next-step temperature (regression) OR a binary "drift risk next 6h" classification head — implement the classification head (more directly useful for alerts).
- `train_lstm(csv_path: str, epochs: int = 15) -> None` — sliding-window sequences (window=24h), trains on `sensor_logs.csv`, saves weights to `models_store/lstm_drift.pt`.
- `predict_drift_risk(equipment_id: str, recent_window: pd.DataFrame) -> dict` — returns `{equipment_id, risk_score: float 0-1, flag: bool}`.
- Explicitly comment in code: *"Implements DL Unit IV — RNN/LSTM sequence learning applied to sensor time-series; selective forget/write gates allow the model to retain long-range temperature trend while ignoring short noise spikes."*
- **Accept when:** `pytest tests/test_risk_models.py::test_lstm` passes — model correctly flags the injected drift windows with recall ≥ 0.7 on the synthetic validation split.

**4b. Autoencoder anomaly detector (DL Unit V)** — `risk_models/autoencoder_anomaly.py`
- `class LogAutoencoder(nn.Module)`: dense encoder (4 → 8 → 3) / decoder (3 → 8 → 4) on the numeric features of `maintenance_logs.csv` (`vibration_rms, temp_delta, oil_pressure, run_hours_since_service`), standardized with `sklearn.StandardScaler`.
- `train_autoencoder(csv_path: str, epochs: int = 50) -> None` — train on rows where `is_anomalous_label == 0` only (unsupervised on "normal" behavior), save to `models_store/autoencoder.pt` + fitted scaler to `models_store/scaler.pkl`.
- `score_anomaly(log_row: dict) -> dict` — returns `{log_id, reconstruction_error: float, is_anomalous: bool}` using a threshold = mean + 2·std of training reconstruction error.
- Explicitly comment: *"Implements DL Unit V — deep autoencoder for anomaly detection, directly analogous to the course's network-traffic anomaly-detection case study, re-applied to maintenance-log feature vectors."*
- **Accept when:** `pytest tests/test_risk_models.py::test_autoencoder` passes — AUC ≥ 0.75 distinguishing `is_anomalous_label` on the held-out validation split.

**4c. Recurrence ranking (IR Unit V)** — `risk_models/recurrence_rank.py`
- `compute_recurrence_scores(reports: list[dict]) -> dict[str, float]` — for each report, count how many other reports share the same `(equipment, hazard_type)` pair, normalize into a 0–1 "recurrence score." Document as a simplified, non-graph analogue of link-based/PageRank-style importance (co-occurrence count standing in for "inbound links").
- **Accept when:** unit test confirms reports sharing equipment+hazard get strictly higher recurrence scores than singleton reports.

### Phase 5 — Recommendation Generation (IR Unit VI)
- `recommend/prompt_templates.py`: a single grounded prompt template that takes `{query, reranked_reports, risk_flags}` and instructs the LLM to (1) summarize the pattern, (2) cite report IDs used, (3) give 2–4 concrete safety actions, (4) explicitly refuse to invent facts not present in the provided reports.
- `recommend/llm_client.py`:
  - `generate_recommendation(query: str, evidence: list[dict], risk_flags: dict) -> dict` — calls Groq first; on failure/missing key, calls Gemini; on failure/missing key, falls back to a deterministic template (`"Based on {n} similar past reports involving {equipment}, common causes were {top_hazards}. Recommended actions: ..."`) built from the evidence without any external call.
  - Never send full report text beyond what's needed — cap total evidence sent to ~1500 tokens.
- **Accept when:** calling `generate_recommendation` with no API keys set still returns a valid, non-empty structured response (proves graceful degradation).

### Phase 6 — API Layer
- `api/models.py`: pydantic request/response models — `QueryRequest{query: str, top_k: int=5}`, `QueryResponse{results: list[ReportResult], risk_summary: dict, recommendation: str}`.
- `api/main.py`: FastAPI app with:
  - `POST /search` → runs hybrid_search → rerank → recurrence_rank → returns ranked reports with scores.
  - `POST /analyze` → runs `/search` + LSTM/autoencoder flags for any equipment mentioned in top results + `generate_recommendation` → returns full `QueryResponse`.
  - `POST /detect-ppe` (only active if `ultralytics` import succeeds) → accepts image upload, runs YOLOv8n, returns detected classes/boxes.
  - `GET /health` → `{status: "ok"}`.
- **Accept when:** `uvicorn api.main:app` starts, `GET /health` returns 200, `POST /analyze` with a sample query returns a well-formed `QueryResponse` in under 5s.

### Phase 7 — CV Branch (optional, DL Unit VI)
- `cv_branch/ppe_detect.py`: `detect_ppe(image_path: str) -> list[dict]` using pretrained `yolov8n.pt` (general object detector as a stand-in unless a PPE-specific fine-tuned checkpoint is provided by the user); if a fine-tuned Roboflow-trained weights file is present at `models_store/ppe_yolo.pt`, prefer that instead.
- Optional fine-tuning script `scripts/finetune_ppe_yolo.py` documented in README for the user to run manually in Colab (agent should not attempt a long GPU training run in this environment).
- **Accept when:** `detect_ppe` runs on a sample image and returns a list (even if empty) without raising.

### Phase 8 — Streamlit UI
- `app.py`: single-page Streamlit app —
  - Text input for the query.
  - Sidebar sliders: `top_k`, `alpha` (BM25 vs dense weight).
  - Main panel: ranked report cards (title, snippet, scores, recurrence badge).
  - "Risk Flags" panel: LSTM drift flags + autoencoder anomaly flags for equipment mentioned in results.
  - "Recommendation" panel: LLM-generated (or fallback template) recommendation with cited report IDs.
  - Optional file-uploader for a photo → calls `/detect-ppe` → overlays detected boxes.
  - Calls the FastAPI backend over HTTP (`requests`) rather than importing modules directly, so the two layers stay decoupled.
- **Accept when:** `streamlit run app.py` (with `uvicorn api.main:app` running separately) lets a user type "overheating motor" and see results, risk flags, and a recommendation rendered without errors.

### Phase 9 — Tests, README, Polish
- Ensure `pytest` (full suite) passes.
- `README.md` must include: setup steps, how to run backend + frontend, how to regenerate synthetic data, where to add API keys, and a short "which concept maps to which chapter" table (reuse Section 2 of the earlier PRD).
- `CHANGELOG.md`: log any substitutions made from Section 3.

---

## 7. API Contracts (for the agent to implement exactly)

### `POST /search`
Request:
```json
{ "query": "overheating motor incidents", "top_k": 5 }
```
Response:
```json
{
  "results": [
    {
      "id": "RPT-0007",
      "title": "...",
      "snippet": "...",
      "dense_score": 0.83,
      "bm25_score": 4.2,
      "rerank_score": 0.91,
      "recurrence_score": 0.6,
      "equipment": "induction motor",
      "hazard_type": "overheating"
    }
  ]
}
```

### `POST /analyze`
Request: same as `/search`.
Response adds:
```json
{
  "results": [ "...same as above..." ],
  "risk_summary": {
    "equipment_flags": {
      "M-12": { "lstm_drift_risk": 0.78, "flag": true, "autoencoder_anomaly": true }
    },
    "recurrence_pattern": "3 of 5 retrieved reports involve induction motors with overheating over the past 6 months"
  },
  "recommendation": "Based on 5 similar past reports... [cites RPT-0007, RPT-0012] Recommended actions: 1) ... 2) ..."
}
```

---

## 8. Definition of Done (whole project)
- [ ] `pytest` full suite green
- [ ] Backend + frontend run locally with only `requirements.txt` and free API keys (or zero keys, via fallback)
- [ ] A demo query about "overheating motors" returns relevant reports, a risk flag, and a grounded recommendation
- [ ] README documents setup, architecture, and the chapter-mapping table
- [ ] No paid service, no GPU-only dependency, total local model size ≤ 600MB
- [ ] CHANGELOG documents any deviations from this spec

---

## 9. Explicit Non-Goals (agent should not attempt these)
- Production-grade authentication/security
- Distributed/clustered deployment (single-process demo is sufficient)
- Large-scale real-time crawling infrastructure — one-shot OSHA scrape is enough
- Full fine-tuning of the embedding or reranker models — use pretrained as-is
- Training YOLOv8 to convergence in this environment — pretrained/lightly fine-tuned only
