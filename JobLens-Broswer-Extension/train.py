"""UNIT V (DL) - AUTOENCODER for anomaly detection.

Uses: deep autoencoder + denoising (noise on input) + regularization (L2 + dropout).
Trained on GENUINE postings only. High reconstruction error => anomaly => likely fraud.

Dataset: Kaggle "Real / Fake Job Posting Prediction" -> save as fake_job_postings.csv
Run:  python train.py
"""
import pickle
import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split
from sklearn.metrics import precision_recall_fscore_support, classification_report
from tensorflow import keras
from tensorflow.keras import layers, regularizers

from crawler import clean

# 1. Load + clean text
df = pd.read_csv("fake_job_postings.csv")
cols = ["title", "company_profile", "description", "requirements", "benefits"]
df["text"] = df[cols].fillna("").agg(" ".join, axis=1).apply(clean)
y = df["fraudulent"].values

# 2. TF-IDF features
vec = TfidfVectorizer(max_features=2000, stop_words="english")
X = vec.fit_transform(df["text"]).toarray().astype("float32")

X_train_all, X_val, y_train_all, y_val = train_test_split(
    X, y, test_size=0.2, stratify=y, random_state=42)
X_train = X_train_all[y_train_all == 0]               # genuine only!
print("Training on genuine postings:", len(X_train))

# 3. Deep denoising autoencoder with regularization
reg = regularizers.l2(1e-5)
inp = keras.Input(shape=(2000,))
x = layers.GaussianNoise(0.05)(inp)                   # denoising (only active in training)
x = layers.Dense(256, activation="relu", kernel_regularizer=reg)(x)
x = layers.Dropout(0.2)(x)                            # regularization
x = layers.Dense(64, activation="relu", kernel_regularizer=reg)(x)
code = layers.Dense(16, activation="relu")(x)         # bottleneck
x = layers.Dense(64, activation="relu")(code)
x = layers.Dense(256, activation="relu")(x)
out = layers.Dense(2000, activation="sigmoid")(x)

autoencoder = keras.Model(inp, out)
autoencoder.compile(optimizer="adam", loss="mse")
autoencoder.fit(X_train, X_train, epochs=30, batch_size=128,
                validation_split=0.1, shuffle=True)

# 4. Reconstruction error + threshold chosen on validation set (best F1)
def recon_error(data):
    return np.mean((data - autoencoder.predict(data, verbose=0)) ** 2, axis=1)

err = recon_error(X_val)
best_t, best_f1 = 0, 0
for t in np.percentile(err, np.arange(50, 100, 0.5)):
    _, _, f1, _ = precision_recall_fscore_support(
        y_val, (err > t).astype(int), average="binary", zero_division=0)
    if f1 > best_f1:
        best_t, best_f1 = t, f1
print(f"Best threshold = {best_t:.6f}  (F1 = {best_f1:.3f})")
print(classification_report(y_val, (err > best_t).astype(int),
                            target_names=["genuine", "fraud"]))

# 5. Save
autoencoder.save("autoencoder.keras")
pickle.dump({"vectorizer": vec, "threshold": float(best_t)}, open("meta.pkl", "wb"))
print("Saved autoencoder.keras and meta.pkl")
