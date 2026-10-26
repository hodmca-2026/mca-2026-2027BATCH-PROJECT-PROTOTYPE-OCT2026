"""
Loads the trained CNN (ml/train.py -> best_model.pth) and runs prediction + Grad-CAM for the API.

If no checkpoint exists, an UNTRAINED network is served so the rest of the app can be demonstrated; every such
response is flagged is_placeholder=True and must be treated as meaningless. If the checkpoint carries a
calibration temperature T, confidence = softmax(logits / T); otherwise T = 1.
"""
import json

import torch
from PIL import Image

from app.core.config import settings
from app.ml.gradcam import DISCLAIMER_TEXT, run_gradcam
from app.ml.model_def import CLASSES, IMG_SIZE, build_model

_model = None
_is_placeholder = True
_arch = "resnet18"
_temperature = 1.0
_device = torch.device("cuda" if torch.cuda.is_available() else "cpu")


def _load_model():
    global _model, _is_placeholder, _arch, _temperature
    if _model is not None:
        return _model
    if settings.MODEL_PATH.exists():
        checkpoint = torch.load(settings.MODEL_PATH, map_location=_device)
        _arch = checkpoint.get("arch", "resnet18")
        model = build_model(_arch, len(CLASSES))
        model.load_state_dict(checkpoint["model_state_dict"])
        _temperature = float(checkpoint.get("temperature", 1.0))
        _is_placeholder = False
        print(f"[inference] Loaded trained {_arch} from {settings.MODEL_PATH} (T={_temperature:.3f})")
    else:
        model = build_model(_arch, len(CLASSES))
        _is_placeholder = True
        print("[inference] WARNING: no trained checkpoint found - serving an UNTRAINED placeholder model.")
    model.to(_device).eval()
    _model = model
    return _model


def get_model_status() -> dict:
    _load_model()
    metrics = None
    if settings.METRICS_PATH.exists():
        with open(settings.METRICS_PATH) as f:
            metrics = json.load(f)
    return {"is_placeholder": _is_placeholder, "architecture": _arch, "classes": CLASSES,
            "temperature": _temperature, "metrics": metrics}


def predict_with_explanation(image_path: str, save_heatmap_to: str, save_overlay_to: str) -> dict:
    model = _load_model()
    pil_image = Image.open(image_path).convert("RGB")
    result = run_gradcam(model, pil_image, img_size=IMG_SIZE, temperature=_temperature)
    result["heatmap_img"].save(save_heatmap_to)
    result["overlay_img"].save(save_overlay_to)
    probs, idx = result["probabilities"], result["predicted_class_idx"]
    return {
        "predicted_class": CLASSES[idx], "confidence_score": float(probs[idx]),
        "all_class_probabilities": {c: float(p) for c, p in zip(CLASSES, probs)},
        "is_placeholder": _is_placeholder, "disclaimer": DISCLAIMER_TEXT,
    }
