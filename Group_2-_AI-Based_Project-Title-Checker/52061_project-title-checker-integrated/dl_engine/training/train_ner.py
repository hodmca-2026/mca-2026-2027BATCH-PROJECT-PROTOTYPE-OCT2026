"""
Training script for Unit VI: Neural Named Entity Recognition (Token Classifier)
==============================================================================
Trains a PyTorch Bidirectional LSTM token classification model on annotated
computer science and academic project tokens.
Saves model weights, vocabulary, and metadata.
"""

import os
import json
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader

from dl_engine.preprocessing import tokenize
from dl_engine.ner_extractor import NeuralNERModel, ENTITY_LABELS, LABEL_TO_IDX

# Annotated token sequence training dataset for technical project descriptions
# 30 illustrative annotated academic sequences covering diverse technical concepts
NER_ANNOTATED_DATA = [
    ("Build a web application using Flask and Python for Healthcare diagnosis",
     ["O", "O", "O", "O", "O", "B-TECH", "O", "B-LANG", "O", "B-DOMAIN", "O"]),

    ("Deep Learning model with PyTorch and LSTM for text classification",
     ["B-METHOD", "I-METHOD", "O", "O", "B-TECH", "O", "B-METHOD", "O", "O", "B-METHOD"]),

    ("Attendance management system using OpenCV and Face Recognition in Python",
     ["O", "O", "O", "O", "B-TECH", "O", "B-METHOD", "I-METHOD", "O", "B-LANG"]),

    ("Skin Cancer Detection Using CNN and Transfer Learning in PyTorch",
     ["B-DOMAIN", "I-DOMAIN", "O", "O", "B-METHOD", "O", "B-METHOD", "I-METHOD", "O", "B-TECH"]),

    ("Credit Card Fraud Detection System Using Random Forest and SQLite",
     ["B-DOMAIN", "I-DOMAIN", "I-DOMAIN", "O", "O", "O", "B-METHOD", "I-METHOD", "O", "B-TECH"]),

    ("Movie Recommendation System Using Collaborative Filtering with React frontend",
     ["B-DOMAIN", "I-DOMAIN", "O", "O", "B-METHOD", "I-METHOD", "O", "B-TECH", "O"]),

    ("Phishing Website Detection Using Random Forest and JavaScript",
     ["B-DOMAIN", "I-DOMAIN", "O", "O", "B-METHOD", "I-METHOD", "O", "B-LANG"]),

    ("Smart Irrigation System with IoT Sensors and Weather Forecasting in Python",
     ["B-DOMAIN", "I-DOMAIN", "O", "O", "B-TECH", "O", "O", "O", "O", "B-LANG"]),

    ("Network Intrusion Detection System Using Deep Autoencoders and Packet Sniffing",
     ["B-DOMAIN", "I-DOMAIN", "O", "O", "O", "B-METHOD", "I-METHOD", "O", "O", "O"]),

    ("Autonomous Robot Navigation using Reinforcement Learning and ROS in C++",
     ["B-DOMAIN", "I-DOMAIN", "O", "O", "B-METHOD", "I-METHOD", "O", "B-TECH", "O", "B-LANG"]),

    ("Crop Yield Prediction Based on Weather and Soil Nutrients in Agriculture",
     ["B-DOMAIN", "I-DOMAIN", "O", "O", "O", "O", "O", "O", "O", "B-DOMAIN"]),

    ("Predicts crop yield using Random Forest and Linear Regression algorithms in Python",
     ["O", "O", "O", "O", "B-METHOD", "I-METHOD", "O", "B-METHOD", "I-METHOD", "O", "O", "B-LANG"]),

    ("Stock Price Forecasting Using BiLSTM and Sentiment Analysis in PyTorch",
     ["B-DOMAIN", "I-DOMAIN", "O", "O", "B-METHOD", "O", "B-METHOD", "I-METHOD", "O", "B-TECH"]),

    ("Decentralized Voting System with Ethereum Smart Contracts and Solidity",
     ["B-DOMAIN", "I-DOMAIN", "O", "O", "B-TECH", "O", "O", "O", "B-LANG"]),

    ("Automated Brain Tumor Segmentation from MRI Images Using UNet in TensorFlow",
     ["O", "B-DOMAIN", "I-DOMAIN", "O", "O", "O", "O", "O", "B-METHOD", "O", "B-TECH"]),

    ("Fake News Detection on Social Media Using BERT and Logistic Regression",
     ["B-DOMAIN", "I-DOMAIN", "O", "O", "O", "O", "B-METHOD", "O", "B-METHOD", "I-METHOD"]),

    ("E-commerce Customer Segmentation Using KMeans Clustering and MongoDB",
     ["B-DOMAIN", "O", "O", "O", "B-METHOD", "I-METHOD", "O", "B-TECH"]),

    ("Object Detection and Tracking in Real Time Video Using YOLO and OpenCV",
     ["B-METHOD", "I-METHOD", "O", "O", "O", "O", "O", "O", "B-METHOD", "O", "B-TECH"]),

    ("Traffic Sign Recognition System Using ResNet Convolutional Neural Network in Keras",
     ["B-DOMAIN", "I-DOMAIN", "O", "O", "O", "B-METHOD", "I-METHOD", "I-METHOD", "I-METHOD", "O", "B-TECH"]),

    ("Student Academic Performance Prediction Using Decision Tree Classifiers in Scikit-Learn",
     ["B-DOMAIN", "I-DOMAIN", "I-DOMAIN", "O", "O", "B-METHOD", "I-METHOD", "O", "O", "B-TECH"]),

    ("Cybersecurity Vulnerability Scanning and Penetration Testing Tool in Go",
     ["B-DOMAIN", "O", "O", "O", "O", "O", "O", "O", "B-LANG"]),

    ("Telemedicine Video Consultation Platform with WebRTC and Django Backend",
     ["B-DOMAIN", "O", "O", "O", "O", "B-TECH", "O", "B-TECH", "O"]),

    ("Microservices Architecture with Docker Kubernetes and PostgreSQL Database",
     ["O", "O", "O", "B-TECH", "B-TECH", "O", "B-TECH", "O"]),

    ("Natural Language Processing for Clinical Discharge Summary Extraction in Spacy",
     ["B-METHOD", "I-METHOD", "I-METHOD", "O", "B-DOMAIN", "O", "O", "O", "O", "B-TECH"]),

    ("Soil Moisture and Temperature Monitoring Using Raspberry Pi and Nodejs",
     ["O", "O", "O", "O", "O", "O", "B-TECH", "I-TECH", "O", "B-TECH"]),

    ("Heart Disease Risk Prediction System with Clinical Biomarkers in Healthcare",
     ["B-DOMAIN", "I-DOMAIN", "O", "O", "O", "O", "O", "O", "B-DOMAIN"]),

    ("Automated Medical Prescription Verification and Drug Interaction Checker in Healthcare",
     ["O", "O", "O", "O", "O", "O", "O", "O", "O", "B-DOMAIN"]),

    ("Continuous Glucose Monitoring Alert System for Type-1 Diabetic Patients",
     ["O", "O", "O", "O", "O", "O", "O", "B-DOMAIN", "O"]),

    ("Rice Blast Disease Severity Classification Using Deep Neural Networks in Agriculture",
     ["B-DOMAIN", "I-DOMAIN", "O", "O", "O", "O", "B-METHOD", "I-METHOD", "I-METHOD", "O", "B-DOMAIN"]),

    ("Greenhouse Climate Control System with IoT Sensors for Horticulture in Agriculture",
     ["B-DOMAIN", "I-DOMAIN", "O", "O", "O", "B-TECH", "O", "O", "O", "O", "B-DOMAIN"]),
]


class NERDataset(Dataset):
    def __init__(self, data, word2idx, unk_dropout=0.15):
        self.samples = []
        for text, labels in data:
            tokens = tokenize(text)
            min_len = min(len(tokens), len(labels))
            tokens = tokens[:min_len]
            labels = labels[:min_len]

            token_ids = [word2idx.get(t.lower(), 1) for t in tokens]
            label_ids = [LABEL_TO_IDX.get(l, 0) for l in labels]

            self.samples.append((
                torch.tensor(token_ids, dtype=torch.long),
                torch.tensor(label_ids, dtype=torch.long)
            ))
        self.unk_dropout = unk_dropout

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, idx):
        seq, lab = self.samples[idx]
        if self.unk_dropout > 0:
            # Word dropout: randomly replace non-entity tokens with <unk> (id 1)
            # so the model learns that unknown words default to 'O'
            mask = torch.rand(len(seq)) < self.unk_dropout
            # Only drop out tokens whose label is 'O' (label 0)
            is_outside = (lab == 0)
            seq = seq.clone()
            seq[mask & is_outside] = 1
        return seq, lab


def collate_fn(batch):
    max_len = max(len(x[0]) for x in batch)
    padded_seqs, padded_labels = [], []
    for seq, lab in batch:
        pad_size = max_len - len(seq)
        padded_seqs.append(torch.cat([seq, torch.zeros(pad_size, dtype=torch.long)]))
        padded_labels.append(torch.cat([lab, torch.zeros(pad_size, dtype=torch.long)]))
    return torch.stack(padded_seqs), torch.stack(padded_labels)


def train_ner_model(artifacts_dir=None, epochs=50, lr=0.005):
    if artifacts_dir is None:
        artifacts_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "artifacts")
    os.makedirs(artifacts_dir, exist_ok=True)

    # Build vocab
    word2idx = {"<pad>": 0, "<unk>": 1}
    for text, _ in NER_ANNOTATED_DATA:
        for t in tokenize(text):
            low = t.lower()
            if low not in word2idx:
                word2idx[low] = len(word2idx)

    # Add common English words to vocab with label 'O' exposure
    common_filler = [
        "is", "are", "was", "were", "this", "that", "these", "those", "from", "with",
        "into", "during", "before", "after", "above", "below", "to", "of", "in", "for",
        "on", "by", "about", "against", "between", "through", "such", "as", "than",
        "too", "very", "can", "will", "just", "should", "now", "data", "based", "system",
        "project", "using", "proposed", "study", "analysis", "approach", "results", "predicts"
    ]
    for w in common_filler:
        if w not in word2idx:
            word2idx[w] = len(word2idx)

    dataset = NERDataset(NER_ANNOTATED_DATA, word2idx, unk_dropout=0.20)
    loader = DataLoader(dataset, batch_size=4, shuffle=True, collate_fn=collate_fn)

    model = NeuralNERModel(vocab_size=len(word2idx), num_classes=len(ENTITY_LABELS))
    criterion = nn.CrossEntropyLoss(ignore_index=0)  # ignore padding token
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)

    model.train()
    for epoch in range(epochs):
        for seqs, labels in loader:
            optimizer.zero_grad()
            logits = model(seqs)  # [batch, seq_len, classes]
            loss = criterion(logits.view(-1, len(ENTITY_LABELS)), labels.view(-1))
            # Explicitly train <unk> (index 1) to predict 'O' (class 0)
            unk_logits = model(torch.tensor([[1]], dtype=torch.long))
            unk_loss = nn.CrossEntropyLoss()(unk_logits.view(-1, len(ENTITY_LABELS)), torch.tensor([0]))
            total_loss = loss + 0.5 * unk_loss
            total_loss.backward()
            optimizer.step()

    print(f"[Neural NER Training Complete] Vocab: {len(word2idx)}, Labels: {len(ENTITY_LABELS)}, Epochs: {epochs}")

    # Save artifacts
    model_path = os.path.join(artifacts_dir, "ner_model.pt")
    vocab_path = os.path.join(artifacts_dir, "ner_vocab.json")
    meta_path = os.path.join(artifacts_dir, "ner_meta.json")

    torch.save(model.state_dict(), model_path)
    with open(vocab_path, "w", encoding="utf-8") as f:
        json.dump(word2idx, f, indent=2)

    meta = {
        "model_type": "PyTorch BiLSTM Token Classifier",
        "vocab_size": len(word2idx),
        "num_classes": len(ENTITY_LABELS),
        "labels": ENTITY_LABELS,
        "epochs": epochs,
        "note": "Trained on 30 illustrative annotated academic sequences with word dropout for OOV regularization.",
    }
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2)

    return meta


if __name__ == "__main__":
    train_ner_model()
