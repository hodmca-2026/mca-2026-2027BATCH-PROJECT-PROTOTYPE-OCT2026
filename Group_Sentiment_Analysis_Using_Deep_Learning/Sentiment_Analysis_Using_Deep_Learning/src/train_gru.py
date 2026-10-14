"""
train_gru.py
============
Builds and trains a Gated Recurrent Unit (GRU) model for IMDB sentiment.

Unit IV mapping:
  - GRU architecture
  - Update gate and reset gate
  - Comparison with LSTM (fewer parameters, similar performance)
"""

import os, time, json
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from tensorflow.keras.models    import Sequential
from tensorflow.keras.layers    import Embedding, GRU, Dense, Dropout
from tensorflow.keras.callbacks import EarlyStopping, ModelCheckpoint
from tensorflow.keras.optimizers import Adam

import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.data_preprocessing import (
    load_keras_imdb, VOCAB_SIZE, MAX_LEN, EMBED_DIM
)

BASE_DIR   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODELS_DIR = os.path.join(BASE_DIR, "models")
EVAL_DIR   = os.path.join(BASE_DIR, "evaluation_results")
os.makedirs(MODELS_DIR, exist_ok=True)
os.makedirs(EVAL_DIR,   exist_ok=True)

MODEL_NAME = "gru"
EPOCHS     = 10
BATCH_SIZE = 128
GRU_UNITS  = 64
DROPOUT    = 0.3
LR         = 1e-3


def build_model():
    """
    GRU Architecture (Cho et al., 2014)
    -------------------------------------
    A GRU simplifies the LSTM by merging the cell state and hidden state and
    using only TWO gates:

      Reset gate  : r_t = σ(W_r · [h_{t-1}, x_t])
        → controls how much of the PREVIOUS hidden state to RESET (forget)
        → r_t ≈ 0  : ignore past, focus on current input
        → r_t ≈ 1  : keep past memory

      Update gate : z_t = σ(W_z · [h_{t-1}, x_t])
        → balances between old memory and new candidate:

      Candidate   : h̃_t = tanh(W · [r_t ⊙ h_{t-1}, x_t])
        → new candidate hidden state

      Hidden state: h_t = (1 - z_t) ⊙ h_{t-1} + z_t ⊙ h̃_t
        → z_t ≈ 0 : keep old state (like identity / skip)
        → z_t ≈ 1 : replace with candidate (like forget + write in LSTM)

    GRU has ~25 % fewer parameters than LSTM and often converges faster.
    """
    model = Sequential([
        Embedding(VOCAB_SIZE, EMBED_DIM, input_length=MAX_LEN),
        GRU(GRU_UNITS, return_sequences=False),
        Dropout(DROPOUT),
        Dense(32, activation="relu"),
        Dense(1,  activation="sigmoid"),
    ], name="GRU_Sentiment")

    model.compile(
        optimizer=Adam(LR),
        loss="binary_crossentropy",
        metrics=["accuracy"],
    )
    return model


def train():
    (x_train, y_train), (x_val, y_val), (x_test, y_test), _ = load_keras_imdb()

    model = build_model()
    model.summary()

    callbacks = [
        EarlyStopping(monitor="val_loss", patience=3, restore_best_weights=True),
        ModelCheckpoint(
            filepath=os.path.join(MODELS_DIR, f"{MODEL_NAME}_best.keras"),
            monitor="val_accuracy", save_best_only=True, verbose=1
        ),
    ]

    t0 = time.time()
    history = model.fit(
        x_train, y_train,
        validation_data=(x_val, y_val),
        epochs=EPOCHS,
        batch_size=BATCH_SIZE,
        callbacks=callbacks,
        verbose=1,
    )
    train_time = time.time() - t0
    print(f"\n[INFO] Training time: {train_time:.1f}s")

    loss, acc = model.evaluate(x_test, y_test, verbose=0)
    print(f"[TEST] Loss={loss:.4f}  Accuracy={acc:.4f}")

    hist_dict = {k: [float(v) for v in vals] for k, vals in history.history.items()}
    metrics = {
        "model":      MODEL_NAME,
        "test_loss":  float(loss),
        "test_acc":   float(acc),
        "train_time": float(train_time),
        "epochs_run": len(hist_dict["loss"]),
        "history":    hist_dict,
    }
    with open(os.path.join(EVAL_DIR, f"{MODEL_NAME}_metrics.json"), "w") as f:
        json.dump(metrics, f, indent=2)

    _plot_history(hist_dict, MODEL_NAME)
    print(f"[INFO] Model saved → models/{MODEL_NAME}_best.keras")
    return model, metrics


def _plot_history(hist, name):
    fig, axes = plt.subplots(1, 2, figsize=(12, 4))
    for ax, metric, title in zip(
        axes,
        [("accuracy", "val_accuracy"), ("loss", "val_loss")],
        ["Accuracy", "Loss"],
    ):
        ax.plot(hist[metric[0]], label="Train")
        ax.plot(hist[metric[1]], label="Validation")
        ax.set_title(f"{name.upper()} – {title}")
        ax.set_xlabel("Epoch")
        ax.set_ylabel(title)
        ax.legend()
        ax.grid(True, alpha=0.3)
    plt.tight_layout()
    path = os.path.join(EVAL_DIR, f"{name}_training_curves.png")
    plt.savefig(path, dpi=120)
    plt.close()
    print(f"[INFO] Training curves saved → {path}")


if __name__ == "__main__":
    train()
