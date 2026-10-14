"""
train_rnn.py
============
Builds and trains a Simple Recurrent Neural Network (SimpleRNN) for
binary sentiment classification on the IMDB dataset.

Unit IV mapping:
  - Recurrent Neural Networks (RNN)
  - Sequence learning
  - Vanishing gradient problem (SimpleRNN is most prone to this)
"""

import os, time, json
import numpy as np
import matplotlib
matplotlib.use("Agg")          # non-interactive backend (safe for scripts)
import matplotlib.pyplot as plt

from tensorflow.keras.models     import Sequential
from tensorflow.keras.layers     import Embedding, SimpleRNN, Dense, Dropout
from tensorflow.keras.callbacks  import EarlyStopping, ModelCheckpoint
from tensorflow.keras.optimizers import Adam

# ── Local imports ─────────────────────────────────────────────────────────────
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.data_preprocessing import (
    load_keras_imdb, VOCAB_SIZE, MAX_LEN, EMBED_DIM
)

# ── Paths ──────────────────────────────────────────────────────────────────────
BASE_DIR   = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODELS_DIR = os.path.join(BASE_DIR, "models")
EVAL_DIR   = os.path.join(BASE_DIR, "evaluation_results")
os.makedirs(MODELS_DIR, exist_ok=True)
os.makedirs(EVAL_DIR,   exist_ok=True)

MODEL_NAME = "simple_rnn"

# ── Hyper-parameters ───────────────────────────────────────────────────────────
EPOCHS     = 10
BATCH_SIZE = 128
RNN_UNITS  = 64
DROPOUT    = 0.3
LR         = 1e-3


def build_model():
    """
    Architecture
    ------------
    Embedding  → (MAX_LEN, EMBED_DIM)   word vector lookup table
    SimpleRNN  → (RNN_UNITS,)           single recurrent layer
    Dropout    →                        regularisation
    Dense(1)   → sigmoid               binary output (P(positive))

    SimpleRNN is the most basic recurrent cell.  At each time-step t it
    computes:
        h_t = tanh(W_h * h_{t-1} + W_x * x_t + b)
    The final hidden state is used as the sentence representation.

    LIMITATION: SimpleRNN suffers from the vanishing gradient problem for
    long sequences – gradients shrink exponentially as they propagate back
    through time, making it hard to learn long-range dependencies.
    """
    model = Sequential([
        Embedding(VOCAB_SIZE, EMBED_DIM, input_length=MAX_LEN),
        SimpleRNN(RNN_UNITS, return_sequences=False),
        Dropout(DROPOUT),
        Dense(32, activation="relu"),
        Dense(1,  activation="sigmoid"),
    ], name="SimpleRNN_Sentiment")

    model.compile(
        optimizer=Adam(LR),
        loss="binary_crossentropy",
        metrics=["accuracy"],
    )
    return model


def train():
    # ── Load data ─────────────────────────────────────────────────────────────
    (x_train, y_train), (x_val, y_val), (x_test, y_test), _ = load_keras_imdb()

    # ── Build ─────────────────────────────────────────────────────────────────
    model = build_model()
    model.summary()

    callbacks = [
        EarlyStopping(monitor="val_loss", patience=3, restore_best_weights=True),
        ModelCheckpoint(
            filepath=os.path.join(MODELS_DIR, f"{MODEL_NAME}_best.keras"),
            monitor="val_accuracy", save_best_only=True, verbose=1
        ),
    ]

    # ── Train ─────────────────────────────────────────────────────────────────
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

    # ── Evaluate on held-out test set ─────────────────────────────────────────
    loss, acc = model.evaluate(x_test, y_test, verbose=0)
    print(f"[TEST] Loss={loss:.4f}  Accuracy={acc:.4f}")

    # ── Save history & metrics ────────────────────────────────────────────────
    hist_dict = {k: [float(v) for v in vals] for k, vals in history.history.items()}
    metrics = {
        "model":       MODEL_NAME,
        "test_loss":   float(loss),
        "test_acc":    float(acc),
        "train_time":  float(train_time),
        "epochs_run":  len(hist_dict["loss"]),
        "history":     hist_dict,
    }
    with open(os.path.join(EVAL_DIR, f"{MODEL_NAME}_metrics.json"), "w") as f:
        json.dump(metrics, f, indent=2)

    # ── Plot training curves ──────────────────────────────────────────────────
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
        ax.set_title(f"{name} – {title}")
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
