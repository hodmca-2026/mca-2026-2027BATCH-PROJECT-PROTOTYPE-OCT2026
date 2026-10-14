# 🎬 Deep Learning-Based IMDB Movie Review Sentiment Analysis

> **MCA Sem 3 – Deep Learning Project**  
> Units IV (RNN/LSTM/GRU) · Unit V (Autoencoders) · Unit VI (Application)

---

## 📌 Overview

This project builds a complete end-to-end deep learning system that:
- Classifies IMDB movie reviews as **positive** or **negative**
- Compares **SimpleRNN**, **LSTM**, **BiLSTM**, and **GRU** models
- Implements a **Deep Autoencoder** for text representation and anomaly detection
- Deploys everything as a **Streamlit web application**

---

## 🗂️ Project Structure

```
sentiment analysis using deep learning/
│
├── app.py                    ← Streamlit web application
├── train_all.py              ← Master training script (run this first)
├── requirements.txt          ← Python dependencies
├── README.md                 ← This file
├── project_report.md         ← Full academic report
│
├── src/
│   ├── __init__.py
│   ├── data_preprocessing.py ← Dataset loading, tokenisation, padding
│   ├── train_rnn.py          ← SimpleRNN model
│   ├── train_lstm.py         ← LSTM model
│   ├── train_bilstm.py       ← Bidirectional LSTM model
│   ├── train_gru.py          ← GRU model
│   ├── train_autoencoder.py  ← Deep Autoencoder
│   ├── evaluation.py         ← Metrics, confusion matrix, comparison
│   └── prediction.py         ← Inference helpers for the app
│
├── notebooks/
│   └── exploration.py        ← EDA + quick model notebook (Colab-ready)
│
├── models/                   ← Saved .keras model files (created after training)
├── data/                     ← Preprocessing metadata and tokenizer (auto-generated)
├── evaluation_results/       ← Plots, metrics JSON, comparison CSV
└── assets/                   ← Static assets
```

---

## ⚡ Quick Start

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Train all models

```bash
python train_all.py
```

> **Expected time**:  
> - CPU: ~30–60 minutes  
> - GPU: ~5–15 minutes  
> 
> This creates all `.keras` model files in `models/` and evaluation plots in `evaluation_results/`.

### 3. Launch the web app

```bash
streamlit run app.py
```

Open **http://localhost:8501** in your browser.

---

## 🧠 Models Implemented

| Model | Unit | Key Feature |
|-------|------|-------------|
| **SimpleRNN** | IV | Basic recurrent cell, prone to vanishing gradient |
| **LSTM** | IV | 3 gates: forget, input, output – solves vanishing gradient |
| **BiLSTM** | IV | Reads forward + backward – full context |
| **GRU** | IV | 2 gates: update, reset – lighter than LSTM |
| **Deep Autoencoder** | V | Encoder → Bottleneck → Decoder, anomaly detection |

---

## 🌐 Web App Features

| Page | Description |
|------|-------------|
| 🏠 Home | Project overview and quick-start guide |
| 🔮 Sentiment Prediction | Enter a review → get sentiment + confidence |
| 📊 Model Comparison | Side-by-side metrics table and bar chart |
| 🔍 Autoencoder Analysis | Reconstruction error and anomaly flag |
| 📈 Evaluation Dashboard | Training curves, confusion matrices |
| 🏷️ NER (optional) | Named entity detection using spaCy |
| 📚 Theory | Architecture explanations for Units IV–V |

---

## 📊 Dataset

- **Source**: `tensorflow.keras.datasets.imdb`
- **Size**: 50,000 reviews (25k train / 25k test)
- **Labels**: 0 = Negative, 1 = Positive (balanced)
- **Preprocessing**:
  - Vocabulary limit: top 10,000 words
  - Sequence padding / truncation: length 200
  - Validation split: 20% of training data

---

## 📦 Dependencies

| Package | Purpose |
|---------|---------|
| `tensorflow` | Model building and training |
| `numpy`, `pandas` | Data manipulation |
| `scikit-learn` | Metrics and evaluation |
| `matplotlib`, `seaborn` | Plotting |
| `streamlit` | Web application |
| `spacy` | Named entity recognition (optional) |

---

## 🔧 Training Individual Models

```bash
# Preprocess only
python src/data_preprocessing.py

# Train individual models
python src/train_rnn.py
python src/train_lstm.py
python src/train_bilstm.py
python src/train_gru.py
python src/train_autoencoder.py

# Evaluate all
python src/evaluation.py
```

---

## 🐛 Troubleshooting

| Problem | Solution |
|---------|----------|
| `ModuleNotFoundError: tensorflow` | Run `pip install tensorflow` |
| `FileNotFoundError: model not found` | Run `python train_all.py` first |
| `OOM / memory error` | Reduce `BATCH_SIZE` in training scripts |
| Slow training on CPU | Use Google Colab with GPU runtime |
| spaCy model missing | Run `python -m spacy download en_core_web_sm` |

---

## 👤 Author

**MCA Student – Semester 3**  
Subject: Deep Learning  
Academic Year: 2024–25
