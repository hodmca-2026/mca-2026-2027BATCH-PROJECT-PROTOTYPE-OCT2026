"""
Unit IV: Recurrent Neural Networks — LSTM Sequence Classifier
=============================================================
PyTorch LSTM architecture for academic project domain classification.
Supports text sequences up to max_len tokens and predicts probabilities
across predefined domains:
Healthcare, Education, Finance, Agriculture, Cybersecurity, Web Applications, Other.
"""

import os
import json
from typing import Dict, Any, Optional, List
import torch
import torch.nn as nn

from .preprocessing import (
    Vocabulary,
    PROJECT_DOMAINS,
    DOMAIN_TO_IDX,
    IDX_TO_DOMAIN,
    PAD_IDX,
    clean_text,
)


class ProjectDomainLSTM(nn.Module):
    """
    Bidirectional/Unidirectional LSTM for Project Domain Sequence Classification.
    Embedding -> LSTM -> Dropout -> Linear -> Logits.
    """

    def __init__(
        self,
        vocab_size: int,
        embedding_dim: int = 64,
        hidden_dim: int = 64,
        output_dim: int = len(PROJECT_DOMAINS),
        n_layers: int = 1,
        bidirectional: bool = True,
        dropout: float = 0.2,
        pad_idx: int = PAD_IDX,
    ):
        super().__init__()
        self.embedding = nn.Embedding(vocab_size, embedding_dim, padding_idx=pad_idx)
        self.lstm = nn.LSTM(
            embedding_dim,
            hidden_dim,
            num_layers=n_layers,
            bidirectional=bidirectional,
            dropout=dropout if n_layers > 1 else 0.0,
            batch_first=True,
        )
        lstm_out_dim = hidden_dim * 2 if bidirectional else hidden_dim
        self.dropout = nn.Dropout(dropout)
        self.fc = nn.Linear(lstm_out_dim, output_dim)

    def forward(self, text_seq: torch.Tensor) -> torch.Tensor:
        # text_seq shape: [batch_size, seq_len]
        mask = (text_seq != PAD_IDX).unsqueeze(-1)  # [batch_size, seq_len, 1]
        embedded = self.dropout(self.embedding(text_seq))
        # embedded shape: [batch_size, seq_len, embedding_dim]
        output, (hidden, cell) = self.lstm(embedded)
        # Use masked mean pooling across time dimension for stable document representation
        masked_output = output * mask.float()
        sum_output = masked_output.sum(dim=1)
        lengths = mask.sum(dim=1).clamp(min=1)
        pooled = sum_output / lengths
        logits = self.fc(self.dropout(pooled))
        return logits


class LSTMClassifierService:
    """Inference service with lazy loading, graceful fallback, and validation."""

    def __init__(self, artifacts_dir: Optional[str] = None):
        if artifacts_dir is None:
            artifacts_dir = os.path.join(os.path.dirname(__file__), "artifacts")
        self.artifacts_dir = artifacts_dir
        self.model_path = os.path.join(artifacts_dir, "lstm_model.pt")
        self.vocab_path = os.path.join(artifacts_dir, "lstm_vocab.json")
        self.meta_path = os.path.join(artifacts_dir, "lstm_meta.json")
        self.baseline_clf_path = os.path.join(artifacts_dir, "baseline_classifier.pkl")
        self.baseline_tfidf_path = os.path.join(artifacts_dir, "baseline_vectorizer.pkl")

        self.model: Optional[ProjectDomainLSTM] = None
        self.vocab: Optional[Vocabulary] = None
        self.baseline_clf = None
        self.baseline_tfidf = None
        self.metadata: Dict[str, Any] = {}
        self.max_len: int = 64
        self._is_loaded: bool = False

    def load_artifacts(self) -> bool:
        """Load trained BiLSTM weights, vocabulary, metadata, and primary baseline model."""
        if not (os.path.exists(self.model_path) and os.path.exists(self.vocab_path)):
            self._is_loaded = False
            return False

        try:
            with open(self.vocab_path, "r", encoding="utf-8") as f:
                vocab_dict = json.load(f)
            self.vocab = Vocabulary.from_dict(vocab_dict)

            if os.path.exists(self.meta_path):
                with open(self.meta_path, "r", encoding="utf-8") as f:
                    self.metadata = json.load(f)
                    self.max_len = self.metadata.get("max_len", 64)

            # Initialize LSTM model architecture
            embedding_dim = self.metadata.get("embedding_dim", 64)
            hidden_dim = self.metadata.get("hidden_dim", 64)
            bidirectional = self.metadata.get("bidirectional", True)

            self.model = ProjectDomainLSTM(
                vocab_size=len(self.vocab),
                embedding_dim=embedding_dim,
                hidden_dim=hidden_dim,
                output_dim=len(PROJECT_DOMAINS),
                bidirectional=bidirectional,
            )
            state_dict = torch.load(self.model_path, map_location=torch.device("cpu"))
            self.model.load_state_dict(state_dict)
            self.model.eval()

            # Load primary TF-IDF + Logistic Regression baseline model if available
            if os.path.exists(self.baseline_clf_path) and os.path.exists(self.baseline_tfidf_path):
                import joblib
                self.baseline_clf = joblib.load(self.baseline_clf_path)
                self.baseline_tfidf = joblib.load(self.baseline_tfidf_path)

            self._is_loaded = True
            return True
        except Exception as e:
            self._is_loaded = False
            self.model = None
            return False

    def is_ready(self) -> bool:
        if not self._is_loaded:
            return self.load_artifacts()
        return True

    def predict(self, text: str) -> Dict[str, Any]:
        """
        Predict project domain with calibrated uncertainty handling.
        Evaluates both the primary TF-IDF + Logistic Regression model (74.3% accuracy)
        and the experimental Unit IV BiLSTM model (42.9% accuracy).
        Flags 'Needs Faculty Review' whenever input is ambiguous, vague, or out-of-distribution.
        """
        if not text or not clean_text(text):
            return {
                "status": "invalid_input",
                "predicted_domain": None,
                "confidence": 0.0,
                "confidence_percent": 0.0,
                "probabilities": {},
                "is_uncertain": True,
                "decision_status": "Needs Faculty Review: Empty or Invalid Input",
                "message": "Input text is empty or contains no valid alphanumeric words.",
            }

        if not self.is_ready():
            return {
                "status": "model_not_trained",
                "predicted_domain": None,
                "confidence": 0.0,
                "confidence_percent": 0.0,
                "probabilities": {},
                "is_uncertain": True,
                "decision_status": "Needs Faculty Review: Model Not Trained",
                "message": "Model artifacts not found. Run training script to train models.",
            }

        # 1. Compute LSTM Sequence Model Prediction (Unit IV syllabus implementation)
        indices = self.vocab.encode(text, max_len=self.max_len)
        tensor_in = torch.tensor([indices], dtype=torch.long)

        with torch.no_grad():
            lstm_logits = self.model(tensor_in)
            lstm_probs = torch.softmax(lstm_logits, dim=1).squeeze(0)

        lstm_top_prob, lstm_top_idx = torch.max(lstm_probs, dim=0)
        lstm_domain = IDX_TO_DOMAIN.get(int(lstm_top_idx), "Other")
        lstm_confidence = round(float(lstm_top_prob), 4)

        lstm_sorted, _ = torch.sort(lstm_probs, descending=True)
        lstm_margin = round(float(lstm_sorted[0] - lstm_sorted[1]), 4)
        oov_rate = round(self.vocab.compute_oov_rate(text), 4)

        lstm_prob_dist = {
            IDX_TO_DOMAIN[i]: round(float(lstm_probs[i]), 4)
            for i in range(len(PROJECT_DOMAINS))
        }

        # 2. Compute Primary Baseline Prediction (TF-IDF + Logistic Regression)
        cleaned = clean_text(text)
        words = cleaned.split()
        word_count = len(words)

        if self.baseline_clf is not None and self.baseline_tfidf is not None:
            X_vec = self.baseline_tfidf.transform([cleaned])
            base_probs = self.baseline_clf.predict_proba(X_vec)[0]
            base_top_idx = int(base_probs.argmax())
            base_domain = IDX_TO_DOMAIN[base_top_idx]
            base_confidence = round(float(base_probs[base_top_idx]), 4)

            # Sort probabilities for margin calculation
            sorted_base = sorted(base_probs, reverse=True)
            base_margin = round(float(sorted_base[0] - sorted_base[1]), 4)

            # Vocabulary coverage: proportion of input tokens seen in reference vocabulary
            vocab_matches = sum(1 for w in words if w in self.baseline_tfidf.vocabulary_)
            vocab_coverage = round(vocab_matches / max(word_count, 1), 4)

            base_prob_dist = {
                IDX_TO_DOMAIN[i]: round(float(base_probs[i]), 4)
                for i in range(len(PROJECT_DOMAINS))
            }

            # Primary prediction selected from best-performing model (Baseline)
            primary_domain = base_domain
            primary_confidence = base_confidence
            primary_model_name = "TF-IDF + Logistic Regression (Primary, 74.3% test accuracy)"

            # Validation-calibrated uncertainty rule:
            # - Insufficient vocabulary overlap (vocab_coverage < 0.30)
            # - Ambiguous classification margin (base_margin < 0.020)
            # - Very short/vague titles without sufficient technical context (word_count <= 2)
            is_uncertain = (vocab_coverage < 0.30) or (base_margin < 0.020) or (word_count <= 2)
            uncertainty_reasons = []
            if word_count <= 2:
                uncertainty_reasons.append("very short proposal")
            if vocab_coverage < 0.30:
                uncertainty_reasons.append("unfamiliar or out-of-distribution vocabulary")
            if base_margin < 0.020:
                uncertainty_reasons.append("ambiguous cross-domain topic")

            margin_value = base_margin
            prob_dist = base_prob_dist
        else:
            # Fallback to LSTM if baseline artifact is absent
            primary_domain = lstm_domain
            primary_confidence = lstm_confidence
            primary_model_name = "PyTorch BiLSTM (42.9% test accuracy)"
            is_uncertain = (oov_rate > 0.50) or (lstm_margin < 0.15) or (word_count <= 2)
            uncertainty_reasons = ["experimental sequence model"]
            margin_value = lstm_margin
            prob_dist = lstm_prob_dist

        decision_status = (
            f"Needs Faculty Review ({', '.join(uncertainty_reasons)})"
            if is_uncertain
            else "Prediction Available"
        )

        return {
            "status": "success",
            "model_type": primary_model_name,
            "predicted_domain": primary_domain,
            "confidence": primary_confidence,
            "confidence_percent": round(primary_confidence * 100, 1),
            "is_uncertain": is_uncertain,
            "decision_status": decision_status,
            "oov_rate": oov_rate,
            "margin": margin_value,
            "probabilities": prob_dist,
            "lstm_domain": lstm_domain,
            "lstm_confidence_percent": round(lstm_confidence * 100, 1),
            "lstm_probabilities": lstm_prob_dist,
            "reliability_note": (
                f"Needs Faculty Review: input exhibits {', '.join(uncertainty_reasons)}."
                if is_uncertain
                else "Automated prediction provided for faculty advisory review; final domain approval remains with faculty."
            ),
        }

