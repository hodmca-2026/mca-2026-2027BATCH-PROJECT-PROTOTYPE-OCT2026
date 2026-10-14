"""
evaluation.py
=============
Comprehensive evaluation of all trained models on the held-out test set.

Produces:
  - Per-model: accuracy, precision, recall, F1-score, confusion matrix
  - Cross-model comparison table (CSV + PNG chart)
  - Classification reports
  - Inference time benchmarks

This module is run ONCE after all models are trained.
"""

import os, json, time, pickle
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns

from sklearn.metrics import (
    accuracy_score, precision_score, recall_score,
    f1_score, confusion_matrix, classification_report,
)
from tensorflow.keras.models import load_model

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.data_preprocessing import load_keras_imdb

BASE_DIR   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODELS_DIR = os.path.join(BASE_DIR, "models")
EVAL_DIR   = os.path.join(BASE_DIR, "evaluation_results")
os.makedirs(EVAL_DIR, exist_ok=True)

MODEL_NAMES = ["simple_rnn", "lstm", "bilstm", "gru"]
LABEL_NAMES = ["Negative", "Positive"]


def evaluate_all():
    """Evaluate every trained model on the same held-out test set."""
    _, _, (x_test, y_test), _ = load_keras_imdb()

    summary_rows = []

    for name in MODEL_NAMES:
        model_path = os.path.join(MODELS_DIR, f"{name}_best.keras")
        if not os.path.exists(model_path):
            print(f"[WARN] Model not found: {model_path} – skipping.")
            continue

        print(f"\n──────────────────────────────────────────")
        print(f"[INFO] Evaluating: {name.upper()}")
        model = load_model(model_path)

        # ── Inference time ────────────────────────────────────────────────────
        # Warm-up pass
        _ = model.predict(x_test[:32], verbose=0)

        t0      = time.time()
        y_prob  = model.predict(x_test, verbose=0).ravel()
        infer_s = time.time() - t0

        y_pred  = (y_prob >= 0.5).astype(int)

        acc  = accuracy_score (y_test, y_pred)
        prec = precision_score(y_test, y_pred, zero_division=0)
        rec  = recall_score   (y_test, y_pred, zero_division=0)
        f1   = f1_score       (y_test, y_pred, zero_division=0)
        cm   = confusion_matrix(y_test, y_pred)

        print(f"  Accuracy  : {acc:.4f}")
        print(f"  Precision : {prec:.4f}")
        print(f"  Recall    : {rec:.4f}")
        print(f"  F1-score  : {f1:.4f}")
        print(f"  Inference : {infer_s:.2f}s for {len(x_test)} samples")
        print(classification_report(y_test, y_pred, target_names=LABEL_NAMES))

        # ── Confusion matrix plot ─────────────────────────────────────────────
        _plot_confusion_matrix(cm, name)

        # ── Per-model metrics JSON ─────────────────────────────────────────────
        existing_path = os.path.join(EVAL_DIR, f"{name}_metrics.json")
        existing = {}
        if os.path.exists(existing_path):
            with open(existing_path) as f:
                existing = json.load(f)

        existing.update({
            "test_accuracy":  float(acc),
            "test_precision": float(prec),
            "test_recall":    float(rec),
            "test_f1":        float(f1),
            "inference_time": float(infer_s),
        })
        with open(existing_path, "w") as f:
            json.dump(existing, f, indent=2)

        # Load training time from existing record
        train_time = existing.get("train_time", 0)

        summary_rows.append({
            "Model":          name.upper(),
            "Accuracy":       acc,
            "Precision":      prec,
            "Recall":         rec,
            "F1-Score":       f1,
            "Train Time (s)": train_time,
            "Infer Time (s)": infer_s,
        })

    if not summary_rows:
        print("[WARN] No models evaluated.")
        return

    # ── Summary table ─────────────────────────────────────────────────────────
    df = pd.DataFrame(summary_rows)
    df.to_csv(os.path.join(EVAL_DIR, "model_comparison.csv"), index=False)
    print("\n══════════════════════════════════════════════")
    print(df.to_string(index=False))

    # ── Comparison bar chart ──────────────────────────────────────────────────
    _plot_comparison(df)

    # Identify best model
    best_row  = df.loc[df["F1-Score"].idxmax()]
    best_name = best_row["Model"]
    print(f"\n[INFO] Best model by F1-Score: {best_name}")

    best_info = {"best_model": best_name, "best_f1": float(best_row["F1-Score"])}
    with open(os.path.join(EVAL_DIR, "best_model.json"), "w") as f:
        json.dump(best_info, f, indent=2)

    return df


def _plot_confusion_matrix(cm, name):
    fig, ax = plt.subplots(figsize=(5, 4))
    sns.heatmap(cm, annot=True, fmt="d", cmap="Blues",
                xticklabels=LABEL_NAMES, yticklabels=LABEL_NAMES, ax=ax)
    ax.set_xlabel("Predicted")
    ax.set_ylabel("Actual")
    ax.set_title(f"Confusion Matrix – {name.upper()}")
    plt.tight_layout()
    path = os.path.join(EVAL_DIR, f"{name}_confusion_matrix.png")
    plt.savefig(path, dpi=120)
    plt.close()
    print(f"[INFO] Confusion matrix → {path}")


def _plot_comparison(df: pd.DataFrame):
    metrics = ["Accuracy", "Precision", "Recall", "F1-Score"]
    x = np.arange(len(df))
    width = 0.2

    fig, ax = plt.subplots(figsize=(12, 5))
    for i, m in enumerate(metrics):
        ax.bar(x + i * width, df[m], width, label=m)

    ax.set_xticks(x + width * (len(metrics) - 1) / 2)
    ax.set_xticklabels(df["Model"])
    ax.set_ylim(0, 1.05)
    ax.set_ylabel("Score")
    ax.set_title("Model Comparison – Sentiment Classification")
    ax.legend()
    ax.grid(axis="y", alpha=0.3)
    plt.tight_layout()
    path = os.path.join(EVAL_DIR, "model_comparison_chart.png")
    plt.savefig(path, dpi=120)
    plt.close()
    print(f"[INFO] Comparison chart → {path}")


if __name__ == "__main__":
    evaluate_all()
