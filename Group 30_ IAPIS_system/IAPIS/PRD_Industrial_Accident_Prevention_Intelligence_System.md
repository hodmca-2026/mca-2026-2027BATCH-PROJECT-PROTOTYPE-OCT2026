# PRD: Industrial Accident Prevention Intelligence System (IAPIS)

**SDGs Addressed:** SDG 8 (Decent Work & Economic Growth), SDG 9 (Industry, Innovation & Infrastructure)
**Type:** Academic Mini-Project — Deep Learning + Information Retrieval
**Design Principle:** Lightweight, free-tier only, runnable on a laptop / Google Colab / Kaggle Notebook

---

## 1. Problem Statement

Industrial sites generate large volumes of unstructured safety data — accident reports, near-miss logs, maintenance records, equipment/safety manuals, OSHA documents, and site photographs. Safety officers currently search this data manually, so recurring hazard patterns (e.g., motor overheating leading to fire) go unnoticed until an accident repeats.

**Goal:** Build a Retrieval-Augmented system that lets a safety officer ask a natural-language question (*"Have there been similar incidents involving overheating motors?"*) and receive:
1. Ranked, semantically similar historical incidents
2. Detected risk patterns across those incidents
3. A generated safety recommendation
4. (Optional/stretch) PPE / hazard detection from an uploaded photo

---

## 2. Why This Project Is a Good Fit (Course Alignment)

This project deliberately combines **two subjects** — Deep Learning (Units IV–VI) and Information Retrieval (Units IV–VI) — because a real retrieval-augmented safety system is inherently a hybrid of both. The table below is the mapping you'll want for your report/viva.

| Component in Architecture | Concept Used | Course & Unit |
|---|---|---|
| Cleaning & tokenizing accident reports, manuals, OSHA text | NLP preprocessing, multinomial distribution over words (bag-of-words / TF stats) | IR – Unit IV (Language Models for IR) |
| BM25 / language-model based first-pass retrieval over report corpus | Finite automata & language models, ranking with language models, divergence from randomness | IR – Unit IV |
| Dense embedding of reports (Sentence-Transformers) | Represents "passage retrieval and ranking" using a learned scoring function instead of pure statistics | IR – Unit IV |
| Vector DB similarity search (ChromaDB/FAISS) | Passage retrieval & ranking, cluster-based/distributed retrieval architecture (conceptually, since FAISS uses inverted-file clustering, same idea as cluster-based search engine architecture) | IR – Unit V (Web Retrieval) |
| Scraping public OSHA incident/safety pages to enrich the corpus | Web crawler structure, `scrapy` / `BeautifulSoup` | IR – Unit V |
| Weighting historical reports by how often similar incidents recur / how "authoritative" a manual is | Link-based ranking / PageRank idea repurposed as an "incident-recurrence rank" | IR – Unit V |
| Suggesting related manuals/checklists once an incident is retrieved | Content-based recommendation, knowledge-based recommendation | IR – Unit VI (IR Applications) |
| Pulling equipment names, failure modes, hazard types out of free-text reports | Named Entity Recognition, extracting data from text | IR – Unit VI / DL – Unit VI |
| Deep-learning **Cross-Encoder reranker** re-scoring the top-k retrieved reports | Sequence modeling over paired text (report + query) — the reranker itself is a small Transformer/RNN-family encoder | DL – Unit IV (RNN family, sequence learning problem) |
| Time-series sensor logs (motor temperature/vibration over time) fed to an LSTM to flag an *impending* overheating event before it becomes an incident | LSTM architecture, selective read/write/forget gates, vanishing/exploding gradient motivation | DL – Unit IV (RNN/LSTM) |
| Anomaly detection on numeric maintenance-log features (unusual sensor patterns = precursor to incident) | Autoencoder (deep autoencoder / denoising autoencoder), reconstruction-error based anomaly detection | DL – Unit V (Autoencoders) — directly matches the **"case study of autoencoders for anomaly detection in network traffic"**, here re-applied to *sensor/maintenance-log traffic* |
| Compressing incident-photo embeddings for efficient storage/search | Autoencoder application: image compression | DL – Unit V |
| PPE / missing-hazard-gear detection in uploaded worker photos | Object detection, image segmentation (project pipeline for computer vision) | DL – Unit VI (Applications of DL) |
| Auto-writing a one-paragraph incident caption from a photo (optional) | Image captioning case study | DL – Unit VI |
| Final "you may also want to review manual X" suggestion box | Recommender systems case study | DL – Unit VI |

This gives you a clean answer to "which concept came from which chapter" for both subjects — 6 units total contributing, roughly evenly.

---

## 3. System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│  DATA SOURCES                                                        │
│  Accident reports · Near-miss reports · Maintenance logs ·           │
│  Safety/Equipment manuals · OSHA docs (scraped) · Incident photos    │
└───────────────────────────────┬───────────────────────────────────--┘
                                 ▼
                 ┌───────────────────────────────┐
                 │  1. INGESTION & NLP PREPROCESS │  (IR Unit IV)
                 │  clean, tokenize, chunk text,  │
                 │  NER for equipment/hazard tags │  (IR Unit VI)
                 └───────────────┬───────────────┘
                                 ▼
              ┌────────────────────────────────────┐
              │ 2. EMBEDDING MODEL                  │
              │ Sentence-Transformers (MiniLM)      │  (IR Unit IV)
              └───────────────┬────────────────────┘
                               ▼
              ┌────────────────────────────────────┐
              │ 3. VECTOR DATABASE (ChromaDB/FAISS) │  (IR Unit V)
              └───────────────┬────────────────────┘
                               ▼
        ┌───────────────────────────────────────────────┐
        │ 4. SEMANTIC RETRIEVAL (hybrid: BM25 + dense)   │  (IR Unit IV/V)
        └───────────────────────┬───────────────────────┘
                                 ▼
        ┌───────────────────────────────────────────────┐
        │ 5. DEEP LEARNING RERANKER (Cross-Encoder)      │  (DL Unit IV)
        └───────────────────────┬───────────────────────┘
                                 ▼
   ┌───────────────────────────────────────────────────────────┐
   │ 6. RISK PATTERN DETECTION                                  │
   │   a) LSTM on time-series sensor logs -> predicts drift      │ (DL Unit IV)
   │   b) Autoencoder on numeric log features -> anomaly score   │ (DL Unit V)
   │   c) Recurrence ranking across retrieved incidents          │ (IR Unit V)
   └───────────────────────────┬───────────────────────────────┘
                                 ▼
        ┌───────────────────────────────────────────────┐
        │ 7. SAFETY RECOMMENDATION GENERATION (LLM)       │  (IR Unit VI –
        │    grounded on retrieved + reranked evidence     │   recommendation)
        └───────────────────────┬───────────────────────┘
                                 ▼
                        Answer + Sources + Risk Report
                                 ▲
                                 │ (parallel, optional branch)
        ┌───────────────────────────────────────────────┐
        │ CV BRANCH: Photo → YOLOv8 PPE/hazard detector  │  (DL Unit VI)
        │ → structured findings merged into recommendation│
        └───────────────────────────────────────────────┘
```

### Why "hybrid" retrieval (BM25 + dense) instead of only vector search?
This is the direct implementation of **IR Unit IV's "ranking with language models" vs "divergence from randomness"** contrast — BM25 represents the classical probabilistic/statistical LM approach, dense embeddings represent the learned neural approach. Combining both is a standard, low-cost way to boost retrieval quality and gives you material to discuss both paradigms in your report.

---

## 4. Lightweight Tech Stack (100% Free / Free-Tier)

| Layer | Tool | Why it's free & lightweight |
|---|---|---|
| Embeddings | `sentence-transformers/all-MiniLM-L6-v2` (HuggingFace) | Open-source, runs on CPU, ~80MB model |
| Reranker | `cross-encoder/ms-marco-MiniLM-L-6-v2` (HuggingFace) | Free, CPU-friendly, small |
| Sparse retrieval | `rank_bm25` (Python pkg) | Pure Python, no server needed |
| Vector DB | **ChromaDB** (local, embedded, no server) or FAISS (`faiss-cpu`) | Free, open-source, file-based |
| NER | `spaCy` (`en_core_web_sm`) | Free, local, lightweight |
| LSTM / Autoencoder | PyTorch or TensorFlow/Keras (small custom models) | Free, train on CPU for a small demo dataset |
| Object detection (PPE) | **Ultralytics YOLOv8n** (nano) pretrained + optional fine-tune on a free Roboflow Universe "PPE detection" dataset | Free model + free public dataset |
| LLM for final answer generation | **Groq API** (free tier, e.g., Llama-3.1-8B-Instant) *or* **Google Gemini API free tier** *or* **HuggingFace Inference API free tier** | Free API keys, generous free quota |
| Web crawling (optional, to enrich corpus with public OSHA data) | `requests` + `BeautifulSoup4`, or `Scrapy` | Free Python libs |
| Backend | FastAPI (Python) | Free, lightweight |
| Frontend | Streamlit | Free, fastest way to build a demo UI |
| Hosting/dev | Google Colab (free GPU) for training the LSTM/Autoencoder; Streamlit Community Cloud or local for the demo app | Free |

### Free API Keys You'll Need
1. **Groq API** — https://console.groq.com — free tier, very fast inference, good for the final "Safety Recommendation" generation step.
2. **Google Gemini API** — https://ai.google.dev — free tier, alternative/backup LLM.
3. **HuggingFace** — https://huggingface.co/settings/tokens — free token, needed only if you use Inference API instead of running models locally (running locally avoids needing this).
4. **Roboflow** — https://roboflow.com — free account to download a public PPE-detection dataset (search "PPE detection" or "hard hat detection" in Roboflow Universe) for the optional CV branch.
5. **OSHA public data** — https://www.osha.gov/severe-injury-reports (open, scrapeable, no API key needed) — real accident data to seed your corpus if you don't want to hand-write sample reports.

No paid service is required anywhere in this pipeline.

---

## 5. Functional Requirements

| ID | Requirement |
|---|---|
| FR1 | User can type a natural-language query (e.g., "motor overheating incidents") and get top-N ranked historical reports |
| FR2 | System reranks the top-N results with a cross-encoder for higher precision |
| FR3 | System detects recurring risk patterns (same equipment/hazard type appearing across multiple incidents) and displays a pattern summary |
| FR4 | System generates a grounded safety recommendation citing which reports it used |
| FR5 | System predicts abnormal sensor drift (e.g., temperature trending up) using an LSTM on maintenance/sensor time-series, and flags "at risk" equipment |
| FR6 | System scores maintenance-log feature vectors with an autoencoder reconstruction error to flag anomalous logs |
| FR7 (stretch) | User can upload a worksite photo; system detects missing PPE / hazardous conditions using YOLOv8 |
| FR8 (stretch) | System recommends related manuals/checklists based on retrieved incident's equipment tags |

## 6. Non-Functional Requirements
- Runs fully on a laptop with 8GB RAM / free Colab; no paid GPU needed.
- Query response time < 5 seconds for retrieval + rerank (CPU).
- All models under ~500MB combined (embedding + reranker + YOLOv8n).
- No user data leaves the machine except the final LLM call (which only sends retrieved text + query, not raw files).

---

## 7. Minimal Dataset Plan (keep it lightweight)

You do **not** need thousands of real reports. For an academic demo:
- 40–80 synthetic/handwritten incident & near-miss reports (mix of equipment types: motors, conveyors, forklifts, electrical panels) — can be generated quickly with an LLM and lightly edited for realism.
- 10–15 real OSHA severe-injury summaries scraped from the public OSHA site (no key needed) to ground the demo in real data.
- 1 small synthetic time-series CSV (temperature/vibration per motor per hour, ~30 days, a few motors) with a few injected "drift" events, for the LSTM.
- Same tabular data reused/reshaped as feature vectors for the autoencoder anomaly detector.
- (Stretch) ~100–200 images from a Roboflow PPE dataset if you attempt the CV branch — you do not need to train from scratch; fine-tuning YOLOv8n for a few epochs on Colab is enough for a demo.

---

## 8. Implementation Plan (6–7 Weeks, matches a 7-hour/unit course pace)

**Week 1 — Data & Preprocessing**
- Collect/write incident reports; scrape a handful of OSHA summaries.
- Build NLP cleaning pipeline (tokenize, remove boilerplate) + spaCy NER for equipment/hazard extraction.
- *Deliverable:* clean JSON corpus of reports with extracted entities.

**Week 2 — Retrieval Core**
- Generate embeddings with `all-MiniLM-L6-v2`; store in ChromaDB.
- Implement BM25 with `rank_bm25` over the same corpus.
- Combine both into a simple hybrid score (weighted sum or reciprocal rank fusion).
- *Deliverable:* `search(query) -> top-k reports` working end-to-end.

**Week 3 — Reranker + Recommendation**
- Add cross-encoder reranker on top-k results.
- Wire up Groq/Gemini API to generate the final grounded recommendation from reranked reports.
- *Deliverable:* full text-in, text-out RAG pipeline.

**Week 4 — Risk Pattern Detection (DL Unit IV: LSTM)**
- Build small LSTM in PyTorch/Keras on synthetic motor sensor time-series.
- Train to predict next-step temperature / flag drift beyond threshold.
- *Deliverable:* "equipment X is trending toward overheating" alert module.

**Week 5 — Anomaly Detection (DL Unit V: Autoencoder)**
- Build a small dense/denoising autoencoder on maintenance-log numeric features.
- Use reconstruction error as anomaly score; flag top anomalous logs.
- *Deliverable:* anomaly score integrated into the "risk pattern" output.

**Week 6 — Recurrence/Link-based Ranking + UI**
- Add a simple "recurrence rank" (how often similar incidents show up across the corpus — conceptually like PageRank's link-count idea, here a co-occurrence count).
- Build Streamlit UI: query box, ranked results, pattern summary, recommendation panel.
- *Deliverable:* usable demo app.

**Week 7 (stretch) — Computer Vision Branch + Polish**
- Load pretrained YOLOv8n, optionally fine-tune briefly on Roboflow PPE dataset.
- Add photo upload -> detection -> merge findings into recommendation panel.
- Final testing, report writing, prepare the concept-to-chapter mapping table (Section 2 above) for viva.

---

## 9. Evaluation Plan (keep simple)
- **Retrieval quality:** manually label 10–15 test queries with "correct" relevant reports; measure Precision@5 before vs after reranking.
- **LSTM:** simple RMSE on held-out sensor time-series + qualitative check that injected drift events are flagged.
- **Autoencoder:** check reconstruction-error separates injected anomalous logs from normal ones (simple threshold + confusion matrix).
- **CV branch (if built):** mAP on Roboflow validation split (Ultralytics reports this automatically).
- **End-to-end demo:** a handful of qualitative example queries with screenshots for the report.

---

## 10. Risks & Mitigations
| Risk | Mitigation |
|---|---|
| Not enough real accident data | Use synthetic LLM-generated reports + real OSHA summaries as ground truth mix |
| LLM API rate limits during demo/viva | Cache responses for the demo queries; have Gemini as backup if Groq is rate-limited |
| CV branch scope creep | Keep it optional/stretch; a pretrained YOLOv8n with zero fine-tuning is already demonstrable |
| Overfitting small LSTM/autoencoder on tiny synthetic data | Fine — the point for this course project is demonstrating the *architecture and concept*, not production accuracy; state this clearly in the report |

---

## 11. Suggested Repo Structure
```
iapis/
├── data/
│   ├── reports/            # incident/near-miss text files (json)
│   ├── sensor_logs.csv     # synthetic time-series for LSTM
│   └── maintenance_logs.csv# numeric features for autoencoder
├── ingestion/
│   ├── preprocess.py       # NLP cleaning + NER
│   └── scrape_osha.py      # optional web crawler
├── retrieval/
│   ├── embed_store.py      # ChromaDB + sentence-transformers
│   ├── bm25_search.py
│   └── reranker.py         # cross-encoder
├── risk_models/
│   ├── lstm_drift.py       # DL Unit IV
│   └── autoencoder_anomaly.py # DL Unit V
├── cv_branch/
│   └── ppe_detect.py       # YOLOv8, DL Unit VI (optional)
├── recommend.py            # LLM call, grounded generation
├── app.py                  # Streamlit UI
└── README.md
```

---

## 12. One-Line Pitch (for slide/report cover)
*"A hybrid retrieval-augmented safety intelligence system that combines classical and neural Information Retrieval with RNN/LSTM sequence models and Autoencoder anomaly detection to catch recurring industrial hazards before they become accidents — built entirely on free, lightweight, open-source tools."*
