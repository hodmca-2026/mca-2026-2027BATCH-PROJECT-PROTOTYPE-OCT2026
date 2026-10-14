# IAPIS — Industrial Accident Prevention Intelligence System

**SDGs Addressed:** SDG 8 (Decent Work & Economic Growth), SDG 9 (Industry, Innovation & Infrastructure)

A hybrid Retrieval-Augmented Generation (RAG) safety intelligence system that combines classical and neural Information Retrieval with RNN/LSTM sequence models and Autoencoder anomaly detection to catch recurring industrial hazards before they become accidents — built entirely on free, lightweight, open-source tools.

---

## Quick Start

### 1. Prerequisites
- Python 3.10+
- 8 GB RAM minimum

### 2. Setup
```bash
# Create virtual environment
python -m venv .venv

# Activate (Windows)
.venv\Scripts\activate

# Activate (Linux/macOS)
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Download spaCy model
python -m spacy download en_core_web_sm
```

### 3. API Keys
Copy `.env.example` to `.env` and fill in your keys:
```bash
cp .env.example .env
```
- **Groq API** — https://console.groq.com (free tier)
- **Gemini API** — https://ai.google.dev (free tier)

> **Note:** The system works without API keys — recommendation generation gracefully falls back to a deterministic template.

### 4. Generate Synthetic Data
```bash
python -m scripts.generate_synthetic_reports
python -m scripts.generate_synthetic_sensor_data
python -m scripts.scrape_osha
```

### 5. Run the Backend & Web Dashboard (FastAPI)
```bash
uvicorn api.main:app --reload --port 8000
```
- **Web Dashboard:** Open [http://localhost:8000](http://localhost:8000) in your browser.
- **Interactive Swagger Docs:** [http://localhost:8000/docs](http://localhost:8000/docs)

### 6. Run the Streamlit Frontend (Alternative UI)
In a separate terminal:
```bash
streamlit run app.py
```
- **Streamlit App:** Open [http://localhost:8501](http://localhost:8501) in your browser.

---

## Architecture

```
DATA SOURCES → INGESTION & NLP → EMBEDDING → VECTOR DB → HYBRID RETRIEVAL
  → CROSS-ENCODER RERANKER → RISK PATTERN DETECTION → RECOMMENDATION → UI

Parallel branch: Photo → YOLOv8 PPE Detection → Merged into recommendations
```

### Components
| Component | Tech | Course Mapping |
|---|---|---|
| Text preprocessing & NER | spaCy `en_core_web_sm` | IR Unit IV, VI |
| Dense embeddings | `all-MiniLM-L6-v2` | IR Unit IV |
| Sparse retrieval | BM25 (`rank_bm25`) | IR Unit IV |
| Vector DB | ChromaDB (local) | IR Unit V |
| Hybrid search | Reciprocal Rank Fusion | IR Unit IV/V |
| Cross-encoder reranker | `ms-marco-MiniLM-L-6-v2` | DL Unit IV |
| LSTM sensor drift | Custom PyTorch LSTM | DL Unit IV |
| Autoencoder anomaly | Custom PyTorch Autoencoder | DL Unit V |
| Recurrence ranking | Co-occurrence scoring | IR Unit V |
| Recommendation | Groq/Gemini LLM (free tier) | IR Unit VI |
| PPE detection | YOLOv8n (Ultralytics) | DL Unit VI |
| Backend | FastAPI | — |
| Frontend | Streamlit | — |

---

## Concept-to-Chapter Mapping

| Component | Concept | Course & Unit |
|---|---|---|
| Cleaning & tokenizing reports | NLP preprocessing, bag-of-words / TF stats | IR – Unit IV |
| BM25 retrieval | Language models, ranking with language models | IR – Unit IV |
| Dense embedding (Sentence-Transformers) | Passage retrieval & ranking (neural) | IR – Unit IV |
| Vector DB search (ChromaDB) | Cluster-based retrieval architecture | IR – Unit V |
| OSHA web scraping | Web crawler structure | IR – Unit V |
| Recurrence ranking | Link-based ranking / PageRank analogue | IR – Unit V |
| Manual/checklist recommendation | Content-based recommendation | IR – Unit VI |
| NER for equipment/hazard extraction | Named Entity Recognition | IR – Unit VI / DL – Unit VI |
| Cross-Encoder reranker | Sequence modeling (Transformer encoder) | DL – Unit IV |
| LSTM sensor drift prediction | LSTM architecture, selective gates | DL – Unit IV |
| Autoencoder anomaly detection | Deep autoencoder, reconstruction-error anomaly | DL – Unit V |
| YOLOv8 PPE detection | Object detection, image segmentation | DL – Unit VI |

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/health` | Health check |
| `POST` | `/search` | Hybrid search + rerank |
| `POST` | `/analyze` | Full analysis pipeline (search + risk flags + recommendation) |
| `POST` | `/detect-ppe` | PPE detection from uploaded image |

---

## Project Structure
```
iapis/
├── .env.example
├── requirements.txt
├── README.md
├── CHANGELOG.md
├── data/
│   ├── raw/osha_scraped.json
│   ├── reports/reports.json
│   ├── sensor_logs.csv
│   └── maintenance_logs.csv
├── scripts/
│   ├── generate_synthetic_reports.py
│   ├── generate_synthetic_sensor_data.py
│   └── scrape_osha.py
├── ingestion/
│   ├── schema.py
│   ├── preprocess.py
│   └── ner_extract.py
├── retrieval/
│   ├── embed_store.py
│   ├── bm25_search.py
│   ├── hybrid_search.py
│   └── reranker.py
├── risk_models/
│   ├── lstm_drift.py
│   ├── autoencoder_anomaly.py
│   └── recurrence_rank.py
├── recommend/
│   ├── llm_client.py
│   └── prompt_templates.py
├── cv_branch/
│   └── ppe_detect.py
├── api/
│   ├── main.py
│   └── models.py
├── app.py
├── tests/
│   ├── test_ingestion.py
│   ├── test_retrieval.py
│   ├── test_risk_models.py
│   └── test_api.py
└── models_store/
```

---

## Regenerating Data
```bash
python -m scripts.generate_synthetic_reports
python -m scripts.generate_synthetic_sensor_data
python -m scripts.scrape_osha   # optional; requires internet
```

---

## Running Tests
```bash
pytest
```

---

## License
Academic project — not for production use.
