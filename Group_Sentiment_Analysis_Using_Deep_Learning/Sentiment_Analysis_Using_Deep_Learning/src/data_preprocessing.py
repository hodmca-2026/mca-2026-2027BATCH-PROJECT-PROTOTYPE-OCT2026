"""
data_preprocessing.py
=====================
Handles loading and preprocessing of the IMDB dataset.

This module:
  - Loads the IMDB dataset (from Keras built-in OR from a local Excel/CSV file)
  - Tokenises and pads sequences
  - Saves the tokeniser config and metadata for later use by the app

Unit IV mapping: Sequence learning, text representation via embedding
"""

import os
import json
import pickle
import numpy as np
import pandas as pd
from tensorflow.keras.datasets import imdb
from tensorflow.keras.preprocessing.sequence import pad_sequences
from tensorflow.keras.preprocessing.text import Tokenizer

# ──────────────────────────────────────────────────────────────────────────────
# Constants – these are the shared settings used by every training script
# ──────────────────────────────────────────────────────────────────────────────
VOCAB_SIZE   = 10_000   # Keep only the 10 000 most frequent words
MAX_LEN      = 200      # Pad / truncate every review to this length
EMBED_DIM    = 64       # Word-embedding size
VALID_SPLIT  = 0.2      # 20 % of training data is used for validation
RANDOM_SEED  = 42

# Paths – everything is relative to the project root
BASE_DIR    = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR    = os.path.join(BASE_DIR, "data")
MODELS_DIR  = os.path.join(BASE_DIR, "models")

os.makedirs(DATA_DIR,   exist_ok=True)
os.makedirs(MODELS_DIR, exist_ok=True)


# ──────────────────────────────────────────────────────────────────────────────
# Helper: decode integer sequences back to text (Keras IMDB word index)
# ──────────────────────────────────────────────────────────────────────────────
def get_keras_word_index():
    """Return the word-to-integer mapping provided by Keras IMDB."""
    word_index = imdb.get_word_index()
    # Keras reserves indices 0-3 for special tokens
    word_index = {k: (v + 3) for k, v in word_index.items()}
    word_index["<PAD>"]     = 0
    word_index["<START>"]   = 1
    word_index["<UNK>"]     = 2
    word_index["<UNUSED>"]  = 3
    return word_index


def decode_review(sequence, word_index):
    """Convert an integer sequence back to a human-readable string."""
    reverse_index = {v: k for k, v in word_index.items()}
    return " ".join(reverse_index.get(i, "?") for i in sequence)


# ──────────────────────────────────────────────────────────────────────────────
# Main loading function – Keras built-in dataset
# ──────────────────────────────────────────────────────────────────────────────
def load_keras_imdb():
    """
    Load the standard IMDB dataset that ships with Keras/TensorFlow.

    Returns
    -------
    (x_train, y_train) : training sequences + labels
    (x_val,   y_val)   : validation sequences + labels (20 % of train)
    (x_test,  y_test)  : held-out test set – never used for tuning
    word_index          : dict mapping word → integer
    """
    print("[INFO] Loading Keras IMDB dataset …")
    (x_train_full, y_train_full), (x_test, y_test) = imdb.load_data(
        num_words=VOCAB_SIZE
    )

    # ── Validation split ──────────────────────────────────────────────────────
    np.random.seed(RANDOM_SEED)
    indices   = np.random.permutation(len(x_train_full))
    val_size  = int(len(x_train_full) * VALID_SPLIT)
    val_idx   = indices[:val_size]
    train_idx = indices[val_size:]

    x_train = [x_train_full[i] for i in train_idx]
    y_train = y_train_full[train_idx]
    x_val   = [x_train_full[i] for i in val_idx]
    y_val   = y_train_full[val_idx]

    # ── Padding ───────────────────────────────────────────────────────────────
    x_train = pad_sequences(x_train, maxlen=MAX_LEN, padding="post", truncating="post")
    x_val   = pad_sequences(x_val,   maxlen=MAX_LEN, padding="post", truncating="post")
    x_test  = pad_sequences(x_test,  maxlen=MAX_LEN, padding="post", truncating="post")

    y_train = np.array(y_train)
    y_val   = np.array(y_val)
    y_test  = np.array(y_test)

    word_index = get_keras_word_index()

    print(f"[INFO] Train : {x_train.shape}  Val : {x_val.shape}  Test : {x_test.shape}")
    print(f"[INFO] Positive train samples : {y_train.sum()} / {len(y_train)}")

    # ── Save metadata for the Streamlit app ───────────────────────────────────
    meta = {
        "vocab_size": VOCAB_SIZE,
        "max_len":    MAX_LEN,
        "embed_dim":  EMBED_DIM,
        "source":     "keras_builtin",
    }
    with open(os.path.join(DATA_DIR, "preprocessing_meta.json"), "w") as f:
        json.dump(meta, f, indent=2)

    # Save word index (needed by the app for custom text prediction)
    with open(os.path.join(DATA_DIR, "word_index.pkl"), "wb") as f:
        pickle.dump(word_index, f)

    print("[INFO] Preprocessing metadata saved.")
    return (x_train, y_train), (x_val, y_val), (x_test, y_test), word_index


# ──────────────────────────────────────────────────────────────────────────────
# Fallback: load from local Excel file (IMDB Dataset_sample.xlsx)
# ──────────────────────────────────────────────────────────────────────────────
def load_local_excel(filepath: str):
    """
    Load from a local Excel or CSV file.
    Expected columns: 'review' (text) and 'sentiment' ('positive'/'negative').

    Returns the same tuple shape as load_keras_imdb().
    """
    print(f"[INFO] Loading local file: {filepath}")
    if filepath.endswith(".xlsx") or filepath.endswith(".xls"):
        df = pd.read_excel(filepath)
    else:
        df = pd.read_csv(filepath)

    # Normalise column names
    df.columns = [c.strip().lower() for c in df.columns]
    assert "review"    in df.columns, "Column 'review' not found."
    assert "sentiment" in df.columns, "Column 'sentiment' not found."

    df = df.dropna(subset=["review", "sentiment"])
    df["label"] = (df["sentiment"].str.lower().str.strip() == "positive").astype(int)

    # ── Tokenise ──────────────────────────────────────────────────────────────
    tokenizer = Tokenizer(num_words=VOCAB_SIZE, oov_token="<OOV>")
    tokenizer.fit_on_texts(df["review"].values)
    sequences = tokenizer.texts_to_sequences(df["review"].values)
    padded    = pad_sequences(sequences, maxlen=MAX_LEN, padding="post", truncating="post")
    labels    = df["label"].values

    # ── Train / Val / Test split (70 / 15 / 15) ───────────────────────────────
    np.random.seed(RANDOM_SEED)
    idx      = np.random.permutation(len(padded))
    n        = len(padded)
    train_end = int(0.70 * n)
    val_end   = int(0.85 * n)

    x_train, y_train = padded[idx[:train_end]],  labels[idx[:train_end]]
    x_val,   y_val   = padded[idx[train_end:val_end]], labels[idx[train_end:val_end]]
    x_test,  y_test  = padded[idx[val_end:]],    labels[idx[val_end:]]

    print(f"[INFO] Train : {x_train.shape}  Val : {x_val.shape}  Test : {x_test.shape}")

    # ── Save tokenizer ────────────────────────────────────────────────────────
    with open(os.path.join(DATA_DIR, "tokenizer.pkl"), "wb") as f:
        pickle.dump(tokenizer, f)

    meta = {
        "vocab_size": VOCAB_SIZE,
        "max_len":    MAX_LEN,
        "embed_dim":  EMBED_DIM,
        "source":     "local_excel",
    }
    with open(os.path.join(DATA_DIR, "preprocessing_meta.json"), "w") as f:
        json.dump(meta, f, indent=2)

    print("[INFO] Tokenizer and metadata saved.")
    return (x_train, y_train), (x_val, y_val), (x_test, y_test), tokenizer.word_index


# ──────────────────────────────────────────────────────────────────────────────
# Text preprocessing for inference (app.py calls this)
# ──────────────────────────────────────────────────────────────────────────────
def preprocess_text_for_inference(text: str, word_index: dict, max_len: int = MAX_LEN) -> np.ndarray:
    """
    Convert raw review text → padded integer sequence ready for the model.
    Uses the same pipeline as training (lowercase, vocabulary mapping).
    """
    import re
    # Basic cleaning
    text = text.lower()
    text = re.sub(r"[^a-z0-9 ]", " ", text)
    tokens = text.split()

    # Map tokens to integer IDs
    sequence = []
    for token in tokens:
        idx = word_index.get(token, word_index.get("<UNK>", 2))
        if idx < VOCAB_SIZE:
            sequence.append(idx)

    # Pad / truncate
    padded = pad_sequences([sequence], maxlen=max_len, padding="post", truncating="post")
    return padded


# ──────────────────────────────────────────────────────────────────────────────
# Quick self-test
# ──────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    # Try the Keras built-in dataset first
    (x_train, y_train), (x_val, y_val), (x_test, y_test), word_index = load_keras_imdb()

    print("\n── Sample review (decoded) ──")
    print(decode_review(x_train[0], word_index))
    print(f"Label : {'positive' if y_train[0] == 1 else 'negative'}")

    # Test inference preprocessing
    sample = "This movie was absolutely fantastic and I loved every moment of it!"
    arr = preprocess_text_for_inference(sample, word_index)
    print(f"\nInference input shape : {arr.shape}")
    print("Preprocessing complete ✓")
