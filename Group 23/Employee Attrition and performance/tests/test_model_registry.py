# ============================================================
# tests/test_model_registry.py
#
# Unit tests for the model registry module.
# ============================================================

import sys
from pathlib import Path
import pytest
import json
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from model_registry import ModelRegistry, _DEFAULT_REGISTRY


# ============================================================
# FIXTURES
# ============================================================

@pytest.fixture
def tmp_registry(tmp_path):
    """A fresh in-memory registry backed by a temp file."""
    registry_file = tmp_path / "test_registry.json"
    return ModelRegistry(path=registry_file)


# ============================================================
# TESTS
# ============================================================

class TestModelRegistry:

    def test_loads_defaults_when_no_file(self, tmp_registry):
        assert "attrition"   in tmp_registry.all_tasks()
        assert "performance" in tmp_registry.all_tasks()

    def test_get_model_info_returns_dict(self, tmp_registry):
        info = tmp_registry.get_model_info("attrition")
        assert isinstance(info, dict)
        assert "version" in info

    def test_get_model_info_unknown_task(self, tmp_registry):
        result = tmp_registry.get_model_info("nonexistent")
        assert result is None

    def test_summary_shape(self, tmp_registry):
        summary = tmp_registry.summary()
        for task, meta in summary.items():
            assert "name"    in meta
            assert "version" in meta

    def test_log_training_run_updates_version(self, tmp_registry):
        original_version = tmp_registry.get_model_info("attrition")["version"]
        tmp_registry.log_training_run(
            "attrition",
            metrics={"accuracy": 0.87, "f1": 0.72},
        )
        new_version = tmp_registry.get_model_info("attrition")["version"]
        assert new_version != original_version

    def test_log_training_run_stores_metrics(self, tmp_registry):
        tmp_registry.log_training_run(
            "attrition",
            metrics={"accuracy": 0.87, "roc_auc": 0.92},
        )
        info = tmp_registry.get_model_info("attrition")
        assert "last_metrics" in info
        assert abs(info["last_metrics"]["accuracy"] - 0.87) < 1e-5

    def test_persists_to_disk(self, tmp_path):
        registry_file = tmp_path / "registry.json"
        r1 = ModelRegistry(path=registry_file)
        r1.log_training_run("attrition", metrics={"f1": 0.72}, version="9.9.9")

        r2 = ModelRegistry(path=registry_file)
        assert r2.get_model_info("attrition")["version"] == "9.9.9"

    def test_explicit_version_string(self, tmp_registry):
        tmp_registry.log_training_run(
            "performance",
            metrics={"accuracy": 0.78},
            version="2.5.0",
        )
        assert tmp_registry.get_model_info("performance")["version"] == "2.5.0"
