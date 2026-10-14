"""
prediction.py
=============
Inference helper used by the Streamlit app.

Loads saved models and preprocessing artifacts once at startup
and provides fast, consistent prediction functions.
"""

import os, json, pickle, time
import numpy as np
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing.sequence import pad_sequences

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.data_preprocessing import VOCAB_SIZE, MAX_LEN

BASE_DIR   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODELS_DIR = os.path.join(BASE_DIR, "models")
DATA_DIR   = os.path.join(BASE_DIR, "data")
EVAL_DIR   = os.path.join(BASE_DIR, "evaluation_results")

MODEL_NAMES = ["simple_rnn", "lstm", "bilstm", "gru"]


# ──────────────────────────────────────────────────────────────────────────────
# Model registry – loaded lazily (once, then cached)
# ──────────────────────────────────────────────────────────────────────────────

_cache = {}   # name → keras Model


def _load_model(name: str):
    if name not in _cache:
        path = os.path.join(MODELS_DIR, f"{name}_best.keras")
        if not os.path.exists(path):
            raise FileNotFoundError(
                f"Model not found: {path}\n"
                f"Please run the training script for '{name}' first."
            )
        _cache[name] = load_model(path)
    return _cache[name]


def _load_word_index():
    if "word_index" not in _cache:
        path = os.path.join(DATA_DIR, "word_index.pkl")
        with open(path, "rb") as f:
            _cache["word_index"] = pickle.load(f)
    return _cache["word_index"]


def _load_autoencoder():
    if "ae" not in _cache:
        ae_path  = os.path.join(MODELS_DIR, "autoencoder_best.keras")
        enc_path = os.path.join(MODELS_DIR, "encoder_best.keras")
        _cache["ae"]  = load_model(ae_path)
        _cache["enc"] = load_model(enc_path)
        with open(os.path.join(DATA_DIR, "autoencoder_meta.json")) as f:
            _cache["ae_meta"] = json.load(f)
    return _cache["ae"], _cache["enc"], _cache["ae_meta"]


# ──────────────────────────────────────────────────────────────────────────────
# Text → padded sequence
# ──────────────────────────────────────────────────────────────────────────────

def _text_to_sequence(text: str, word_index: dict) -> np.ndarray:
    """
    Preprocess raw text using the SAME pipeline as training:
      1. Lowercase
      2. Remove non-alpha-numeric characters
      3. Map tokens to vocab integers (OOV → <UNK>=2)
      4. Pad / truncate to MAX_LEN
    """
    import re
    text   = text.lower()
    text   = re.sub(r"[^a-z0-9 ]", " ", text)
    tokens = text.split()

    seq = []
    for tok in tokens:
        idx = word_index.get(tok, 2)   # 2 = <UNK>
        if idx < VOCAB_SIZE:
            seq.append(idx)

    padded = pad_sequences([seq], maxlen=MAX_LEN, padding="post", truncating="post")
    return padded


# ──────────────────────────────────────────────────────────────────────────────
# Public API
# ──────────────────────────────────────────────────────────────────────────────

def predict_sentiment(text: str, model_name: str = "bilstm"):
    """
    Run sentiment prediction on raw text.

    Returns
    -------
    dict with keys:
      label       : "Positive" or "Negative"
      probability : float in [0, 1]  (P(positive))
      confidence  : float in [0.5, 1] (how certain the model is)
      infer_ms    : inference latency in milliseconds
    """
    if not text or not text.strip():
        return {
            "label": "Unknown", "probability": 0.5,
            "confidence": 0.0, "infer_ms": 0,
        }

    word_index = _load_word_index()
    seq        = _text_to_sequence(text, word_index)
    model      = _load_model(model_name)

    t0   = time.time()
    prob = float(model.predict(seq, verbose=0)[0][0])
    ms   = (time.time() - t0) * 1000

    label      = "Positive" if prob >= 0.5 else "Negative"
    confidence = prob if prob >= 0.5 else (1 - prob)

    return {
        "label":       label,
        "probability": prob,
        "confidence":  confidence,
        "infer_ms":    ms,
    }


def predict_all_models(text: str):
    """Run prediction across all four models and return a list of results."""
    results = []
    for name in MODEL_NAMES:
        try:
            r = predict_sentiment(text, model_name=name)
            r["model"] = name.upper()
            results.append(r)
        except FileNotFoundError as e:
            results.append({
                "model": name.upper(),
                "label": "Not trained",
                "probability": 0.0,
                "confidence": 0.0,
                "infer_ms": 0,
            })
    return results


def compute_reconstruction_error(text: str):
    """
    Compute the autoencoder reconstruction error for a raw review.

    Returns
    -------
    dict with keys:
      error      : float MSE
      threshold  : float (from training set)
      flagged    : bool – True if error > threshold
      note       : explanatory message
    """
    try:
        ae, enc, meta = _load_autoencoder()
    except FileNotFoundError:
        return {
            "error": None, "threshold": None,
            "flagged": None,
            "note": "Autoencoder model not found. Train it first.",
        }

    vocab_size = meta["input_dim"]
    threshold  = meta["threshold"]

    # Convert to BoW vector (same as training)
    word_index  = _load_word_index()
    seq         = _text_to_sequence(text, word_index).ravel()

    bow = np.zeros((1, vocab_size), dtype=np.float32)
    for tok in seq:
        if 0 < tok < vocab_size:
            bow[0, tok] += 1.0
    row_sum = bow[0].sum()
    if row_sum > 0:
        bow[0] /= row_sum

    x_hat  = ae.predict(bow, verbose=0)
    error  = float(np.mean(np.square(bow - x_hat)))
    flagged = error > threshold

    note = (
        "⚠️ This review's representation is statistically unusual compared to "
        "the training distribution. This does NOT mean the review is fake – "
        "it may simply be written in an atypical style, language, or topic."
        if flagged else
        "✅ This review's representation is within the normal range."
    )

    return {
        "error":     error,
        "threshold": threshold,
        "flagged":   flagged,
        "note":      note,
    }


def get_model_metrics(name: str) -> dict:
    """Load saved evaluation metrics for a given model."""
    path = os.path.join(EVAL_DIR, f"{name}_metrics.json")
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return {}


def get_best_model_name() -> str:
    """Return the name of the best-performing model (by F1-score)."""
    path = os.path.join(EVAL_DIR, "best_model.json")
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f).get("best_model", "BILSTM")
    return "BILSTM"


if __name__ == "__main__":
    sample = "The film was absolutely brilliant, a masterpiece of storytelling!"
    for name in MODEL_NAMES:
        try:
            r = predict_sentiment(sample, model_name=name)
            print(f"{name.upper():12s}: {r['label']:8s} (p={r['probability']:.3f}, {r['infer_ms']:.1f}ms)")
        except FileNotFoundError:
            print(f"{name.upper():12s}: model not found, skipping.")

    ae_result = compute_reconstruction_error(sample)
    print(f"\nAutoencoder error : {ae_result['error']}")
    print(f"Threshold         : {ae_result['threshold']}")
    print(f"Flagged           : {ae_result['flagged']}")
