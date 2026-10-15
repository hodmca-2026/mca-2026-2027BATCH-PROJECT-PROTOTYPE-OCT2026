# 🤖 AI-Based Project Similarity Detection & Deep Learning Verification System

[![Python](https://img.shields.io/badge/Python-3.9+-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-2.x-000000?style=for-the-badge&logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![PyTorch](https://img.shields.io/badge/PyTorch-Deep%20Learning-EE4C2C?style=for-the-badge&logo=pytorch&logoColor=white)](https://pytorch.org/)
[![scikit-learn](https://img.shields.io/badge/scikit--learn-ML-F7931E?style=for-the-badge&logo=scikit-learn&logoColor=white)](https://scikit-learn.org/)
[![NLTK](https://img.shields.io/badge/NLTK-NLP-306998?style=for-the-badge)](https://www.nltk.org/)
[![SQLite](https://img.shields.io/badge/SQLite-Database-003B57?style=for-the-badge&logo=sqlite&logoColor=white)](https://www.sqlite.org/)

An intelligent web-based platform designed for academic institutions to eliminate duplicate and semantically similar project title submissions. Built using **Python, Flask, PyTorch Deep Learning, Machine Learning (TF-IDF & Semantic Embeddings), NLP (NLTK), Information Retrieval modules, SQLite, and a Modern Responsive UI**.

---

## 📌 Problem Statement

In universities and colleges, students frequently submit project titles and abstracts that are identical or cosmetically rephrased versions of previously submitted titles (e.g., *"AI Attendance System using Face Recognition"* vs. *"Face Recognition based Smart Attendance App"*).

Manual verification by faculty is time-consuming and error-prone. This system automates duplication detection using an **ensemble AI/ML, Semantic Transformer, and NLP similarity pipeline**, while providing faculty with **Deep Learning Verification** (Domain Classification, Novelty Scoring, and Named Entity Recognition).

---

## 🧠 AI/ML & NLP Similarity Pipeline

The system uses a multi-field, multi-stage Natural Language Processing and Machine Learning pipeline combining semantic embeddings and lexical metrics:

```
[Student Proposal: Title + Description]
                  │
                  ▼
   1. Text Normalization & Preprocessing (Lowercasing, Tokenization, Stemming)
                  │
                  ▼
   2. Multi-Method Hybrid Scoring
         ├── Semantic Similarity (all-MiniLM-L6-v2 embeddings)
         ├── TF-IDF Vector Space Cosine Similarity
         ├── Jaccard Token Overlap Similarity
         └── SequenceMatcher Fuzzy String Flow
                  │
                  ▼
   3. Calibrated Threshold Evaluation:
         ├── Exact Duplicate (100%)       ──► 🚫 REJECTED
         ├── High Similarity (>= 60%)     ──► 🚫 REJECTED (Returns matched title & score)
         └── Original Proposal (< 60%)    ──► ✅ ACCEPTED & SAVED
```

---

## 🔬 Deep Learning & Information Retrieval Modules

### Deep Learning Verification Engine (`dl_engine/`)
- **Unit IV (Domain Classifier):** Primary calibrated TF-IDF + Logistic Regression model backed by a PyTorch Bidirectional LSTM sequence classifier. Provides calibrated domain predictions (Healthcare, Education, Finance, Agriculture, Cybersecurity, Web Applications, etc.) with conservative uncertainty handling: returns *"Needs Faculty Review"* for ambiguous or out-of-domain proposals.
- **Unit V (Novelty / Anomaly Detection):** PyTorch Dense Autoencoder computing reconstruction Mean Squared Error (MSE) against historical project proposal distributions, generating calibrated novelty and typicality scores.
- **Unit VI (Neural Named Entity Recognition):** PyTorch BiLSTM neural token classifier coupled with a technical gazetteer for extracting programming languages, frameworks, AI/ML methods, and domains from student proposals.

### Information Retrieval Dashboard (`/ir`)
- **Ranked Search:** Search stored projects using TF-IDF vector space ranking.
- **Passage Retrieval:** Segment and rank arbitrary multi-paragraph technical texts against queries.
- **Content-Based Recommendation:** Recommends up to 3 similar approved projects for any input idea.
- **PageRank Analysis:** Computes graph centrality over proposal similarity networks.

---

## 🎯 Key Features

### 👨‍🎓 Student Dashboard (`/student`)
- **Roll Number Authentication**: Secure student sign-up and login using college Roll Number.
- **Real-Time Similarity Check**: AI checks proposed title and description against all existing submitted and approved titles.
- **Duplicate Prevention**: Rejects duplicate or semantically identical proposals and displays conflicting project details.
- **Faculty Warning Notifications**: Real-time alerts when faculty requests changes to a project proposal.
- **Proposal Revision**: Enables students to refine and update their proposal with automatic re-verification.

### 🎓 Faculty Dashboard (`/faculty`)
- **Live Analytics Overview**: Real-time metrics for Total Students, Submitted Projects, Approved Titles, and Warned Titles.
- **AI-Monitored Projects Table**: Displays all submitted titles with student names, roll numbers, and AI-computed similarity scores.
- **Deep Learning Review Modal**: Comprehensive modal inspecting calibrated domain classification, Autoencoder novelty scores, Neural NER extraction, and uncertainty flags.
- **Student Warning & Feedback**: Direct faculty feedback mechanism instructing students to modify scope or methodology.
- **One-Click Approval**: Faculty can approve titles meeting originality and academic standards.

---

## 🛠 Tech Stack

| Layer | Technology | Purpose |
|---|---|---|
| **Backend** | Python 3.9+, Flask | RESTful APIs, Session Management, Controller logic |
| **Deep Learning** | PyTorch (`torch`) | Bidirectional LSTM, Autoencoder, Neural NER models |
| **Machine Learning** | scikit-learn, NumPy | TF-IDF Vectorizers, Calibrated Logistic Regression, Cosine Metrics |
| **Semantic Embeddings** | Sentence-Transformers (`all-MiniLM-L6-v2`) | Deep sentence representations for semantic similarity |
| **NLP** | NLTK | Word Tokenization, Stopword Filtering, Porter Stemmer |
| **Database** | SQLite3 | Relational storage with foreign key constraints |
| **Frontend** | HTML5, Modern CSS3, JavaScript (Fetch API) | Clean, responsive UI with zero external bulky frameworks |

---

## 🚀 Setup & Installation

### 1. Clone or Open the Repository
```powershell
cd project-title-checker
```

### 2. Install Dependencies
```powershell
python -m pip install -r requirements.txt
```

### 3. Run the Application
```powershell
python app.py
```

### 4. Access the Web Application
Open your browser and navigate to:
```
http://localhost:3000
```

---

## 🔑 Demo & Testing Credentials

| Role | Roll No / ID | Password | Access URL |
|---|---|---|---|
| **Faculty** | `faculty` | `faculty123` | [http://localhost:3000/faculty](http://localhost:3000/faculty) |
| **Student** | Register any Roll No (e.g. `21CS001`) | Any password | [http://localhost:3000/student](http://localhost:3000/student) |
| **IR Dashboard** | Accessible via top navigation bar | Logged-in session | [http://localhost:3000/ir](http://localhost:3000/ir) |

---

## 🧪 Automated Testing & Model Training

### Run Test Suites
Run the complete automated test suite (including similarity, IR, and DL tests):
```powershell
python -m unittest discover tests
```

To run individual test modules:
```powershell
python -m unittest tests/test_ir.py
python -m unittest tests/test_dl.py
python -m unittest tests/test_similarity.py
```

### Deep Learning Retraining Scripts
To retrain Deep Learning models and update artifact weights:
```powershell
python -m dl_engine.training.train_lstm
python -m dl_engine.training.train_autoencoder
python -m dl_engine.training.train_ner
```
