# =============================================================================
# IMDB Sentiment Analysis – Google Colab / Jupyter Exploration Notebook
# =============================================================================
# This notebook is designed for data exploration, EDA, and quick model testing.
# For full training, use train_all.py from the project root.
#
# To use in Google Colab:
#   1. Upload this notebook and requirements.txt to Colab
#   2. Run the first cell to install dependencies
#   3. Run cells in order
# =============================================================================

# Cell 1: Install dependencies
# ----------------------------
# !pip install tensorflow numpy pandas scikit-learn matplotlib seaborn plotly

# Cell 2: Imports
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from tensorflow.keras.datasets import imdb
from tensorflow.keras.preprocessing.sequence import pad_sequences
from sklearn.metrics import classification_report, confusion_matrix

VOCAB_SIZE = 10_000
MAX_LEN    = 200

# Cell 3: Load dataset
(x_train_full, y_train_full), (x_test, y_test) = imdb.load_data(num_words=VOCAB_SIZE)

print(f"Training samples : {len(x_train_full)}")
print(f"Test samples     : {len(x_test)}")
print(f"Sample sequence  : {x_train_full[0][:20]} …")
print(f"Label            : {'positive' if y_train_full[0]==1 else 'negative'}")

# Cell 4: Decode a sample review
word_index = imdb.get_word_index()
word_index = {k: (v + 3) for k, v in word_index.items()}
word_index["<PAD>"] = 0; word_index["<START>"] = 1
word_index["<UNK>"] = 2; word_index["<UNUSED>"] = 3
reverse_index = {v: k for k, v in word_index.items()}

def decode(seq):
    return " ".join(reverse_index.get(i, "?") for i in seq)

print(decode(x_train_full[0]))

# Cell 5: EDA – Review length distribution
lengths = [len(s) for s in x_train_full]
plt.figure(figsize=(10, 4))
plt.hist(lengths, bins=60, color="steelblue", edgecolor="white")
plt.axvline(MAX_LEN, color="red", linestyle="--", label=f"MAX_LEN={MAX_LEN}")
plt.xlabel("Review Length (tokens)")
plt.ylabel("Count")
plt.title("Distribution of Review Lengths – Training Set")
plt.legend()
plt.show()
print(f"Mean: {np.mean(lengths):.1f}  Median: {np.median(lengths):.1f}  Max: {np.max(lengths)}")
print(f"Reviews ≤ {MAX_LEN} tokens: {np.mean(np.array(lengths) <= MAX_LEN)*100:.1f}%")

# Cell 6: Class balance
pos = y_train_full.sum()
neg = len(y_train_full) - pos
plt.figure(figsize=(4, 4))
plt.pie([pos, neg], labels=["Positive", "Negative"],
        colors=["#4CAF50", "#F44336"], autopct="%1.1f%%")
plt.title("Training Set Class Balance")
plt.show()

# Cell 7: Pad sequences
x_train_padded = pad_sequences(x_train_full, maxlen=MAX_LEN, padding="post", truncating="post")
x_test_padded  = pad_sequences(x_test,       maxlen=MAX_LEN, padding="post", truncating="post")
print(f"Train shape: {x_train_padded.shape}")
print(f"Test shape:  {x_test_padded.shape}")

# Cell 8: Build a quick LSTM model for notebook testing
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Embedding, LSTM, Dense, Dropout

EMBED_DIM  = 64
LSTM_UNITS = 64

model = Sequential([
    Embedding(VOCAB_SIZE, EMBED_DIM, input_length=MAX_LEN),
    LSTM(LSTM_UNITS),
    Dropout(0.3),
    Dense(1, activation="sigmoid"),
], name="Quick_LSTM")

model.compile(optimizer="adam", loss="binary_crossentropy", metrics=["accuracy"])
model.summary()

# Cell 9: Train (small run for notebook)
history = model.fit(
    x_train_padded, y_train_full,
    validation_split=0.2,
    epochs=5,
    batch_size=256,
    verbose=1,
)

# Cell 10: Plot curves
fig, axes = plt.subplots(1, 2, figsize=(12, 4))
axes[0].plot(history.history["accuracy"],     label="Train")
axes[0].plot(history.history["val_accuracy"], label="Validation")
axes[0].set_title("Accuracy"); axes[0].legend()

axes[1].plot(history.history["loss"],     label="Train")
axes[1].plot(history.history["val_loss"], label="Validation")
axes[1].set_title("Loss"); axes[1].legend()
plt.tight_layout()
plt.show()

# Cell 11: Evaluate
loss, acc = model.evaluate(x_test_padded, y_test, verbose=0)
print(f"Test Accuracy: {acc:.4f}   Test Loss: {loss:.4f}")

y_pred = (model.predict(x_test_padded, verbose=0) >= 0.5).astype(int).ravel()
print(classification_report(y_test, y_pred, target_names=["Negative", "Positive"]))

# Cell 12: Confusion matrix
cm = confusion_matrix(y_test, y_pred)
plt.figure(figsize=(5, 4))
sns.heatmap(cm, annot=True, fmt="d", cmap="Blues",
            xticklabels=["Neg", "Pos"], yticklabels=["Neg", "Pos"])
plt.xlabel("Predicted"); plt.ylabel("Actual")
plt.title("Confusion Matrix – Quick LSTM")
plt.show()

# Cell 13: Custom prediction
def predict_review(text):
    import re
    text   = text.lower()
    text   = re.sub(r"[^a-z0-9 ]", " ", text)
    tokens = text.split()
    seq    = [word_index.get(tok, 2) for tok in tokens if word_index.get(tok, 2) < VOCAB_SIZE]
    padded = pad_sequences([seq], maxlen=MAX_LEN, padding="post", truncating="post")
    prob   = model.predict(padded, verbose=0)[0][0]
    label  = "Positive" if prob >= 0.5 else "Negative"
    print(f"Sentiment : {label}  (p={prob:.4f})")

predict_review("This movie was absolutely fantastic! One of the best films I've seen.")
predict_review("Terrible waste of time. Boring, predictable, and badly acted.")
