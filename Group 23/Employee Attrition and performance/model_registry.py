# ==============================================================
# model_registry.py
#
# Model Versioning & Performance Registry
#
# Industry pattern: every trained model should be tagged with
# a version, training date, dataset stats, and evaluation
# metrics so that deployment decisions are auditable.
#
# Usage:
#   from model_registry import registry
#   info = registry.get_model_info("attrition")
#   registry.log_training_run("attrition", metrics={...})
# ==============================================================

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from logger import get_logger

logger = get_logger(__name__)


# ==============================================================
# PATHS
# ==============================================================

PROJECT_DIR   = Path(__file__).resolve().parent
REGISTRY_PATH = PROJECT_DIR / "results" / "model_registry.json"


# ==============================================================
# DEFAULT REGISTRY SEED
# (populated from actual training output in results/)
# ==============================================================

_DEFAULT_REGISTRY: Dict[str, Any] = {
    "attrition": {
        "name":           "Employee Attrition Predictor",
        "task":           "binary_classification",
        "primary_model":  "Deep Neural Network",
        "version":        "1.0.0",
        "trained_at":     "2026-10-01T00:00:00Z",
        "dataset": {
            "source":      "employee_attrition_hr_2026.csv",
            "total_rows":  5000,
            "train_rows":  4000,
            "test_rows":   1000,
            "features":    27,
            "target":      "attrition",
            "positive_rate": 0.179,
        },
        "models": {
            "Deep Neural Network": {
                "architecture": "128-64-32-1 (sigmoid)",
                "dropout":      0.30,
                "batch_norm":   True,
                "epochs":       100,
                "batch_size":   32,
                "optimizer":    "Adam(lr=0.001)",
                "loss":         "binary_crossentropy",
                "class_weights": "balanced",
            },
            "Random Forest": {
                "n_estimators":     300,
                "class_weight":     "balanced",
            },
            "Logistic Regression": {
                "max_iter":    2000,
                "class_weight": "balanced",
            },
        },
        "metrics_file": "results/attrition_model_comparison.csv",
        "training_history_file": "results/attrition_training_history.csv",
        "threshold_file": "results/best_attrition_threshold.txt",
        "shap_file":    "results/attrition_shap_feature_importance.csv",
    },
    "performance": {
        "name":           "Employee Performance Predictor",
        "task":           "multi_class_classification",
        "primary_model":  "Deep Neural Network",
        "version":        "1.0.0",
        "trained_at":     "2026-10-01T00:00:00Z",
        "dataset": {
            "source":      "employee_attrition_hr_2026.csv",
            "total_rows":  5000,
            "train_rows":  4000,
            "test_rows":   1000,
            "features":    27,
            "target":      "performance_rating",
            "classes":     [2, 3, 4, 5],
        },
        "models": {
            "Deep Neural Network": {
                "architecture": "128-64-32-4 (softmax)",
                "dropout":      0.30,
                "batch_norm":   True,
                "epochs":       100,
                "batch_size":   32,
                "optimizer":    "Adam(lr=0.001)",
                "loss":         "sparse_categorical_crossentropy",
            },
            "Random Forest": {
                "n_estimators": 300,
                "class_weight": "balanced",
            },
            "Logistic Regression": {
                "max_iter": 2000,
                "class_weight": "balanced",
            },
        },
        "metrics_file": "results/performance_model_comparison.csv",
        "training_history_file": "results/performance_training_history.csv",
        "shap_file":   "results/performance_shap_feature_importance.csv",
    },
}


# ==============================================================
# REGISTRY CLASS
# ==============================================================

class ModelRegistry:
    """
    Lightweight JSON-backed model registry.

    Stores model versions, training metadata, and evaluation
    metrics. Falls back gracefully to defaults if the registry
    file does not yet exist.
    """

    def __init__(self, path: Path = REGISTRY_PATH) -> None:
        self._path = path
        self._data: Dict[str, Any] = self._load()

    # ----------------------------------------------------------
    # LOAD / SAVE
    # ----------------------------------------------------------

    def _load(self) -> Dict[str, Any]:
        """Load registry from disk; seed with defaults if missing."""
        if self._path.exists():
            try:
                with open(self._path, "r", encoding="utf-8") as fh:
                    data = json.load(fh)
                logger.debug("Model registry loaded from %s", self._path)
                return data
            except (json.JSONDecodeError, OSError) as err:
                logger.warning(
                    "Could not read model registry (%s); using defaults.", err
                )
        return dict(_DEFAULT_REGISTRY)

    def _save(self) -> None:
        """Persist the current registry to disk."""
        self._path.parent.mkdir(parents=True, exist_ok=True)
        with open(self._path, "w", encoding="utf-8") as fh:
            json.dump(self._data, fh, indent=2, default=str)
        logger.debug("Model registry saved to %s", self._path)

    # ----------------------------------------------------------
    # PUBLIC API
    # ----------------------------------------------------------

    def get_model_info(self, task: str) -> Optional[Dict[str, Any]]:
        """
        Return metadata for a trained model task.

        Args:
            task: ``"attrition"`` or ``"performance"``.

        Returns:
            Metadata dict, or ``None`` if the task is unknown.
        """
        return self._data.get(task)

    def all_tasks(self) -> Dict[str, Any]:
        """Return the full registry."""
        return dict(self._data)

    def log_training_run(
        self,
        task: str,
        metrics: Dict[str, Any],
        version: Optional[str] = None,
    ) -> None:
        """
        Record a new training run result in the registry.

        Args:
            task:    Model task name (``"attrition"`` or ``"performance"``).
            metrics: Evaluation metrics dict
                     e.g. ``{"accuracy": 0.87, "f1": 0.72, "roc_auc": 0.92}``.
            version: Optional semantic version string. Auto-increments patch
                     if omitted.
        """
        if task not in self._data:
            self._data[task] = {}

        entry = self._data[task]

        # Auto-bump patch version
        if version is None:
            current = entry.get("version", "1.0.0")
            parts   = current.split(".")
            try:
                parts[-1] = str(int(parts[-1]) + 1)
            except (ValueError, IndexError):
                parts = ["1", "0", "1"]
            version = ".".join(parts)

        entry["version"]    = version
        entry["trained_at"] = datetime.now(tz=timezone.utc).isoformat()
        entry["last_metrics"] = {
            k: (round(v, 6) if isinstance(v, float) else v)
            for k, v in metrics.items()
        }

        self._save()
        logger.info(
            "Logged training run for '%s' — version=%s metrics=%s",
            task, version, metrics,
        )

    def summary(self) -> Dict[str, Any]:
        """
        Return a concise API-ready summary of all registered models.
        """
        out = {}
        for task, info in self._data.items():
            out[task] = {
                "name":          info.get("name", task),
                "task":          info.get("task"),
                "primary_model": info.get("primary_model"),
                "version":       info.get("version"),
                "trained_at":    info.get("trained_at"),
                "last_metrics":  info.get("last_metrics"),
            }
        return out


# ==============================================================
# SINGLETON
# ==============================================================

registry = ModelRegistry()
