"""
train.py
--------
CNN training pipeline for MRI brain tumor classification.

Dataset expected layout (Kaggle "Brain Tumor MRI Dataset", Masoud Nickparvar):

    ml/dataset/Training/{glioma,meningioma,notumor,pituitary}/*.jpg
    ml/dataset/Testing/{glioma,meningioma,notumor,pituitary}/*.jpg

This script:
  1. Loads the dataset with torchvision ImageFolder
  2. Splits the Training folder into train/validation (patient-level split is
     not applicable here since this public dataset has no patient IDs --
     documented as a known limitation, see docs/README.md)
  3. Applies data augmentation on the training split only
  4. Trains a CNN (transfer learning on ResNet18 by default, or a small
     custom CNN with --arch custom)
  5. Evaluates on the held-out Testing folder: accuracy, precision, recall,
     F1, confusion matrix, per-class sensitivity/specificity
  6. Saves the best model (by validation accuracy) to ml/models/best_model.pth
  7. Writes metrics to ml/models/metrics.json for the backend/dashboard to read

Usage:
    python train.py --epochs 15 --arch resnet18
"""
import argparse
import json
import os
import time
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, random_split
from torchvision import datasets, models, transforms
from sklearn.metrics import (
    accuracy_score, precision_recall_fscore_support, confusion_matrix
)

CLASSES = ["glioma", "meningioma", "notumor", "pituitary"]
IMG_SIZE = 224
DATA_DIR = Path(__file__).parent / "dataset"
MODEL_DIR = Path(__file__).parent / "models"
MODEL_DIR.mkdir(exist_ok=True)


def get_transforms():
    train_tf = transforms.Compose([
        transforms.Grayscale(num_output_channels=3),
        transforms.Resize((IMG_SIZE, IMG_SIZE)),
        transforms.RandomHorizontalFlip(p=0.3),
        transforms.RandomRotation(10),
        transforms.ColorJitter(brightness=0.15, contrast=0.15),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406],
                              std=[0.229, 0.224, 0.225]),
    ])
    eval_tf = transforms.Compose([
        transforms.Grayscale(num_output_channels=3),
        transforms.Resize((IMG_SIZE, IMG_SIZE)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406],
                              std=[0.229, 0.224, 0.225]),
    ])
    return train_tf, eval_tf


def build_model(arch: str, num_classes: int):
    if arch == "resnet18":
        model = models.resnet18(weights=models.ResNet18_Weights.DEFAULT)
        model.fc = nn.Linear(model.fc.in_features, num_classes)
    elif arch == "custom":
        model = nn.Sequential(
            nn.Conv2d(3, 32, 3, padding=1), nn.BatchNorm2d(32), nn.ReLU(),
            nn.MaxPool2d(2),
            nn.Conv2d(32, 64, 3, padding=1), nn.BatchNorm2d(64), nn.ReLU(),
            nn.MaxPool2d(2),
            nn.Conv2d(64, 128, 3, padding=1), nn.BatchNorm2d(128), nn.ReLU(),
            nn.MaxPool2d(2),
            nn.Conv2d(128, 256, 3, padding=1), nn.BatchNorm2d(256), nn.ReLU(),
            nn.AdaptiveAvgPool2d((1, 1)),
            nn.Flatten(),
            nn.Dropout(0.4),
            nn.Linear(256, num_classes),
        )
    else:
        raise ValueError(f"Unknown arch: {arch}")
    return model


def evaluate(model, loader, device, criterion):
    model.eval()
    all_preds, all_labels = [], []
    running_loss = 0.0
    with torch.no_grad():
        for images, labels in loader:
            images, labels = images.to(device), labels.to(device)
            outputs = model(images)
            loss = criterion(outputs, labels)
            running_loss += loss.item() * images.size(0)
            preds = outputs.argmax(dim=1)
            all_preds.extend(preds.cpu().numpy())
            all_labels.extend(labels.cpu().numpy())
    avg_loss = running_loss / len(loader.dataset)
    acc = accuracy_score(all_labels, all_preds)
    precision, recall, f1, _ = precision_recall_fscore_support(
        all_labels, all_preds, average="macro", zero_division=0
    )
    cm = confusion_matrix(all_labels, all_preds, labels=list(range(len(CLASSES))))

    # Per-class sensitivity (recall) and specificity from confusion matrix
    per_class = {}
    for i, cls in enumerate(CLASSES):
        tp = cm[i, i]
        fn = cm[i, :].sum() - tp
        fp = cm[:, i].sum() - tp
        tn = cm.sum() - tp - fn - fp
        sensitivity = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        specificity = tn / (tn + fp) if (tn + fp) > 0 else 0.0
        per_class[cls] = {"sensitivity": round(float(sensitivity), 4),
                           "specificity": round(float(specificity), 4)}

    return {
        "loss": avg_loss,
        "accuracy": acc,
        "precision_macro": precision,
        "recall_macro": recall,
        "f1_macro": f1,
        "confusion_matrix": cm.tolist(),
        "per_class": per_class,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--epochs", type=int, default=15)
    parser.add_argument("--batch_size", type=int, default=32)
    parser.add_argument("--lr", type=float, default=1e-4)
    parser.add_argument("--arch", type=str, default="resnet18",
                         choices=["resnet18", "custom"])
    parser.add_argument("--val_split", type=float, default=0.15)
    args = parser.parse_args()

    if not DATA_DIR.exists():
        raise FileNotFoundError(
            f"Dataset not found at {DATA_DIR}. Extract the Kaggle dataset "
            f"into ml/dataset/ with Training/ and Testing/ subfolders."
        )

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Using device: {device}")

    train_tf, eval_tf = get_transforms()

    full_train = datasets.ImageFolder(DATA_DIR / "Training", transform=train_tf)
    test_set = datasets.ImageFolder(DATA_DIR / "Testing", transform=eval_tf)

    # sanity check class order matches CLASSES
    assert full_train.classes == CLASSES, (
        f"Dataset class order {full_train.classes} does not match expected "
        f"{CLASSES}. Update the CLASSES constant to match."
    )

    val_size = int(len(full_train) * args.val_split)
    train_size = len(full_train) - val_size
    train_set, val_set = random_split(full_train, [train_size, val_size])
    # val split should use eval transform, not augmented -- swap dataset ref
    val_set.dataset = datasets.ImageFolder(DATA_DIR / "Training", transform=eval_tf)

    train_loader = DataLoader(train_set, batch_size=args.batch_size, shuffle=True, num_workers=2)
    val_loader = DataLoader(val_set, batch_size=args.batch_size, shuffle=False, num_workers=2)
    test_loader = DataLoader(test_set, batch_size=args.batch_size, shuffle=False, num_workers=2)

    print(f"Train: {len(train_set)} | Val: {len(val_set)} | Test: {len(test_set)}")

    model = build_model(args.arch, len(CLASSES)).to(device)
    criterion = nn.CrossEntropyLoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=args.lr)
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode="max", patience=2, factor=0.5)

    best_val_acc = 0.0
    history = []

    for epoch in range(1, args.epochs + 1):
        model.train()
        running_loss = 0.0
        t0 = time.time()
        for images, labels in train_loader:
            images, labels = images.to(device), labels.to(device)
            optimizer.zero_grad()
            outputs = model(images)
            loss = criterion(outputs, labels)
            loss.backward()
            optimizer.step()
            running_loss += loss.item() * images.size(0)
        train_loss = running_loss / len(train_loader.dataset)

        val_metrics = evaluate(model, val_loader, device, criterion)
        scheduler.step(val_metrics["accuracy"])

        elapsed = time.time() - t0
        print(f"Epoch {epoch}/{args.epochs} | train_loss={train_loss:.4f} "
              f"val_loss={val_metrics['loss']:.4f} val_acc={val_metrics['accuracy']:.4f} "
              f"({elapsed:.1f}s)")

        history.append({
            "epoch": epoch, "train_loss": train_loss,
            "val_loss": val_metrics["loss"], "val_accuracy": val_metrics["accuracy"],
        })

        if val_metrics["accuracy"] > best_val_acc:
            best_val_acc = val_metrics["accuracy"]
            torch.save({
                "model_state_dict": model.state_dict(),
                "arch": args.arch,
                "classes": CLASSES,
                "img_size": IMG_SIZE,
            }, MODEL_DIR / "best_model.pth")
            print(f"  -> saved new best model (val_acc={best_val_acc:.4f})")

    # Final evaluation on held-out test set using the BEST checkpoint
    checkpoint = torch.load(MODEL_DIR / "best_model.pth", map_location=device)
    model = build_model(checkpoint["arch"], len(CLASSES)).to(device)
    model.load_state_dict(checkpoint["model_state_dict"])
    test_metrics = evaluate(model, test_loader, device, criterion)

    print("\n=== Final Test Set Metrics (best checkpoint) ===")
    print(json.dumps({k: v for k, v in test_metrics.items() if k != "confusion_matrix"}, indent=2))

    metrics_out = {
        "generated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "is_placeholder": False,
        "arch": args.arch,
        "epochs_trained": args.epochs,
        "best_val_accuracy": best_val_acc,
        "test_metrics": test_metrics,
        "classes": CLASSES,
        "history": history,
    }
    with open(MODEL_DIR / "metrics.json", "w") as f:
        json.dump(metrics_out, f, indent=2)
    print(f"\nSaved model to {MODEL_DIR / 'best_model.pth'}")
    print(f"Saved metrics to {MODEL_DIR / 'metrics.json'}")


if __name__ == "__main__":
    main()
