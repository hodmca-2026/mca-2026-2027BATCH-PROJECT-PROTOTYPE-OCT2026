"""
Training script for Unit V: Autoencoder Anomaly Detection
=========================================================
Trains a PyTorch Deep Autoencoder on historical academic projects.
Computes reconstruction error (MSE) across the training distribution,
establishes an anomaly threshold based on the 85th/90th percentile of normal reconstruction error,
evaluates on in-distribution vs out-of-distribution (anomalous) test samples,
and saves the model weights, vectorizer, and metadata.
"""

import os
import json
import pickle
import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import TensorDataset, DataLoader
from sklearn.feature_extraction.text import TfidfVectorizer

from dl_engine.autoencoder import ProjectAutoencoder
from dl_engine.training.train_lstm import TRAINING_DATA

# In-distribution corpus from academic projects
NORMAL_CORPUS = [title for title, _ in TRAINING_DATA]

# Synthetic out-of-distribution test queries to evaluate anomaly detection
OUT_OF_DISTRIBUTION_SAMPLES = [
    "Quantum entanglement based teleportation protocol in non-abelian anyon lattices",
    "Gourmet culinary recipe recommendation with sous vide thermal temperature charts",
    "High fashion textile weaving patterns using antique handloom jacquard machines",
    "Archaeological ceramic pottery classification using carbon-14 dating isotopes",
]


def train_autoencoder(
    artifacts_dir=None,
    epochs=60,
    batch_size=8,
    lr=0.005,
    hidden_dim=64,
    latent_dim=24,
    percentile_threshold=90.0,
):
    if artifacts_dir is None:
        artifacts_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "artifacts")
    os.makedirs(artifacts_dir, exist_ok=True)

    # 1. Feature extraction: TF-IDF representation
    vectorizer = TfidfVectorizer(max_features=250, ngram_range=(1, 2), stop_words="english")
    X_train_np = vectorizer.fit_transform(NORMAL_CORPUS).toarray()
    input_dim = X_train_np.shape[1]

    X_train = torch.tensor(X_train_np, dtype=torch.float32)
    dataset = TensorDataset(X_train)
    loader = DataLoader(dataset, batch_size=batch_size, shuffle=True)

    # 2. Model setup
    model = ProjectAutoencoder(input_dim=input_dim, hidden_dim=hidden_dim, latent_dim=latent_dim)
    criterion = nn.MSELoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)

    # 3. Training loop
    model.train()
    for epoch in range(epochs):
        for (batch_x,) in loader:
            optimizer.zero_grad()
            recon = model(batch_x)
            loss = criterion(recon, batch_x)
            loss.backward()
            optimizer.step()

    # 4. Reconstruction error distribution on normal samples
    model.eval()
    with torch.no_grad():
        recon_train = model(X_train)
        # Per-sample MSE: mean over feature dimensions
        sample_mses = torch.mean((recon_train - X_train) ** 2, dim=1).numpy()

    # Set threshold at specified percentile of training distribution
    threshold = float(np.percentile(sample_mses, percentile_threshold))
    mean_mse = float(np.mean(sample_mses))
    std_mse = float(np.std(sample_mses))

    print(f"[Autoencoder Training Complete] Input Dim: {input_dim}, Bottleneck: {latent_dim}")
    print(f"Normal Sample MSE - Mean: {mean_mse:.6f}, Std: {std_mse:.6f}, Threshold (P{int(percentile_threshold)}): {threshold:.6f}")

    # 5. Evaluate on Out-Of-Distribution (anomalous) samples with zero-vector awareness
    X_ood_np = vectorizer.transform(OUT_OF_DISTRIBUTION_SAMPLES).toarray()
    X_ood = torch.tensor(X_ood_np, dtype=torch.float32)
    with torch.no_grad():
        recon_ood = model(X_ood)
        ood_mses = torch.mean((recon_ood - X_ood) ** 2, dim=1).numpy()

    ood_results = []
    for sample, score, vec in zip(OUT_OF_DISTRIBUTION_SAMPLES, ood_mses, X_ood_np):
        is_zero_vector = bool(np.linalg.norm(vec) == 0.0)
        is_unusual = bool(score > threshold or is_zero_vector)
        ood_results.append({
            "text": sample,
            "mse": round(float(score), 6),
            "is_zero_vector": is_zero_vector,
            "detected_as_unusual": is_unusual,
        })
        print(f"  [OOD Test] MSE={score:.6f} (ZeroVector={is_zero_vector}, Unusual={is_unusual}): '{sample[:50]}...'")

    # 6. Save artifacts
    model_path = os.path.join(artifacts_dir, "autoencoder_model.pt")
    vectorizer_path = os.path.join(artifacts_dir, "autoencoder_vectorizer.pkl")
    meta_path = os.path.join(artifacts_dir, "autoencoder_meta.json")

    torch.save(model.state_dict(), model_path)
    with open(vectorizer_path, "wb") as f:
        pickle.dump(vectorizer, f)

    meta = {
        "model_type": "PyTorch Dense Autoencoder",
        "purpose": "Experimental Novelty & Anomaly Signal (Separate from Duplicate Detection)",
        "input_dim": input_dim,
        "hidden_dim": hidden_dim,
        "latent_dim": latent_dim,
        "epochs": epochs,
        "anomaly_threshold": round(threshold, 6),
        "mean_mse": round(mean_mse, 6),
        "std_mse": round(std_mse, 6),
        "percentile_used": percentile_threshold,
        "zero_vector_handling": "Flagged as unfamiliar vocabulary outlier (norm == 0)",
        "sample_size_limitation": "Trained on 70 illustrative academic titles; requires larger corpus for calibrated continuous anomaly detection",
        "ood_validation": ood_results,
    }
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)

    return meta


if __name__ == "__main__":
    train_autoencoder()
