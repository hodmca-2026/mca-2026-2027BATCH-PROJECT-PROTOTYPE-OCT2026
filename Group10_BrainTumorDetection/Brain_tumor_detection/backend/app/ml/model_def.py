"""
Model architecture definition used by the backend for inference.

Kept separate from ml/train.py so the backend is fully self-contained
(Render/Docker builds only include backend/). Must stay in sync with
build_model() in ml/train.py.
"""
import torch.nn as nn
from torchvision import models

CLASSES = ["glioma", "meningioma", "notumor", "pituitary"]
IMG_SIZE = 224


def build_model(arch: str, num_classes: int):
    if arch == "resnet18":
        # weights=None: we load our own trained weights (or run untrained placeholder)
        model = models.resnet18(weights=None)
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
