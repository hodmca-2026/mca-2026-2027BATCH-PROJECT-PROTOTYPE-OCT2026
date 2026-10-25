"""
evaluate_model.py - honest re-evaluation of an ALREADY TRAINED model (no retraining needed).

Why: the validation score printed during training comes from a random slice of the Training folder, which can
contain near-duplicates of training images, so it is optimistic. This script
  1. scores the model on the official Testing folder,
  2. finds Testing images that are near-duplicates of a Training image (dedup.py) and also scores the model
     WITHOUT them (the "leakage-controlled" result - the more trustworthy number),
  3. saves the confusion matrix, per-class sensitivity/specificity, ROC-AUC and the most common mistakes,
  4. updates ml/models/metrics.json so the app's "Model & admin" page shows the full picture
     (your original file is kept as metrics.v1.json).

Usage (from the ml/ folder, venv active):    python evaluate_model.py
"""
import argparse
import json
import shutil
import time
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import torch
import torch.nn as nn
from PIL import Image
from sklearn.metrics import (accuracy_score, classification_report, confusion_matrix,
                             precision_recall_fscore_support, roc_auc_score)
from torch.utils.data import DataLoader, Subset
from torchvision import datasets, models, transforms

from dedup import compute_features, leaked_indices, normalise

HERE = Path(__file__).parent
MEAN, STD = [0.485, 0.456, 0.406], [0.229, 0.224, 0.225]


def build_model(arch, n):
    """Same graphs as training; no pretrained weights are downloaded here."""
    if arch == "resnet18":
        m = models.resnet18(weights=None); m.fc = nn.Linear(m.fc.in_features, n)
    elif arch == "resnet50":
        m = models.resnet50(weights=None); m.fc = nn.Linear(m.fc.in_features, n)
    elif arch == "efficientnet_b0":
        m = models.efficientnet_b0(weights=None); m.classifier[1] = nn.Linear(m.classifier[1].in_features, n)
    elif arch == "custom":
        m = nn.Sequential(
            nn.Conv2d(3, 32, 3, padding=1), nn.BatchNorm2d(32), nn.ReLU(), nn.MaxPool2d(2),
            nn.Conv2d(32, 64, 3, padding=1), nn.BatchNorm2d(64), nn.ReLU(), nn.MaxPool2d(2),
            nn.Conv2d(64, 128, 3, padding=1), nn.BatchNorm2d(128), nn.ReLU(), nn.MaxPool2d(2),
            nn.Conv2d(128, 256, 3, padding=1), nn.BatchNorm2d(256), nn.ReLU(),
            nn.AdaptiveAvgPool2d((1, 1)), nn.Flatten(), nn.Dropout(0.4), nn.Linear(256, n))
    else:
        raise ValueError(f"Unknown architecture in checkpoint: {arch}")
    return m


def softmax(z):
    z = z - z.max(axis=1, keepdims=True)
    e = np.exp(z)
    return e / e.sum(axis=1, keepdims=True)


def ece(probs, labels, bins=15):
    conf, pred = probs.max(1), probs.argmax(1)
    ok = (pred == labels).astype(float)
    edges = np.linspace(0, 1, bins + 1)
    total = 0.0
    for lo, hi in zip(edges[:-1], edges[1:]):
        m = (conf > lo) & (conf <= hi)
        if m.any():
            total += m.mean() * abs(ok[m].mean() - conf[m].mean())
    return float(total)


@torch.no_grad()
def collect_logits(model, ds, device, batch_size, workers):
    model.eval()
    logits, labels = [], []
    for x, y in DataLoader(ds, batch_size=batch_size, shuffle=False, num_workers=workers):
        logits.append(model(x.to(device)).float().cpu().numpy())
        labels.append(y.numpy())
    return np.concatenate(logits), np.concatenate(labels)


def metrics_from_logits(logits, labels, classes):
    probs = softmax(logits)
    preds = probs.argmax(1)
    k = len(classes)
    prec, rec, f1, _ = precision_recall_fscore_support(labels, preds, average="macro", zero_division=0)
    cm = confusion_matrix(labels, preds, labels=list(range(k)))
    per_class = {}
    for i, c in enumerate(classes):
        tp = cm[i, i]; fn = cm[i].sum() - tp; fp = cm[:, i].sum() - tp; tn = cm.sum() - tp - fn - fp
        per_class[c] = {"sensitivity": round(float(tp / (tp + fn)) if tp + fn else 0.0, 4),
                        "specificity": round(float(tn / (tn + fp)) if tn + fp else 0.0, 4)}
    try:
        auc = float(roc_auc_score(labels, probs, multi_class="ovr", average="macro", labels=list(range(k))))
    except ValueError:
        auc = None
    return {"n_images": int(len(labels)), "accuracy": float(accuracy_score(labels, preds)),
            "precision_macro": float(prec), "recall_macro": float(rec), "f1_macro": float(f1),
            "roc_auc_ovr_macro": auc, "ece_uncalibrated": ece(probs, labels),
            "confusion_matrix": cm.tolist(), "per_class": per_class,
            "classification_report": classification_report(labels, preds, labels=list(range(k)), target_names=classes,
                                                           output_dict=True, zero_division=0)}


def top_mistakes(cm, classes, n=5):
    cm = np.array(cm)
    items = [(classes[i], classes[j], int(cm[i, j])) for i in range(len(classes)) for j in range(len(classes))
             if i != j and cm[i, j] > 0]
    return sorted(items, key=lambda t: -t[2])[:n]


def plot_confusion(cm, classes, path, title):
    cm = np.array(cm); norm = cm / np.maximum(cm.sum(axis=1, keepdims=True), 1)
    fig, ax = plt.subplots(figsize=(5.6, 4.8))
    ax.imshow(norm, cmap="Blues", vmin=0, vmax=1)
    ax.set_xticks(range(len(classes))); ax.set_yticks(range(len(classes)))
    ax.set_xticklabels(classes, rotation=30, ha="right"); ax.set_yticklabels(classes)
    ax.set_xlabel("Predicted"); ax.set_ylabel("True"); ax.set_title(title, fontsize=10)
    for i in range(len(classes)):
        for j in range(len(classes)):
            ax.text(j, i, f"{cm[i, j]}\n{norm[i, j]*100:.0f}%", ha="center", va="center",
                    color="white" if norm[i, j] > 0.5 else "black", fontsize=8)
    fig.tight_layout(); fig.savefig(path, dpi=140); plt.close(fig)


def plot_dedup_pairs(te_paths, tr_paths, flagged, mins, nearest, path, max_pairs=6):
    """Flagged test image (top) vs its closest training image (bottom); weakest matches first."""
    if len(flagged) == 0:
        return False
    order = flagged[np.argsort(-mins[flagged])][:max_pairs]
    fig, ax = plt.subplots(2, len(order), figsize=(2.4 * len(order), 5.2), squeeze=False)
    for col, i in enumerate(order):
        for row, p in enumerate((te_paths[i], tr_paths[nearest[i]])):
            ax[row, col].imshow(Image.open(p).convert("L"), cmap="gray"); ax[row, col].axis("off")
        ax[0, col].set_title(f"distance {mins[i]:.3f}", fontsize=8)
    ax[0, 0].text(-0.05, 0.5, "Testing", transform=ax[0, 0].transAxes, rotation=90, ha="right", va="center")
    ax[1, 0].text(-0.05, 0.5, "closest Training", transform=ax[1, 0].transAxes, rotation=90, ha="right", va="center")
    fig.suptitle("Flagged near-duplicates (weakest matches first)", fontsize=10)
    fig.tight_layout(); fig.savefig(path, dpi=130); plt.close(fig)
    return True


def _jsonable(o):
    if isinstance(o, np.generic):
        return o.item()
    if isinstance(o, np.ndarray):
        return o.tolist()
    raise TypeError(type(o))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--checkpoint", type=Path, default=HERE / "models" / "best_model.pth")
    ap.add_argument("--data_dir", type=Path, default=HERE / "dataset")
    ap.add_argument("--out_dir", type=Path, default=None, help="default: the folder of the checkpoint")
    ap.add_argument("--dup_threshold", type=float, default=0.12, help="max cosine distance to call two images near-duplicates")
    ap.add_argument("--batch_size", type=int, default=64)
    ap.add_argument("--workers", type=int, default=0)
    args = ap.parse_args()
    out_dir = args.out_dir or args.checkpoint.parent

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    ckpt = torch.load(args.checkpoint, map_location=device)
    classes = ckpt["classes"]
    model = build_model(ckpt["arch"], len(classes)).to(device)
    model.load_state_dict(ckpt["model_state_dict"])
    img_size = ckpt.get("img_size", 224)
    print(f"Loaded {ckpt['arch']} from {args.checkpoint} | device: {device}")

    eval_tf = transforms.Compose([transforms.Grayscale(num_output_channels=3), transforms.Resize((img_size, img_size)),
                                  transforms.ToTensor(), transforms.Normalize(MEAN, STD)])
    train_ds = datasets.ImageFolder(args.data_dir / "Training", transform=eval_tf)
    test_ds = datasets.ImageFolder(args.data_dir / "Testing", transform=eval_tf)
    assert train_ds.classes == classes == test_ds.classes, f"class folders {test_ds.classes} != checkpoint {classes}"
    tr_paths = [p for p, _ in train_ds.samples]; te_paths = [p for p, _ in test_ds.samples]

    print(f"Scoring {len(test_ds)} test images ...")
    logits, labels = collect_logits(model, test_ds, device, args.batch_size, args.workers)
    official = metrics_from_logits(logits, labels, classes)

    print(f"Scanning {len(tr_paths)} training + {len(te_paths)} test images for near-duplicates ...")
    t0 = time.time()
    tr_f, te_f = compute_features(tr_paths), compute_features(te_paths)
    mean_img = tr_f.mean(axis=0)
    flagged, mins, nearest = leaked_indices(normalise(tr_f, mean_img), normalise(te_f, mean_img), args.dup_threshold)
    keep = np.setdiff1d(np.arange(len(te_paths)), flagged)
    print(f"  done in {time.time()-t0:.0f}s: {len(flagged)} of {len(te_paths)} test images are near-duplicates of a training image")
    clean = metrics_from_logits(logits[keep], labels[keep], classes) if len(keep) else official

    out_dir.mkdir(parents=True, exist_ok=True)
    plot_confusion(clean["confusion_matrix"], classes, out_dir / "confusion_matrix.png",
                   f"Confusion matrix - leakage-controlled test (n={clean['n_images']})")
    made = plot_dedup_pairs(te_paths, tr_paths, flagged, mins, nearest, out_dir / "dedup_pairs.png")

    line = lambda name, m: print(f"  {name:28s} n={m['n_images']:5d}  accuracy {m['accuracy']*100:6.2f}%  "
                                 f"macro-F1 {m['f1_macro']*100:6.2f}%  ROC-AUC {m['roc_auc_ovr_macro'] if m['roc_auc_ovr_macro'] is None else round(m['roc_auc_ovr_macro'], 4)}")
    print("\n=== RESULTS ===")
    line("Official Testing folder", official)
    line("Leakage-controlled (headline)", clean)
    print("\nPer class (leakage-controlled):  sensitivity = share of real cases found, specificity = share of non-cases correctly rejected")
    for c, v in clean["per_class"].items():
        print(f"  {c:12s} sensitivity {v['sensitivity']*100:6.2f}%   specificity {v['specificity']*100:6.2f}%")
    print("\nMost common mistakes (true -> predicted):")
    for t, p, n in top_mistakes(clean["confusion_matrix"], classes):
        print(f"  {t:12s} -> {p:12s} {n} images")
    print(f"\nUncalibrated confidence error (ECE): {clean['ece_uncalibrated']:.3f}  (0 = confidence matches accuracy)")

    mpath = out_dir / "metrics.json"
    old = json.loads(mpath.read_text()) if mpath.exists() else {}
    if old and not (out_dir / "metrics.v1.json").exists():
        shutil.copy(mpath, out_dir / "metrics.v1.json")
    old.update({
        "is_placeholder": False, "arch": ckpt["arch"], "classes": classes,
        "evaluated_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "evaluation_protocol": ("Headline test metrics exclude Testing images that are near-duplicates of a Training image "
                                "(no patient IDs exist in this dataset); official-test metrics are reported separately. "
                                "Not clinically validated."),
        "dataset": {"name": "Brain Tumor MRI Dataset (Kaggle)", "classes": classes, "train_images": len(tr_paths),
                    "test_official": len(te_paths), "test_leakage_controlled": int(len(keep))},
        "dedup": {"method": "mean-centred 32x32 grayscale, cosine distance", "threshold_distance": args.dup_threshold,
                  "test_flagged_near_duplicates": int(len(flagged)),
                  "flagged_examples": [Path(te_paths[i]).name for i in flagged[:20]]},
        "test_metrics": clean, "test_metrics_official": official,
    })
    mpath.write_text(json.dumps(old, indent=2, default=_jsonable))
    print(f"\nSaved: {mpath} (original kept as metrics.v1.json)\n       {out_dir / 'confusion_matrix.png'}")
    if made:
        print(f"       {out_dir / 'dedup_pairs.png'}  <- open it: do the flagged pairs really look like the same scan?")
    else:
        print("       (no near-duplicates found, so no dedup_pairs.png)")


if __name__ == "__main__":
    main()
