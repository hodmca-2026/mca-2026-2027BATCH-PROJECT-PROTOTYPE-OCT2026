"""
Unit V: Autoencoders — Anomaly Detection for Unusual Projects
=============================================================
PyTorch Encoder-Decoder Neural Network for detecting unusual or anomalous
project proposals based on reconstruction Mean Squared Error (MSE).

Architecture:
    Input (TF-IDF feature vector: d)
    -> Linear(d, 64) -> ReLU -> Dropout
    -> Linear(64, 24) -> ReLU (Bottleneck Latent Space)
    -> Linear(24, 64) -> ReLU
    -> Linear(64, d) -> Sigmoid / Linear (Reconstructed Output)
"""

import os
import json
import pickle
from typing import Dict, Any, Optional, List, Tuple
import numpy as np
import torch
import torch.nn as nn
from sklearn.feature_extraction.text import TfidfVectorizer

from .preprocessing import clean_text


class ProjectAutoencoder(nn.Module):
    """Deep autoencoder network compressing sparse TF-IDF vectors into bottleneck latent space."""

    def __init__(self, input_dim: int, hidden_dim: int = 64, latent_dim: int = 24, dropout: float = 0.1):
        super().__init__()
        # Encoder
        self.encoder = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, latent_dim),
            nn.ReLU(),
        )
        # Decoder
        self.decoder = nn.Sequential(
            nn.Linear(latent_dim, hidden_dim),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(hidden_dim, input_dim),
            nn.Sigmoid(),  # TF-IDF normalized features are bounded [0, 1]
        )

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        latent = self.encoder(x)
        reconstructed = self.decoder(latent)
        return reconstructed

    def encode(self, x: torch.Tensor) -> torch.Tensor:
        return self.encoder(x)


class AutoencoderService:
    """Inference service computing reconstruction error and anomaly status."""

    def __init__(self, artifacts_dir: Optional[str] = None):
        if artifacts_dir is None:
            artifacts_dir = os.path.join(os.path.dirname(__file__), "artifacts")
        self.artifacts_dir = artifacts_dir
        self.model_path = os.path.join(artifacts_dir, "autoencoder_model.pt")
        self.vectorizer_path = os.path.join(artifacts_dir, "autoencoder_vectorizer.pkl")
        self.meta_path = os.path.join(artifacts_dir, "autoencoder_meta.json")

        self.model: Optional[ProjectAutoencoder] = None
        self.vectorizer: Optional[TfidfVectorizer] = None
        self.metadata: Dict[str, Any] = {}
        self.threshold: float = 0.05
        self._is_loaded: bool = False

    def load_artifacts(self) -> bool:
        if not (os.path.exists(self.model_path) and os.path.exists(self.vectorizer_path)):
            self._is_loaded = False
            return False

        try:
            with open(self.vectorizer_path, "rb") as f:
                self.vectorizer = pickle.load(f)

            if os.path.exists(self.meta_path):
                with open(self.meta_path, "r", encoding="utf-8") as f:
                    self.metadata = json.load(f)
                    self.threshold = self.metadata.get("anomaly_threshold", 0.05)

            input_dim = len(self.vectorizer.get_feature_names_out())
            hidden_dim = self.metadata.get("hidden_dim", 64)
            latent_dim = self.metadata.get("latent_dim", 24)

            self.model = ProjectAutoencoder(input_dim=input_dim, hidden_dim=hidden_dim, latent_dim=latent_dim)
            state_dict = torch.load(self.model_path, map_location=torch.device("cpu"))
            self.model.load_state_dict(state_dict)
            self.model.eval()
            self._is_loaded = True
            return True
        except Exception:
            self._is_loaded = False
            self.model = None
            return False

    def is_ready(self) -> bool:
        if not self._is_loaded:
            return self.load_artifacts()
        return True

    def evaluate_novelty(self, text: str) -> Dict[str, Any]:
        """
        Compute reconstruction error (MSE) on input project text.
        Returns anomaly_score, is_unusual flag, threshold, and academic interpretation.
        """
        if not text or not clean_text(text):
            return {
                "status": "invalid_input",
                "reconstruction_error": None,
                "is_unusual": False,
                "anomaly_score": 0.0,
                "interpretation": "Empty or invalid input text.",
            }

        if not self.is_ready():
            return {
                "status": "model_not_trained",
                "reconstruction_error": None,
                "is_unusual": False,
                "anomaly_score": 0.0,
                "interpretation": "Autoencoder model artifacts not found. Model not trained.",
            }

        # Vectorize
        x_vec = self.vectorizer.transform([text]).toarray()
        vector_norm = float(np.linalg.norm(x_vec))
        num_known_terms = int(np.count_nonzero(x_vec))

        x_tensor = torch.tensor(x_vec, dtype=torch.float32)

        with torch.no_grad():
            reconstructed = self.model(x_tensor)
            # Mean Squared Error across feature dimensions
            mse = nn.functional.mse_loss(reconstructed, x_tensor).item()

        # Handle zero-vector / completely unfamiliar vocabulary condition
        is_zero_vector = (vector_norm == 0.0 or num_known_terms == 0)

        if is_zero_vector:
            is_unusual = True
            interpretation = (
                "Experimental Novelty Signal: All non-stopword tokens in this proposal fall outside the "
                "training vocabulary (zero vector input). Because the vocabulary is completely unfamiliar "
                "relative to historical projects, this proposal is flagged as an experimental pattern outlier. "
                "Note: Novelty reflects unconventional vocabulary/originality, NOT duplicate submission."
            )
            anomaly_ratio = 2.0  # Normalized indicator for completely unfamiliar vocabulary
        else:
            is_unusual = bool(mse > self.threshold)
            anomaly_ratio = round(mse / (self.threshold or 1e-5), 2)
            if is_unusual:
                interpretation = (
                    f"Experimental Novelty Signal: Unusual proposal pattern detected (MSE={mse:.5f} > threshold {self.threshold:.5f}). "
                    "The proposal contains vocabulary combinations that differ from the learned training distribution. "
                    "Note: This signal is for faculty review of topic originality, NOT duplicate detection."
                )
            else:
                interpretation = (
                    f"Experimental Novelty Signal: Standard proposal pattern (MSE={mse:.5f} <= threshold {self.threshold:.5f}). "
                    "The proposal vocabulary aligns with typical academic project patterns in the training corpus."
                )

        return {
            "status": "success",
            "model_type": "PyTorch Dense Autoencoder (MSE)",
            "reconstruction_error": round(mse, 6),
            "threshold": round(self.threshold, 6),
            "anomaly_ratio": anomaly_ratio,
            "is_unusual": is_unusual,
            "is_unfamiliar_vocabulary": is_zero_vector,
            "known_vocabulary_terms_count": num_known_terms,
            "interpretation": interpretation,
        }
