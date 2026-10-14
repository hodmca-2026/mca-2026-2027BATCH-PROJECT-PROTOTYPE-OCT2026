"""
train_all.py
============
Master training script – runs the full ML pipeline in sequence:

  1.  Preprocess & verify data
  2.  Train SimpleRNN
  3.  Train LSTM
  4.  Train BiLSTM
  5.  Train GRU
  6.  Train Autoencoder
  7.  Run comprehensive evaluation
  8.  Print final summary

Run this once to populate the models/ and evaluation_results/ directories
before launching the Streamlit app.

Usage:
    python train_all.py

Expected time on CPU: 20-60 min (all 4 classifiers + autoencoder)
Expected time on GPU: 5-15 min
"""

import os, sys, time, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("=" * 60)
print("  IMDB Sentiment Analysis – Full Training Pipeline")
print("=" * 60)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
EVAL_DIR = os.path.join(BASE_DIR, "evaluation_results")

# ──────────────────────────────────────────────────────────────────────────────
# Step 1: Data
# ──────────────────────────────────────────────────────────────────────────────
print("\n[STEP 1/7] Loading & preprocessing data …")
from src.data_preprocessing import load_keras_imdb
(x_train, y_train), (x_val, y_val), (x_test, y_test), word_index = load_keras_imdb()
print(f"  Training   : {x_train.shape}")
print(f"  Validation : {x_val.shape}")
print(f"  Test       : {x_test.shape}")

# ──────────────────────────────────────────────────────────────────────────────
# Step 2-5: RNN family
# ──────────────────────────────────────────────────────────────────────────────
results = {}

for step, (label, module_path) in enumerate([
    ("SimpleRNN", "src.train_rnn"),
    ("LSTM",      "src.train_lstm"),
    ("BiLSTM",    "src.train_bilstm"),
    ("GRU",       "src.train_gru"),
], start=2):
    print(f"\n[STEP {step}/7] Training {label} …")
    t0 = time.time()
    module = __import__(module_path, fromlist=["train"])
    _, metrics = module.train()
    elapsed = time.time() - t0
    results[label] = metrics
    print(f"  ✓ {label} done in {elapsed:.1f}s  |  test_acc = {metrics['test_acc']:.4f}")

# ──────────────────────────────────────────────────────────────────────────────
# Step 6: Autoencoder
# ──────────────────────────────────────────────────────────────────────────────
print("\n[STEP 6/7] Training Autoencoder …")
from src.train_autoencoder import train as train_ae
ae, encoder, threshold = train_ae()
print(f"  ✓ Autoencoder done  |  anomaly threshold = {threshold:.6f}")

# ──────────────────────────────────────────────────────────────────────────────
# Step 7: Evaluation
# ──────────────────────────────────────────────────────────────────────────────
print("\n[STEP 7/7] Running comprehensive evaluation …")
from src.evaluation import evaluate_all
df = evaluate_all()

# ──────────────────────────────────────────────────────────────────────────────
# Final summary
# ──────────────────────────────────────────────────────────────────────────────
print("\n" + "=" * 60)
print("  Training Complete!")
print("=" * 60)
if df is not None:
    print(df[["Model", "Accuracy", "Precision", "Recall", "F1-Score"]].to_string(index=False))
    best = df.loc[df["F1-Score"].idxmax(), "Model"]
    print(f"\n  🏆 Best model by F1-Score: {best}")

print(f"\n  Models saved in   : {os.path.join(BASE_DIR, 'models')}/")
print(f"  Results saved in  : {EVAL_DIR}/")
print("\n  Launch the app with:")
print("    streamlit run app.py")
print("=" * 60)
