# HR Insight AI — Employee Attrition & Performance Decision Support

> **An end-to-end machine learning platform that predicts employee attrition risk,
> forecasts performance ratings, and surfaces HR knowledge — built for
> HR managers, people-analytics teams, and workforce planners.**

---

## 📋 Table of Contents

- [Overview](#-overview)
- [Features](#-features)
- [Architecture](#-architecture)
- [Tech Stack](#-tech-stack)
- [Quick Start](#-quick-start)
- [Project Structure](#-project-structure)
- [ML Pipeline](#-ml-pipeline)
- [API Reference](#-api-reference)
- [Configuration](#-configuration)
- [Testing](#-testing)
- [Deployment](#-deployment)
- [Model Performance](#-model-performance)
- [Contributing](#-contributing)

---

## 🔍 Overview

HR Insight AI is a **production-grade people-analytics platform** that combines
deep learning, classical ML, and information retrieval to give HR teams
an AI-powered lens on workforce health.

Key capabilities:

| Capability                  | Detail                                                         |
| --------------------------- | -------------------------------------------------------------- |
| **Attrition prediction**    | Probability a given employee will leave within 12 months       |
| **Performance forecasting** | Predicted performance rating (1–5 scale)                       |
| **SHAP explanations**       | Which features drove each individual prediction                |
| **Risk simulation**         | What-if sliders to model intervention scenarios                |
| **HR knowledge search**     | BM25 + TF-IDF + language-model search over HR policy documents |
| **Batch prediction**        | Score up to 100 employees in a single API call                 |
| **Workforce dashboard**     | Live KPIs, risk distribution, department heatmaps              |

---

## ✨ Features

### Machine Learning

- **3-model ensemble** per task: Deep Neural Network · Random Forest · Logistic Regression
- **Imbalanced-class handling** via class-weighting and threshold optimisation
- **SHAP (SHapley Additive exPlanations)** for individual and global feature importance
- **Optimised attrition threshold** (F1-maximising, tuned on hold-out set)

### Information Retrieval

- **BM25** — probabilistic lexical ranking
- **TF-IDF** — inverted-index cosine similarity
- **Language Model** — query-likelihood smoothed retrieval
- **SVM HR Document Classifier** — auto-categorises uploaded HR docs

### API & Web

- RESTful Flask API (`/api/v*` versioned namespace)
- Input validation layer with field-range and logical-consistency checks
- Batch prediction endpoint (up to 100 employees/request)
- Structured JSON logging to rotating log files

### Operations

- `Dockerfile` — multi-stage, non-root user, Gunicorn production server
- GitHub Actions CI — lint → unit tests → Docker build
- `.env`-based configuration for all environments
- `requirements.txt` + `requirements-dev.txt`

---

## 🏗 Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Web Browser                              │
│   Dashboard │ Prediction Lab │ Simulator │ Roster │ Knowledge   │
└──────────────────────────┬──────────────────────────────────────┘
                           │ HTTP / JSON
┌──────────────────────────▼──────────────────────────────────────┐
│                    Flask REST API  (app.py)                      │
│  /api/health  /api/predict  /api/predict/batch  /api/employees  │
│  /api/dashboard  /api/shap-explain  /api/search  /api/simulate  │
└────────────┬────────────────────────────┬───────────────────────┘
             │                            │
┌────────────▼──────────┐    ┌────────────▼──────────────────────┐
│   Prediction Service   │    │        IR Search Engine           │
│  prediction_service.py │    │  bm25_search.py                   │
│  ┌──────────────────┐  │    │  ir_search_service.py (TF-IDF)    │
│  │ Attrition DNN    │  │    │  language_model_search.py         │
│  │ Performance DNN  │  │    └───────────────────────────────────┘
│  │ SHAP Explainer   │  │
│  └──────────────────┘  │
└────────────────────────┘
             │
┌────────────▼──────────────────────────────────────────────────┐
│                   Trained Artifacts                            │
│  models/  *.keras  *.pkl   artifacts/ *.pkl   results/ *.csv  │
└───────────────────────────────────────────────────────────────┘
```

---

<<<<<<< HEAD

## 🛠 Tech Stack

| Layer                  | Technology                         |
| ---------------------- | ---------------------------------- |
| **Web framework**      | Flask 3.x                          |
| **ML / DL**            | TensorFlow 2.21 · scikit-learn 1.9 |
| **Explainability**     | SHAP 0.52                          |
| **Data**               | pandas 3 · NumPy 2.5               |
| **Serialisation**      | joblib                             |
| **Visualisation (UI)** | Chart.js                           |
| **Icons**              | Lucide                             |
| **Production server**  | Gunicorn                           |
| **Container**          | Docker (multi-stage)               |
| **CI/CD**              | GitHub Actions                     |
| **Testing**            | pytest · pytest-cov                |

---

## 🚀 Quick Start

### 1. Clone & Install

```bash
git clone https://github.com/your-org/hr-insight-ai.git
cd hr-insight-ai

# Create a virtual environment
python -m venv .venv
.\.venv\Scripts\activate      # Windows
# source .venv/bin/activate    # macOS / Linux

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Environment

```bash
cp .env.example .env
# Edit .env and set SECRET_KEY (required for production)
```

### 3. Train Models (or use pre-trained)

```bash
# Preprocess data
python preprocess_attrition.py
python preprocess_performance.py

# Train models
python train_attrition.py
python train_performance.py

# Build IR index
python build_inverted_index.py
```

### 4. Run the Application

```bash
python app.py
```

Open **http://localhost:5000** in your browser.

---

### Docker (Recommended for Production)

````bash
# Build image
docker build -t hr-attrition-ai .

# Run with environment file
docker run --env-file .env -p 5000:5000 hr-attrition-ai
=======
### 2. Performance Prediction

Predicts employee performance across four ratings:

```text
2
3
4
5
````

The performance model uses a Deep Neural Network with dense layers, batch normalization, dropout, and softmax output.

The system returns:

- Predicted performance rating
- Performance label
- Confidence
- Class probabilities

---

### 3. SHAP Explainability

The system provides employee-level explanations using SHAP KernelExplainer.

The explanation identifies features that contributed to the model's predicted attrition risk.

Example output fields:

```text
Feature
Impact
Importance
Direction
```

> SHAP contributions explain model behavior and should not be interpreted as causal evidence.

---

### 4. HR Recommendation Engine

The system generates HR-focused recommendations using employee attributes and prediction results.

The recommendation workflow can consider:

- Attrition risk
- Burnout
- Engagement
- Manager support
- Overtime
- Work-life balance
- Years since promotion
- Training
- Performance
- Perceived AI job risk

The generated actions are intended to support HR review and intervention planning.

---

### 5. HR Knowledge Search

The HR Knowledge module is an Information Retrieval system for searching the internal HR document collection.

Current retrieval methods:

```text
BM25
TF-IDF
Language Model
```

The knowledge base contains 20 HR documents covering:

- Leave
- Performance
- Benefits
- Training
- Compensation

Search results include:

- Document name
- Document ID
- Relevance score
- Matched terms
- View Document action

The **View Document** feature opens the actual retrieved HR policy/document so HR can read the source content.

---

### 6. HR Action Center

The HR Action Center generates an employee-specific HR retrieval query from the employee's model assessment and workplace factors.

The query is searched using:

```text
BM25
TF-IDF
Language Model
```

The retrieved results are combined into policy evidence that can support an employee-level HR assessment.

---

### 7. Risk Simulator

The Risk Simulator allows HR users to change selected employee factors and compare the current prediction with a simulated scenario.

Simulation factors include:

- Burnout
- Engagement
- Manager support
- Work-life balance
- Overtime
- Training
- Salary hike
- Years since promotion

The simulator compares:

```text
Current State
      vs
Simulated State
```

and reports:

- Attrition probability
- Risk level
- Performance rating
- Performance confidence
- Risk change
- Performance change
- Recommendations

Scenario history is stored locally in the browser.

---

### 8. Model Evidence

The Model Evidence page presents recorded evaluation evidence for the tested attrition and performance models.

It includes:

- Model comparison
- Confusion matrices
- DNN architecture
- Evaluation notes
- Global SHAP feature importance when a saved artifact is available

#### Recorded Attrition Evaluation

| Model               | Accuracy | Precision | Recall |     F1 | ROC-AUC |
| ------------------- | -------: | --------: | -----: | -----: | ------: |
| Logistic Regression |   0.7260 |    0.3631 | 0.7039 | 0.4791 |  0.8071 |
| Random Forest       |   0.8240 |    0.5118 | 0.3631 | 0.4248 |  0.7925 |
| Deep Neural Network |   0.6730 |    0.3263 | 0.7765 | 0.4595 |  0.7890 |

#### Recorded Performance Evaluation

| Model               | Accuracy | Macro Precision | Macro Recall | Macro F1 | Weighted F1 |
| ------------------- | -------: | --------------: | -----------: | -------: | ----------: |
| Deep Neural Network |   0.4200 |          0.3281 |       0.3842 |   0.3275 |      0.4392 |
| Logistic Regression |   0.3620 |          0.3529 |       0.4904 |   0.3163 |      0.4026 |
| Random Forest       |   0.5530 |          0.3039 |       0.3076 |   0.2958 |      0.5270 |

These values are the recorded test-set evaluation results from the project's model training/evaluation workflow.

---

# System Architecture

```text
                    HR INTELLIGENCE PLATFORM
                             │
              ┌──────────────┴──────────────┐
              │                             │
        Employee Data                  HR Documents
              │                             │
              ▼                             ▼
       Prediction Engine              IR Engine
              │                     ┌───────┼───────┐
              ▼                     │       │       │
       Attrition Risk              TF-IDF  BM25   LM
       Performance                    │       │       │
              │                       └───────┼───────┘
              ▼                               │
        SHAP Explanation                      │
              │                               │
              └──────────────┬────────────────┘
                             ▼
                    HR Decision Support
                             │
                             ▼
                    Recommended Actions
                             │
                             ▼
                     Relevant HR Policies
>>>>>>> origin/main
```

---

<<<<<<< HEAD

## 📁 Project Structure

````
hr-insight-ai/
├── app.py                        # Flask application & REST API
├── config.py                     # Centralised configuration
├── logger.py                     # Structured logging
├── validator.py                  # Input validation layer
├── prediction_service.py         # Attrition + performance inference
├── bm25_search.py                # BM25 retrieval
├── ir_search_service.py          # TF-IDF retrieval
├── language_model_search.py      # LM retrieval
├── hr_recommendation.py          # Content-based HR recommendations
│
├── preprocess_attrition.py       # Attrition preprocessing pipeline
├── preprocess_performance.py     # Performance preprocessing pipeline
├── train_attrition.py            # Attrition model training
├── train_performance.py          # Performance model training
├── train_hr_classifier.py        # HR document SVM classifier
├── explain_attrition.py          # SHAP analysis
├── optimize_attrition_threshold.py
│
├── data/
│   └── employee_attrition_hr_2026.csv   # 5,000 employee records
│
├── models/                        # Trained model files (*.keras, *.pkl)
├── artifacts/                     # Preprocessors, feature names
├── processed_data/                # Train/test numpy arrays
├── results/                       # Metrics, confusion matrices, SHAP CSVs
├── ir_artifacts/                  # BM25/TF-IDF index files
├── hr_documents/                  # Raw HR policy documents
├── extracted_documents/           # Parsed document text
│
├── templates/                     # Jinja2 HTML templates
│   ├── base.html
│   ├── dashboard.html
│   ├── prediction.html
│   ├── simulator.html
│   ├── employees.html
│   ├── knowledge_search.html
│   └── model_evidence.html
│
├── static/
│   ├── css/style.css
│   └── js/
│       ├── dashboard.js
│       ├── prediction.js
│       ├── risk_simulator.js
│       ├── employees.js
│       ├── knowledge_search.js
│       └── model_evidence.js
│
├── tests/
│   ├── test_config.py
│   └── test_validator.py
│
├── logs/                          # Rotating application logs
├── .github/workflows/ci.yml      # GitHub Actions CI pipeline
├── Dockerfile                     # Multi-stage production image
├── requirements.txt
├── requirements-dev.txt
└── .env.example
=======
# Information Retrieval Workflow

```text
HR Query
   ↓
Text Preprocessing
   ↓
BM25 / TF-IDF / Language Model
   ↓
Ranked HR Documents
   ↓
Relevance Score + Matched Terms
   ↓
View Actual HR Document
````

---

# Dataset

The project uses the employee dataset:

```text
data/employee_attrition_hr_2026.csv
```

Dataset characteristics used by the project:

- 5,000 employee records
- 29 columns
- Unique employee IDs
- Attrition target: Yes / No
- Performance ratings: 2, 3, 4, 5
- No missing values in the prepared dataset
- Employee ID is excluded from predictive features

---

# Information Retrieval Collection

The HR knowledge base contains 20 internal HR documents across:

```text
hr_documents/
├── leave/
├── performance/
├── benefits/
├── training/
└── compensation/
```

Examples include:

```text
annual_leave.txt
performance_review.txt
promotion_guidelines.txt
overtime_policy.txt
technical_training.txt
employee_benefits.txt
salary_policy.txt
bonus_policy.txt
```

The indexed collection contains:

```text
20 documents
234 unique terms
597 indexed postings
```

---

# Technology Stack

## Backend

- Python
- Flask
- Pandas
- NumPy
- Scikit-learn
- TensorFlow
- SHAP
- Joblib

## Frontend

- HTML5
- CSS3
- JavaScript
- Chart.js
- Lucide Icons

## Information Retrieval

- Inverted Index
- BM25
- TF-IDF
- Language Model
- Jelinek-Mercer smoothing

## Machine Learning

- Logistic Regression
- Random Forest
- Deep Neural Network

---

# Project Structure

```text
employee-attrition-performance-ai/
│
├── app.py
├── prediction_service.py
│
├── bm25_search.py
├── ir_search_service.py
├── language_model_search.py
├── search_hr_documents.py
│
├── add_hr_documents.py
├── ingest_hr_documents.py
├── build_inverted_index.py
│
├── preprocess.py
├── preprocess_attrition.py
├── preprocess_performance.py
│
├── train_attrition.py
├── train_performance.py
├── train_hr_classifier.py
│
├── explain_attrition.py
├── explain_performance.py
├── optimize_attrition_threshold.py
├── hr_recommendation.py
├── eda.py
│
├── data/
├── artifacts/
├── models/
├── processed_data/
├── ir_artifacts/
├── extracted_documents/
├── hr_documents/
├── results/
│
├── static/
│   ├── css/
│   └── js/
│
├── templates/
│   ├── base.html
│   ├── dashboard.html
│   ├── prediction.html
│   ├── employees.html
│   ├── knowledge_search.html
│   ├── simulator.html
│   └── model_evidence.html
│
├── .gitignore
├── requirements.txt
└── README.md
>>>>>>> origin/main
```

---

<<<<<<< HEAD

## 🧪 ML Pipeline

### Dataset

- **5,000 employee records** · 29 features · 17.9 % attrition rate
- Features: demographics, compensation, engagement scores, AI-adoption metrics

### Feature Engineering

- Categorical → OneHotEncoder (handle_unknown="ignore")
- Numerical → StandardScaler + median imputation
- Class imbalance → computed class weights (`sklearn.utils.class_weight`)

### Models

| Task        | Model                                   | Notes                   |
| ----------- | --------------------------------------- | ----------------------- |
| Attrition   | **DNN** (128→64→32, Dropout, BatchNorm) | Primary model           |
| Attrition   | Random Forest (300 trees)               | Ensemble comparison     |
| Attrition   | Logistic Regression                     | Interpretable baseline  |
| Performance | **DNN** (multi-class softmax)           | Rating 1–5              |
| Performance | Random Forest                           | Ensemble comparison     |
| HR Docs     | SVM + TF-IDF                            | Document classification |

### Explainability

SHAP DeepExplainer used to produce per-employee feature contribution
waterfall charts, both in the web UI and as CSV exports.

---

## 📡 API Reference

### `GET /api/health`

System health check.

```json
{
  "status": "ok",
  "version": "2.0.0",
  "env": "development",
  "timestamp": "2026-10-01T14:00:00Z"
}
```

---

### `POST /api/predict`

Single-employee prediction.

**Request body:**

```json
{
  "age": 30,
  "gender": "Male",
  "department": "Engineering",
  "job_role": "Software Engineer",
  "monthly_income": 75000,
  "burnout_score": 7,
  "engagement_score": 5,
  "performance_rating": 3,
  ...
}
```

**Response:**

```json
{
  "success": true,
  "attrition": {
    "probability": 0.68,
    "risk_level": "HIGH",
    "percentage": "68.0%"
  },
  "performance": {
    "predicted_rating": 3,
    "label": "Meets Expectations",
    "confidence": 0.71
  },
  "top_risk_factors": ["burnout_score", "overtime_hours_per_week", ...]
}
```

---

### `POST /api/predict/batch`

Batch prediction for up to 100 employees.

**Request body:**

```json
{
  "employees": [ { "age": 30, ... }, { "age": 45, ... } ]
}
```

**Response:**

```json
{
  "success": true,
  "requested": 2,
  "processed": 2,
  "failed": 0,
  "results": [...],
  "summary": {
    "high_risk": 1,
    "medium_risk": 1,
    "low_risk": 0
  },
  "generated_at": "2026-10-01T14:00:00Z"
}
```

---

### Validation Error (HTTP 422)

```json
{
  "success": false,
  "error": "Validation failed",
  "details": ["Field 'age' = 200 is outside the expected range [18.0, 80.0]."],
  "warnings": []
}
```

---

## ⚙️ Configuration

All settings are controlled via environment variables (see `.env.example`):

| Variable                     | Default       | Description          |
| ---------------------------- | ------------- | -------------------- |
| `SECRET_KEY`                 | (required)    | Flask session secret |
| `FLASK_HOST`                 | `0.0.0.0`     | Bind address         |
| `FLASK_PORT`                 | `5000`        | Port                 |
| `FLASK_DEBUG`                | `false`       | Enable debug mode    |
| `APP_ENV`                    | `development` | Environment label    |
| `LOG_LEVEL`                  | `INFO`        | Logging verbosity    |
| `ATTRITION_HIGH_THRESHOLD`   | `0.64`        | High-risk cutoff     |
| `ATTRITION_MEDIUM_THRESHOLD` | `0.40`        | Medium-risk cutoff   |

---

## 🧪 Testing

```bash
# Install dev dependencies
pip install -r requirements-dev.txt

# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ -v --cov=. --cov-omit="tests/*" --cov-report=term-missing
```

Current test suite: **28 tests** covering:

- `config.py` — paths, settings, logical invariants
- `validator.py` — required fields, numeric ranges, categorical checks, edge cases

---

## 🚢 Deployment

### Development

=======

# Installation

Clone the repository:

```bash
git clone https://github.com/shivamlendghar/employee-attrition-performance-ai.git
```

Enter the project directory:

```bash
cd employee-attrition-performance-ai
```

Create a virtual environment:

```bash
python -m venv .venv
```

Activate it on Windows Git Bash:

```bash
source .venv/Scripts/activate
```

Install the required packages:

```bash
pip install -r requirements.txt
```

---

# Running the Application

Start the Flask application:

> > > > > > > origin/main

```bash
python app.py
```

<<<<<<< HEAD

### Production (Gunicorn)

```bash
gunicorn --bind 0.0.0.0:5000 --workers 2 --threads 4 app:app
```

### Docker

````bash
docker build -t hr-attrition-ai .
docker run --env-file .env -p 5000:5000 hr-attrition-ai
=======
Open the application in a browser:

```text
http://127.0.0.1:5000
>>>>>>> origin/main
````

---

<<<<<<< HEAD

## 📊 Model Performance

| Model               | Task        | Accuracy | F1    | ROC-AUC |
| ------------------- | ----------- | -------- | ----- | ------- |
| Deep Neural Network | Attrition   | ~87%     | ~0.72 | ~0.92   |
| Random Forest       | Attrition   | ~86%     | ~0.71 | ~0.91   |
| Logistic Regression | Attrition   | ~83%     | ~0.66 | ~0.88   |
| Deep Neural Network | Performance | ~78%     | ~0.77 | —       |

> Metrics are on hold-out test sets. Exact numbers in `results/`.

---

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/my-feature`
3. Install dev deps: `pip install -r requirements-dev.txt`
4. Make changes and add tests
5. Run `pytest tests/ -v` — all tests must pass
6. Open a pull request

---

## 📄 License

# MIT License. See `LICENSE` for details.

# Application Routes

| Page            | Route               |
| --------------- | ------------------- |
| Dashboard       | `/`                 |
| Prediction Lab  | `/prediction`       |
| Employee Roster | `/employees`        |
| HR Knowledge    | `/knowledge-search` |
| Risk Simulator  | `/simulator`        |
| Model Evidence  | `/model-evidence`   |

---

# API Endpoints

```text
GET  /api/health

GET  /api/employees

GET  /api/employees/<employee_id>

POST /api/predict

POST /api/employees/<employee_id>/action-center

POST /api/employees/<employee_id>/explain

POST /api/search

GET  /api/document/<document_id>

POST /api/simulate

GET  /api/dashboard

GET  /api/model-evidence
```

---

# Example HR Knowledge Search

A user can search:

```text
promotion policy
```

The selected IR method returns ranked results containing:

```text
Document
Document ID
Relevance Score
Matched Terms
```

The user can then select:

```text
View Document
```

to read the actual HR policy/document content.

---

# Important Notes

This project is an **academic HR decision-support prototype**.

Predictions and recommendations are intended to support human review and should not be used as autonomous employment decisions.

SHAP explanations represent model contributions and should not be treated as proof of causation.

The recorded evaluation metrics represent the project's model evaluation runs and should be interpreted in the context of the dataset and test split used during development.

---

# Current Limitations

The prototype does not implement production-grade:

- Authentication
- Role-based authorization
- Audit logging
- Enterprise employee-data access controls
- Encryption and secure deployment
- Formal fairness/bias assessment
- Continuous model monitoring

Additional governance, privacy, security, and fairness review would be required before real-world HR deployment.

---

# End-to-End Workflow

```text
Employee Roster
      ↓
Select Employee
      ↓
AI Assessment
      ↓
Attrition Risk + Performance
      ↓
SHAP Explanation
      ↓
HR Recommendations
      ↓
Relevant HR Policies
      ↓
BM25 / TF-IDF / Language Model
      ↓
HR Decision Support
```

---

# Project Objective

The objective of the project is to demonstrate how deep learning, machine learning, explainability, information retrieval, and recommendation techniques can be integrated into a unified HR intelligence platform.

The system brings together:

```text
Prediction
+
Explainability
+
Information Retrieval
+
Recommendations
+
Simulation
+
Model Evidence
```

to create a single academic HR decision-support workflow.

---

# Author

**Employee Performance & Attrition Prediction Using Deep Learning**

Academic Project

> > > > > > > origin/main
