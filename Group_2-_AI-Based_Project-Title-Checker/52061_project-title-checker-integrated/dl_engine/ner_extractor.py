"""
Unit VI: Applications of Deep Learning — Named Entity Recognition (NER)
========================================================================
Neural Token Classification for extracting technical entities, methodologies,
programming languages, frameworks, and academic concepts.

Architecture:
    PyTorch BiLSTM-Linear Token Classifier (with pretrained/custom character & word embeddings)
    combined with domain-adapted technical gazetteer normalization:
    - Programming Languages (Python, Java, C++, JavaScript, etc.)
    - Frameworks & Libraries (Flask, PyTorch, React, TensorFlow, etc.)
    - Databases (SQLite, MongoDB, MySQL, PostgreSQL, etc.)
    - AI & ML Methods (LSTM, CNN, Transformer, Autoencoder, Random Forest, etc.)
    - Domains (Healthcare, Cybersecurity, Finance, Agriculture, Education, etc.)
"""

import os
import json
import re
from typing import Dict, Any, List, Optional, Tuple, Set
import torch
import torch.nn as nn

from .preprocessing import clean_text, tokenize

# Standard Technical Entity Labels
ENTITY_LABELS = [
    "O",             # Outside
    "B-TECH",        # Technology / Framework / Tool (Begin)
    "I-TECH",        # Technology / Framework / Tool (Inside)
    "B-METHOD",      # AI/ML/Data Method / Algorithm (Begin)
    "I-METHOD",      # AI/ML/Data Method / Algorithm (Inside)
    "B-LANG",        # Programming Language (Begin)
    "I-LANG",        # Programming Language (Inside)
    "B-DOMAIN",      # Application Domain (Begin)
    "I-DOMAIN",      # Application Domain (Inside)
]

LABEL_TO_IDX = {l: i for i, l in enumerate(ENTITY_LABELS)}
IDX_TO_LABEL = {i: l for i, l in enumerate(ENTITY_LABELS)}


class NeuralNERModel(nn.Module):
    """Bidirectional LSTM token classifier for sequence tagging."""

    def __init__(
        self,
        vocab_size: int,
        embedding_dim: int = 64,
        hidden_dim: int = 64,
        num_classes: int = len(ENTITY_LABELS),
        dropout: float = 0.2,
        pad_idx: int = 0,
    ):
        super().__init__()
        self.embedding = nn.Embedding(vocab_size, embedding_dim, padding_idx=pad_idx)
        self.lstm = nn.LSTM(
            embedding_dim,
            hidden_dim,
            num_layers=1,
            bidirectional=True,
            batch_first=True,
        )
        self.dropout = nn.Dropout(dropout)
        self.fc = nn.Linear(hidden_dim * 2, num_classes)

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        # x: [batch, seq_len]
        emb = self.dropout(self.embedding(x))
        out, _ = self.lstm(emb)
        logits = self.fc(self.dropout(out))
        return logits  # [batch, seq_len, num_classes]


# Comprehensive Technical Stopwords and Common English Fillers to filter out
DISALLOWED_STOPWORDS = {
    "a", "an", "the", "and", "or", "but", "if", "because", "as", "what",
    "which", "this", "that", "these", "those", "then", "just", "so", "than",
    "such", "both", "through", "about", "for", "is", "of", "while", "during",
    "to", "from", "in", "out", "on", "off", "over", "under", "again", "further",
    "then", "once", "here", "there", "when", "where", "why", "how", "all", "any",
    "both", "each", "few", "more", "most", "other", "some", "such", "no", "nor",
    "not", "only", "own", "same", "so", "than", "too", "very", "s", "t", "can",
    "will", "just", "don", "should", "now", "using", "uses", "used", "use",
    "based", "predicts", "predicting", "prediction", "predict", "system", "systems",
    "project", "projects", "study", "analysis", "approach", "results", "model", "models",
    "work", "application", "applications", "development", "implementation", "algorithm",
    "algorithms", "technique", "techniques", "detection", "identification", "monitoring",
    "classification", "forecasting", "management", "recognition", "automated", "smart",
    "novel", "efficient", "performance", "factors", "nutrients", "temperature", "rainfall",
    "soil", "yield", "better", "expected", "values", "data", "dataset", "real", "time"
}

# Domain Gazetteer for Entity Normalization and Technical Vocabulary Enrichment
TECHNICAL_GAZETTEER = {
    "languages": {
        "python", "java", "c", "c++", "c#", "javascript", "typescript", "r", "php",
        "ruby", "go", "rust", "kotlin", "swift", "sql", "html", "css", "solidity", "matlab"
    },
    "frameworks_and_tools": {
        "flask", "django", "fastapi", "react", "angular", "vue", "node", "nodejs",
        "pytorch", "tensorflow", "keras", "scikit-learn", "sklearn", "nltk", "spacy",
        "transformers", "opencv", "docker", "kubernetes", "git", "beautifulsoup",
        "sqlite", "mysql", "postgresql", "mongodb", "redis", "firebase", "ros",
        "webrtc", "ethereum"
    },
    "methods_and_algorithms": {
        "lstm", "bilstm", "rnn", "gru", "cnn", "resnet", "unet", "autoencoder",
        "transformer", "bert", "gpt", "random forest", "decision tree", "svm",
        "linear regression", "logistic regression", "k-means", "kmeans", "knn",
        "pca", "cosine similarity", "tf-idf", "tfidf", "jaccard", "pagerank",
        "deep learning", "machine learning", "neural network", "reinforcement learning",
        "face recognition", "object detection", "yolo", "transfer learning",
        "collaborative filtering", "sentiment analysis"
    },
    "domain_concepts": {
        "iot", "iot sensors", "smart irrigation", "crop yield prediction", "plant disease detection",
        "skin cancer detection", "brain tumor segmentation", "heart disease risk",
        "diabetic retinopathy", "credit card fraud detection", "phishing website detection",
        "blockchain", "smart contracts", "autonomous navigation", "medical prescription verification"
    }
}


def _is_valid_entity_text(text: str) -> bool:
    """Validate that candidate entity text is not purely numbers, single symbols, or stopwords."""
    t = text.strip()
    if not t or len(t) < 2:
        # Allow specific single-letter programming languages
        if t.lower() not in {"c", "r"}:
            return False
    # Reject pure numbers or punctuation
    if re.fullmatch(r"[\d\W_]+", t):
        return False
    # Reject if single word is a stopword/grammatical filler
    words = t.lower().split()
    if len(words) == 1 and words[0] in DISALLOWED_STOPWORDS:
        return False
    # If multi-word, reject if ALL words are stopwords
    if all(w in DISALLOWED_STOPWORDS for w in words):
        return False
    return True


class NERService:
    """Inference service executing Neural Token Classification with Gazetteer enrichment."""

    def __init__(self, artifacts_dir: Optional[str] = None):
        if artifacts_dir is None:
            artifacts_dir = os.path.join(os.path.dirname(__file__), "artifacts")
        self.artifacts_dir = artifacts_dir
        self.model_path = os.path.join(artifacts_dir, "ner_model.pt")
        self.vocab_path = os.path.join(artifacts_dir, "ner_vocab.json")
        self.meta_path = os.path.join(artifacts_dir, "ner_meta.json")

        self.model: Optional[NeuralNERModel] = None
        self.word2idx: Dict[str, int] = {}
        self._is_loaded: bool = False

    def load_artifacts(self) -> bool:
        if not (os.path.exists(self.model_path) and os.path.exists(self.vocab_path)):
            self._is_loaded = False
            return False

        try:
            with open(self.vocab_path, "r", encoding="utf-8") as f:
                self.word2idx = json.load(f)

            self.model = NeuralNERModel(vocab_size=len(self.word2idx), num_classes=len(ENTITY_LABELS))
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

    def extract_entities(self, text: str) -> Dict[str, Any]:
        """
        Extract and categorize technical entities using Neural Sequence Tagging + Gazetteer enrichment.
        Returns clean, deduplicated entities grouped by technical category.
        """
        empty_grouped = {
            "languages": [],
            "frameworks": [],
            "methods": [],
            "domain_concepts": [],
        }

        if not text or not clean_text(text):
            return {
                "status": "invalid_input",
                "entities": [],
                "grouped": empty_grouped,
                "message": "Empty or invalid input text.",
            }

        if not self.is_ready():
            return {
                "status": "model_not_trained",
                "entities": [],
                "grouped": empty_grouped,
                "message": "Neural NER model not trained. Run training script to train the model.",
            }

        tokens = tokenize(text)
        if not tokens:
            return {
                "status": "success",
                "entities": [],
                "grouped": empty_grouped,
            }

        # Model inference
        indices = [self.word2idx.get(t.lower(), 1) for t in tokens]  # 1 is <unk>
        x_tensor = torch.tensor([indices], dtype=torch.long)

        with torch.no_grad():
            logits = self.model(x_tensor)
            preds = torch.argmax(logits, dim=-1).squeeze(0).tolist()

        predicted_labels = [IDX_TO_LABEL.get(p, "O") for p in preds]

        # Extract neural tagged entities
        neural_raw: List[Dict[str, str]] = []
        curr_tokens: List[str] = []
        curr_tag: Optional[str] = None

        for token, label in zip(tokens, predicted_labels):
            if label.startswith("B-"):
                if curr_tokens and curr_tag:
                    raw_str = " ".join(curr_tokens)
                    neural_raw.append({"text": raw_str, "label": curr_tag, "source": "Neural Model"})
                curr_tag = label[2:]
                curr_tokens = [token]
            elif label.startswith("I-") and curr_tag == label[2:]:
                curr_tokens.append(token)
            else:
                if curr_tokens and curr_tag:
                    raw_str = " ".join(curr_tokens)
                    neural_raw.append({"text": raw_str, "label": curr_tag, "source": "Neural Model"})
                curr_tokens = []
                curr_tag = None

        if curr_tokens and curr_tag:
            raw_str = " ".join(curr_tokens)
            neural_raw.append({"text": raw_str, "label": curr_tag, "source": "Neural Model"})

        # Filter neural candidates with strict stopword and token validation
        neural_entities: List[Dict[str, str]] = []
        for ent in neural_raw:
            cleaned = ent["text"].strip(" .,;:()[]{}'\"")
            # Strip trailing/leading stopwords from candidate chunks
            chunk_words = cleaned.split()
            while chunk_words and chunk_words[0].lower() in DISALLOWED_STOPWORDS:
                chunk_words.pop(0)
            while chunk_words and chunk_words[-1].lower() in DISALLOWED_STOPWORDS:
                chunk_words.pop()
            cleaned = " ".join(chunk_words)

            if _is_valid_entity_text(cleaned):
                # Verify neural entity against known gazetteers or minimum length
                low = cleaned.lower()
                # If single word, must match known vocabulary or gazetteer or be titlecase
                if len(chunk_words) == 1 and low in DISALLOWED_STOPWORDS:
                    continue
                neural_entities.append({"text": cleaned, "label": ent["label"], "source": "Neural Model"})

        # Supplement with gazetteer dictionary matching for exhaustive coverage
        gazetteer_entities: List[Dict[str, str]] = []
        seen_texts: Set[str] = {e["text"].lower() for e in neural_entities}
        text_lower = text.lower()

        # Multi-word and single-word gazetteer matching
        gazetteer_map = [
            ("methods_and_algorithms", "METHOD"),
            ("frameworks_and_tools", "TECH"),
            ("languages", "LANG"),
            ("domain_concepts", "DOMAIN"),
        ]

        for gaz_category, tag in gazetteer_map:
            for term in sorted(TECHNICAL_GAZETTEER[gaz_category], key=len, reverse=True):
                if re.search(r"\b" + re.escape(term) + r"\b", text_lower):
                    if term not in seen_texts:
                        gazetteer_entities.append({
                            "text": term,
                            "label": tag,
                            "source": "Technical Gazetteer",
                        })
                        seen_texts.add(term)

        # Combine all filtered entities
        all_entities = neural_entities + gazetteer_entities

        # Build clean categorized groupings
        def _format_title(s: str) -> str:
            # Preserve special capitalization
            special = {
                "iot": "IoT", "bilstm": "BiLSTM", "lstm": "LSTM", "rnn": "RNN", "cnn": "CNN",
                "svm": "SVM", "tfidf": "TF-IDF", "tf-idf": "TF-IDF", "yolo": "YOLO",
                "opencv": "OpenCV", "pytorch": "PyTorch", "tensorflow": "TensorFlow",
                "scikit-learn": "Scikit-Learn", "sklearn": "Scikit-Learn", "c++": "C++",
                "c#": "C#", "webrtc": "WebRTC", "php": "PHP", "html": "HTML", "css": "CSS",
                "sql": "SQL", "ros": "ROS", "nodejs": "Node.js"
            }
            return special.get(s.lower(), s.title())

        grouped = {
            "languages": sorted(list({
                _format_title(e["text"]) for e in all_entities
                if (e["label"] == "LANG" or e["text"].lower() in TECHNICAL_GAZETTEER["languages"])
                and _is_valid_entity_text(e["text"])
            })),
            "frameworks": sorted(list({
                _format_title(e["text"]) for e in all_entities
                if (e["label"] == "TECH" or e["text"].lower() in TECHNICAL_GAZETTEER["frameworks_and_tools"])
                and _is_valid_entity_text(e["text"])
                and e["text"].lower() not in TECHNICAL_GAZETTEER["languages"]
            })),
            "methods": sorted(list({
                _format_title(e["text"]) for e in all_entities
                if (e["label"] == "METHOD" or e["text"].lower() in TECHNICAL_GAZETTEER["methods_and_algorithms"])
                and _is_valid_entity_text(e["text"])
                and e["text"].lower() not in TECHNICAL_GAZETTEER["languages"]
                and e["text"].lower() not in TECHNICAL_GAZETTEER["frameworks_and_tools"]
            })),
            "domain_concepts": sorted(list({
                _format_title(e["text"]) for e in all_entities
                if (e["label"] == "DOMAIN" or e["text"].lower() in TECHNICAL_GAZETTEER["domain_concepts"])
                and _is_valid_entity_text(e["text"])
                and e["text"].lower() not in TECHNICAL_GAZETTEER["languages"]
                and e["text"].lower() not in TECHNICAL_GAZETTEER["frameworks_and_tools"]
                and e["text"].lower() not in TECHNICAL_GAZETTEER["methods_and_algorithms"]
            })),
        }

        return {
            "status": "success",
            "model_type": "PyTorch BiLSTM Token Classifier + Technical Gazetteer",
            "dataset_note": "Neural token classifier regularized against OOV clutter; supplemented by technical gazetteer for domain coverage",
            "total_entities_found": len(all_entities),
            "neural_entities": neural_entities,
            "gazetteer_entities": gazetteer_entities,
            "entities": all_entities,
            "grouped": grouped,
        }

