"""
train_autoencoder.py
====================
Implements a Deep Autoencoder for learning compressed text representations
from IMDB reviews and detecting unusual (anomalous) review patterns.

Unit V mapping:
  - Encoder → Bottleneck → Decoder architecture
  - Reconstruction error
  - Anomaly detection using reconstruction error threshold
  - Regularisation (L2, Dropout)
  - Denoising Autoencoder variant
"""

import os, time, json, pickle
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from tensorflow.keras.models    import Model, Sequential
from tensorflow.keras.layers    import (Input, Dense, Dropout,
                                        Embedding, GlobalAveragePooling1D,
                                        GaussianNoise)
from tensorflow.keras.callbacks import EarlyStopping
from tensorflow.keras.optimizers import Adam
from tensorflow.keras           import regularizers

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.data_preprocessing import (
    load_keras_imdb, VOCAB_SIZE, MAX_LEN, EMBED_DIM
)

BASE_DIR   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODELS_DIR = os.path.join(BASE_DIR, "models")
EVAL_DIR   = os.path.join(BASE_DIR, "evaluation_results")
DATA_DIR   = os.path.join(BASE_DIR, "data")
os.makedirs(MODELS_DIR, exist_ok=True)
os.makedirs(EVAL_DIR,   exist_ok=True)

MODEL_NAME      = "autoencoder"
EMBED_DIM_AE    = 64      # embedding dim used inside the autoencoder
BOTTLENECK_DIM  = 32      # compressed representation size
NOISE_FACTOR    = 0.10    # noise added in denoising variant
EPOCHS          = 15
BATCH_SIZE      = 256
LR              = 1e-3


# ──────────────────────────────────────────────────────────────────────────────
# Step 1: Convert padded integer sequences → dense pooled embeddings
# ──────────────────────────────────────────────────────────────────────────────

def build_embedding_encoder(vocab_size=VOCAB_SIZE, embed_dim=EMBED_DIM_AE,
                             max_len=MAX_LEN):
    """
    Converts variable-length token sequences into a fixed-size vector by:
      1. Looking up a trainable embedding for each token.
      2. Average-pooling across the sequence dimension.

    Output shape: (batch, embed_dim)  – one vector per review.

    This is a simple but effective way to represent text for an autoencoder
    without adding sequential complexity.  More advanced alternatives include
    using the final LSTM hidden state or a pre-trained sentence encoder.
    """
    inp = Input(shape=(max_len,), name="token_input")
    x   = Embedding(vocab_size, embed_dim, name="embedding")(inp)
    x   = GlobalAveragePooling1D(name="avg_pool")(x)
    return Model(inp, x, name="SequenceToVector")


# ──────────────────────────────────────────────────────────────────────────────
# Step 2: Build the Autoencoder (Encoder + Bottleneck + Decoder)
# ──────────────────────────────────────────────────────────────────────────────

def build_autoencoder(input_dim: int, bottleneck_dim: int = BOTTLENECK_DIM,
                      denoising: bool = False):
    """
    Deep Autoencoder Architecture
    ------------------------------

    INPUT  (input_dim)
      │
      ▼  ── Encoder ──────────────────────────────────────────────────
    Dense(128, relu) + L2-regularisation
    Dropout(0.2)
    Dense(64,  relu)
      │
      ▼  ── Bottleneck ───────────────────────────────────────────────
    Dense(bottleneck_dim, relu)   ← compressed representation z
      │
      ▼  ── Decoder ──────────────────────────────────────────────────
    Dense(64,  relu)
    Dense(128, relu)
    Dense(input_dim, linear)      ← reconstructed input x̂
      │
      ▼
    OUTPUT  (input_dim)

    Loss: MSE(x, x̂)   – reconstruction error

    Anomaly detection:
      An unusual review will have a HIGH reconstruction error because
      the autoencoder was trained on typical reviews and cannot
      compress/reconstruct atypical ones accurately.

    Denoising Autoencoder (optional):
      Adding Gaussian noise to inputs forces the encoder to learn
      ROBUST representations – it must recover clean data from noisy input.

    NOTE: High reconstruction error means the review is statistically
    unusual relative to the training distribution.  It does NOT prove
    the review is fake or malicious.
    """
    inp = Input(shape=(input_dim,), name="ae_input")

    # Optional noise for denoising variant
    x = GaussianNoise(NOISE_FACTOR)(inp) if denoising else inp

    # ── Encoder ───────────────────────────────────────────────────────────────
    x = Dense(128, activation="relu",
              kernel_regularizer=regularizers.l2(1e-4),
              name="enc_1")(x)
    x = Dropout(0.2, name="enc_drop")(x)
    x = Dense(64,  activation="relu", name="enc_2")(x)

    # ── Bottleneck ─────────────────────────────────────────────────────────────
    bottleneck = Dense(bottleneck_dim, activation="relu", name="bottleneck")(x)

    # ── Decoder ───────────────────────────────────────────────────────────────
    x = Dense(64,       activation="relu",   name="dec_1")(bottleneck)
    x = Dense(128,      activation="relu",   name="dec_2")(x)
    output = Dense(input_dim, activation="linear", name="reconstruction")(x)

    autoencoder = Model(inp, output, name="DeepAutoencoder")
    encoder     = Model(inp, bottleneck, name="Encoder")

    autoencoder.compile(optimizer=Adam(LR), loss="mse")
    return autoencoder, encoder


# ──────────────────────────────────────────────────────────────────────────────
# Training
# ──────────────────────────────────────────────────────────────────────────────

def train():
    # ── Load sequences ────────────────────────────────────────────────────────
    (x_train, y_train), (x_val, y_val), (x_test, y_test), _ = load_keras_imdb()

    # ── Convert sequences → dense vectors using a small embedding model ───────
    print("[INFO] Converting sequences to dense embeddings …")
    seq2vec = build_embedding_encoder()
    # We train seq2vec jointly with the autoencoder; no separate training needed
    # because we use it as a non-trainable feature extractor AFTER the
    # autoencoder is fit in the embedding space.

    # For the AE we use a simple approach:
    #   Convert token IDs → bag-of-words normalised frequency vectors
    print("[INFO] Building BoW representation …")
    x_train_bow = _to_bow(x_train)
    x_val_bow   = _to_bow(x_val)
    x_test_bow  = _to_bow(x_test)

    input_dim = x_train_bow.shape[1]
    print(f"[INFO] BoW input dim = {input_dim}")

    # ── Build & train standard autoencoder ───────────────────────────────────
    print("[INFO] Training standard autoencoder …")
    ae, encoder = build_autoencoder(input_dim, denoising=False)
    ae.summary()

    t0 = time.time()
    history = ae.fit(
        x_train_bow, x_train_bow,
        validation_data=(x_val_bow, x_val_bow),
        epochs=EPOCHS,
        batch_size=BATCH_SIZE,
        callbacks=[EarlyStopping(monitor="val_loss", patience=4,
                                 restore_best_weights=True)],
        verbose=1,
    )
    train_time = time.time() - t0
    print(f"[INFO] AE training time: {train_time:.1f}s")

    # ── Compute reconstruction errors on TRAINING set → set anomaly threshold ─
    print("[INFO] Computing reconstruction errors on training set …")
    x_hat_train = ae.predict(x_train_bow, verbose=0)
    errors_train = np.mean(np.square(x_train_bow - x_hat_train), axis=1)

    # Threshold = mean + 2 × std on TRAINING errors (never use test data here!)
    threshold = float(np.mean(errors_train) + 2 * np.std(errors_train))
    print(f"[INFO] Anomaly threshold (mean + 2σ): {threshold:.6f}")

    # ── Evaluate on test set ──────────────────────────────────────────────────
    x_hat_test  = ae.predict(x_test_bow, verbose=0)
    errors_test = np.mean(np.square(x_test_bow - x_hat_test), axis=1)
    flagged     = np.sum(errors_test > threshold)
    print(f"[INFO] Test reviews flagged as unusual: {flagged}/{len(errors_test)}"
          f" ({100*flagged/len(errors_test):.1f}%)")

    # ── Train denoising variant ───────────────────────────────────────────────
    print("[INFO] Training denoising autoencoder …")
    dae, _ = build_autoencoder(input_dim, denoising=True)
    dae.fit(
        x_train_bow, x_train_bow,
        validation_data=(x_val_bow, x_val_bow),
        epochs=EPOCHS,
        batch_size=BATCH_SIZE,
        callbacks=[EarlyStopping(monitor="val_loss", patience=4,
                                 restore_best_weights=True)],
        verbose=0,
    )
    print("[INFO] Denoising AE trained ✓")

    # ── Save models & metadata ────────────────────────────────────────────────
    ae.save(os.path.join(MODELS_DIR, "autoencoder_best.keras"))
    encoder.save(os.path.join(MODELS_DIR, "encoder_best.keras"))

    ae_meta = {
        "input_dim":   input_dim,
        "bottleneck":  BOTTLENECK_DIM,
        "threshold":   threshold,
        "train_time":  float(train_time),
    }
    with open(os.path.join(DATA_DIR, "autoencoder_meta.json"), "w") as f:
        json.dump(ae_meta, f, indent=2)

    # ── Plots ─────────────────────────────────────────────────────────────────
    _plot_errors(errors_train, errors_test, threshold)
    _plot_ae_loss(history.history)

    print("[INFO] Autoencoder training complete ✓")
    return ae, encoder, threshold


# ──────────────────────────────────────────────────────────────────────────────
# Utility helpers
# ──────────────────────────────────────────────────────────────────────────────

def _to_bow(sequences: np.ndarray, vocab_size: int = VOCAB_SIZE) -> np.ndarray:
    """Convert padded integer sequences to normalised bag-of-words vectors."""
    bow = np.zeros((len(sequences), vocab_size), dtype=np.float32)
    for i, seq in enumerate(sequences):
        for tok in seq:
            if 0 < tok < vocab_size:
                bow[i, tok] += 1.0
        row_sum = bow[i].sum()
        if row_sum > 0:
            bow[i] /= row_sum     # L1 normalise
    return bow


def _plot_errors(train_errors, test_errors, threshold):
    fig, axes = plt.subplots(1, 2, figsize=(14, 4))

    axes[0].hist(train_errors, bins=60, color="steelblue", alpha=0.7, edgecolor="white")
    axes[0].axvline(threshold, color="red", linestyle="--", label=f"Threshold={threshold:.4f}")
    axes[0].set_title("Reconstruction Errors – Training Set")
    axes[0].set_xlabel("MSE")
    axes[0].set_ylabel("Count")
    axes[0].legend()

    axes[1].hist(test_errors, bins=60, color="darkorange", alpha=0.7, edgecolor="white")
    axes[1].axvline(threshold, color="red", linestyle="--", label=f"Threshold={threshold:.4f}")
    axes[1].set_title("Reconstruction Errors – Test Set")
    axes[1].set_xlabel("MSE")
    axes[1].set_ylabel("Count")
    axes[1].legend()

    plt.tight_layout()
    path = os.path.join(EVAL_DIR, "autoencoder_reconstruction_errors.png")
    plt.savefig(path, dpi=120)
    plt.close()
    print(f"[INFO] Error histogram saved → {path}")


def _plot_ae_loss(hist):
    plt.figure(figsize=(8, 4))
    plt.plot(hist["loss"],     label="Train Loss (MSE)")
    plt.plot(hist["val_loss"], label="Val Loss (MSE)")
    plt.title("Autoencoder Training Loss")
    plt.xlabel("Epoch")
    plt.ylabel("MSE")
    plt.legend()
    plt.grid(True, alpha=0.3)
    path = os.path.join(EVAL_DIR, "autoencoder_training_loss.png")
    plt.savefig(path, dpi=120)
    plt.close()
    print(f"[INFO] AE loss plot saved → {path}")


if __name__ == "__main__":
    train()
