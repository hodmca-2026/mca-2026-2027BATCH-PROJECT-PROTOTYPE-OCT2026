"""
Deep Learning Engine Package Interface
=======================================
Integrates the three Deep Learning syllabus models:
1. Unit IV: LSTM Sequence Domain Classifier (ProjectDomainLSTM)
2. Unit V: Autoencoder Anomaly Detector (ProjectAutoencoder)
3. Unit VI: Neural NER Token Classifier & Gazetteer (NeuralNERModel)

Provides unified analysis for student proposal submission and faculty review.
"""

from typing import Dict, Any, Optional

from .lstm_classifier import LSTMClassifierService
from .autoencoder import AutoencoderService
from .ner_extractor import NERService

# Global service singletons
lstm_service = LSTMClassifierService()
autoencoder_service = AutoencoderService()
ner_service = NERService()


def analyze_proposal(title: str, description: Optional[str] = None) -> Dict[str, Any]:
    """
    Run the unified Deep Learning pipeline on a student project proposal.
    Takes title and optional abstract/description, combines them for analysis,
    and returns domain classification, anomaly novelty score, and technical entities.
    """
    full_text = f"{title} {description}".strip() if description else (title or "").strip()

    domain_result = lstm_service.predict(full_text)
    novelty_result = autoencoder_service.evaluate_novelty(full_text)
    entities_result = ner_service.extract_entities(full_text)

    return {
        "status": "success",
        "domain_classification": domain_result,
        "novelty_analysis": novelty_result,
        "named_entities": entities_result,
    }
