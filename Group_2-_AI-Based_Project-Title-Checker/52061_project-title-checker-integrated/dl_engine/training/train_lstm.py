"""
Training Script for Unit IV: LSTM Domain Classifier
===================================================
Constructs a benchmark academic project dataset across 7 domains using
curated title + description proposals, trains the PyTorch Bidirectional LSTM model,
evaluates against a TF-IDF + Logistic Regression baseline on a held-out test split,
and persists model weights, vocabulary, and evaluation metadata.

SAFETY & INTEGRITY RULES:
- Stratified Train (70%), Validation (15%), and Held-out Test (15%) splits.
- Zero data leakage: Vocabulary is built strictly on the training split.
- Word dropout regularization: Randomly replaces training tokens with <unk>
  to prevent untrained OOV bias.
- Full baseline comparison against Logistic Regression.
"""

import os
import json
import random
from typing import Dict, Any, List, Tuple
import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, f1_score, accuracy_score, confusion_matrix

from dl_engine.preprocessing import (
    Vocabulary,
    PROJECT_DOMAINS,
    DOMAIN_TO_IDX,
    IDX_TO_DOMAIN,
    UNK_IDX,
    PAD_IDX,
    clean_text,
    tokenize,
)
from dl_engine.lstm_classifier import ProjectDomainLSTM
from dl_engine.training.data import ACADEMIC_PROPOSALS

# Set reproducible seeds
SEED = 42
random.seed(SEED)
np.random.seed(SEED)
torch.manual_seed(SEED)


class ProposalDataset(Dataset):
    """PyTorch Dataset for (text, label) with optional training word dropout to <unk>."""

    def __init__(self, samples: List[Tuple[str, int]], vocab: Vocabulary, max_len: int = 64, unk_dropout: float = 0.0):
        self.data = []
        for text, label in samples:
            tokens = tokenize(text)
            if unk_dropout > 0:
                # Randomly drop tokens to <unk> with probability unk_dropout to regularize OOV embedding
                corrupted = []
                for t in tokens:
                    if random.random() < unk_dropout:
                        corrupted.append(UNK_IDX)
                    else:
                        corrupted.append(vocab.word2idx.get(t, UNK_IDX))
                indices = corrupted
            else:
                indices = [vocab.word2idx.get(t, UNK_IDX) for t in tokens]

            if len(indices) < max_len:
                indices = indices + [PAD_IDX] * (max_len - len(indices))
            else:
                indices = indices[:max_len]

            self.data.append((torch.tensor(indices, dtype=torch.long), torch.tensor(label, dtype=torch.long)))

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        return self.data[idx]


def split_data(
    proposals: List[Tuple[str, str, str]],
    train_ratio: float = 0.70,
    val_ratio: float = 0.15,
) -> Tuple[List[Tuple[str, int]], List[Tuple[str, int]], List[Tuple[str, int]]]:
    """
    Perform stratified train / val / test split per domain without leakage.
    Returns (train_samples, val_samples, test_samples) where each sample is (full_text, label_idx).
    """
    by_domain: Dict[str, List[Tuple[str, int]]] = {d: [] for d in PROJECT_DOMAINS}

    for title, desc, domain in proposals:
        full_text = f"{title}. {desc}".strip()
        label_idx = DOMAIN_TO_IDX[domain]
        by_domain[domain].append((full_text, label_idx))

    train_samples = []
    val_samples = []
    test_samples = []

    for domain, items in by_domain.items():
        # Deterministic shuffle per class
        shuffled = items.copy()
        random.Random(SEED).shuffle(shuffled)
        n = len(shuffled)
        n_train = int(n * train_ratio)
        n_val = int(n * val_ratio)

        train_samples.extend(shuffled[:n_train])
        val_samples.extend(shuffled[n_train:n_train + n_val])
        test_samples.extend(shuffled[n_train + n_val:])

    return train_samples, val_samples, test_samples


def train_lstm_pipeline(
    artifacts_dir: str = None,
    epochs: int = 40,
    batch_size: int = 16,
    lr: float = 0.003,
    max_len: int = 64,
    embedding_dim: int = 64,
    hidden_dim: int = 64,
    unk_dropout: float = 0.12,
) -> Dict[str, Any]:
    if artifacts_dir is None:
        artifacts_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "artifacts")
    os.makedirs(artifacts_dir, exist_ok=True)

    # 1. Stratified Splits
    train_samples, val_samples, test_samples = split_data(ACADEMIC_PROPOSALS)
    print(f"Dataset Split: Train={len(train_samples)}, Val={len(val_samples)}, Test={len(test_samples)} (Total={len(ACADEMIC_PROPOSALS)})")

    # 2. Build Vocabulary strictly on Training Split
    vocab = Vocabulary(min_freq=1)
    vocab.build_vocab([text for text, _ in train_samples])
    print(f"Vocabulary built strictly from training split: {len(vocab)} unique tokens")

    # 3. Create Datasets and DataLoaders
    train_ds = ProposalDataset(train_samples, vocab, max_len=max_len, unk_dropout=unk_dropout)
    val_ds = ProposalDataset(val_samples, vocab, max_len=max_len, unk_dropout=0.0)
    test_ds = ProposalDataset(test_samples, vocab, max_len=max_len, unk_dropout=0.0)

    train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True)
    val_loader = DataLoader(val_ds, batch_size=batch_size, shuffle=False)
    test_loader = DataLoader(test_ds, batch_size=batch_size, shuffle=False)

    # 4. Initialize LSTM Model
    model = ProjectDomainLSTM(
        vocab_size=len(vocab),
        embedding_dim=embedding_dim,
        hidden_dim=hidden_dim,
        output_dim=len(PROJECT_DOMAINS),
        bidirectional=True,
        dropout=0.3,
        pad_idx=PAD_IDX,
    )
    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.AdamW(model.parameters(), lr=lr, weight_decay=1e-4)

    best_val_f1 = -1.0
    best_state_dict = None

    # 5. Training Loop with Model Checkpointing on Validation Macro-F1
    for epoch in range(1, epochs + 1):
        model.train()
        train_loss = 0.0
        for seqs, labels in train_loader:
            optimizer.zero_grad()
            logits = model(seqs)
            loss = criterion(logits, labels)
            loss.backward()
            optimizer.step()
            train_loss += loss.item()

        # Validation step
        model.eval()
        val_true, val_preds = [], []
        with torch.no_grad():
            for seqs, labels in val_loader:
                logits = model(seqs)
                preds = torch.argmax(logits, dim=1)
                val_true.extend(labels.tolist())
                val_preds.extend(preds.tolist())

        val_acc = accuracy_score(val_true, val_preds)
        val_macro_f1 = f1_score(val_true, val_preds, average="macro", zero_division=0)

        if val_macro_f1 > best_val_f1:
            best_val_f1 = val_macro_f1
            best_state_dict = model.state_dict().copy()

    # Load best checkpoint
    if best_state_dict is not None:
        model.load_state_dict(best_state_dict)
    model.eval()

    # 6. Evaluate LSTM on Held-out Test Set
    test_true, test_preds, test_probs = [], [], []
    with torch.no_grad():
        for seqs, labels in test_loader:
            logits = model(seqs)
            probs = torch.softmax(logits, dim=1)
            preds = torch.argmax(logits, dim=1)
            test_true.extend(labels.tolist())
            test_preds.extend(preds.tolist())
            test_probs.extend(probs.tolist())

    lstm_test_acc = accuracy_score(test_true, test_preds)
    lstm_test_macro_f1 = f1_score(test_true, test_preds, average="macro", zero_division=0)
    lstm_cm = confusion_matrix(test_true, test_preds).tolist()
    lstm_report = classification_report(
        test_true, test_preds, target_names=PROJECT_DOMAINS, output_dict=True, zero_division=0
    )

    # 7. Evaluate Baseline: TF-IDF + Logistic Regression on the identical splits
    tfidf = TfidfVectorizer(ngram_range=(1, 2), max_features=1000)
    X_train_tfidf = tfidf.fit_transform([clean_text(t) for t, _ in train_samples])
    y_train = [l for _, l in train_samples]

    X_test_tfidf = tfidf.transform([clean_text(t) for t, _ in test_samples])
    baseline_clf = LogisticRegression(C=1.0, max_iter=200, random_state=SEED)
    baseline_clf.fit(X_train_tfidf, y_train)

    base_preds = baseline_clf.predict(X_test_tfidf)
    base_test_acc = accuracy_score(test_true, base_preds)
    base_test_macro_f1 = f1_score(test_true, base_preds, average="macro", zero_division=0)
    base_cm = confusion_matrix(test_true, base_preds).tolist()
    base_report = classification_report(
        test_true, base_preds, target_names=PROJECT_DOMAINS, output_dict=True, zero_division=0
    )

    print("\n" + "=" * 65)
    print("  MODEL EVALUATION ON STRICT HELD-OUT TEST SPLIT (28 SAMPLES)")
    print("=" * 65)
    print(f"BiLSTM Test Accuracy:       {lstm_test_acc * 100:.2f}% | Macro F1: {lstm_test_macro_f1:.4f}")
    print(f"Logistic Reg Test Accuracy: {base_test_acc * 100:.2f}% | Macro F1: {base_test_macro_f1:.4f}")

    print("\nBiLSTM Classification Report (Held-Out Test Set):")
    print(classification_report(test_true, test_preds, target_names=PROJECT_DOMAINS, zero_division=0))

    # 8. Unseen Case Check: Crop Yield Prediction
    test_crop_text = "AI-Based Crop Yield Prediction. Predict crop production using soil type, rainfall, temperature, humidity, fertilizer usage, and historical crop yield data."
    crop_seq = vocab.encode(test_crop_text, max_len=max_len)
    with torch.no_grad():
        crop_logits = model(torch.tensor([crop_seq], dtype=torch.long))
        crop_probs = torch.softmax(crop_logits, dim=1).squeeze(0)
    top_p, top_i = torch.max(crop_probs, dim=0)
    predicted_crop_domain = IDX_TO_DOMAIN[int(top_i)]
    print(f"\n[Required Test Case Validation]: '{test_crop_text[:40]}...'")
    print(f"  Predicted Domain: {predicted_crop_domain} (Confidence: {float(top_p)*100:.1f}%)")

    # 9. Verify <unk> Regularization (Pure UNK sequence should yield neutral, flat probabilities)
    unk_seq = [UNK_IDX] * max_len
    with torch.no_grad():
        unk_logits = model(torch.tensor([unk_seq], dtype=torch.long))
        unk_probs = torch.softmax(unk_logits, dim=1).squeeze(0)
    print("\n[UNK Regularization Check (Neutral Probabilities)]:")
    for d_idx, d_name in enumerate(PROJECT_DOMAINS):
        print(f"  {d_name:18s}: {float(unk_probs[d_idx])*100:.1f}%")

    # 10. Persist Trained Artifacts
    model_path = os.path.join(artifacts_dir, "lstm_model.pt")
    vocab_path = os.path.join(artifacts_dir, "lstm_vocab.json")
    meta_path = os.path.join(artifacts_dir, "lstm_meta.json")
    baseline_clf_path = os.path.join(artifacts_dir, "baseline_classifier.pkl")
    baseline_tfidf_path = os.path.join(artifacts_dir, "baseline_vectorizer.pkl")

    torch.save(model.state_dict(), model_path)
    with open(vocab_path, "w", encoding="utf-8") as f:
        json.dump(vocab.to_dict(), f, indent=2)

    import joblib
    joblib.dump(baseline_clf, baseline_clf_path)
    joblib.dump(tfidf, baseline_tfidf_path)

    metadata = {
        "model_type": "PyTorch Bidirectional LSTM (Masked Mean Pooling)",
        "epochs": epochs,
        "max_len": max_len,
        "embedding_dim": embedding_dim,
        "hidden_dim": hidden_dim,
        "bidirectional": True,
        "vocab_size": len(vocab),
        "dataset_info": {
            "dataset_provenance": "182 curated illustrative academic proposal benchmarks across 7 domains (26 per domain).",
            "provenance_note": "Synthetic/manually curated development dataset for syllabus integration and experimental evaluation. Does not represent production real-world accuracy.",
            "train_size": len(train_samples),
            "val_size": len(val_samples),
            "test_size": len(test_samples),
        },
        "lstm_metrics": {
            "test_accuracy": round(lstm_test_acc, 4),
            "test_macro_f1": round(lstm_test_macro_f1, 4),
            "confusion_matrix": lstm_cm,
            "classification_report": lstm_report,
        },
        "baseline_metrics": {
            "model": "TF-IDF (1-2 ngrams) + Logistic Regression (C=1.0)",
            "test_accuracy": round(base_test_acc, 4),
            "test_macro_f1": round(base_test_macro_f1, 4),
            "confusion_matrix": base_cm,
            "classification_report": base_report,
        },
        "domains": PROJECT_DOMAINS,
        "crop_yield_test_case": {
            "input": test_crop_text,
            "predicted_domain": predicted_crop_domain,
            "confidence": round(float(top_p), 4),
            "success": predicted_crop_domain == "Agriculture",
        },
    }

    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    return metadata


if __name__ == "__main__":
    train_lstm_pipeline()
