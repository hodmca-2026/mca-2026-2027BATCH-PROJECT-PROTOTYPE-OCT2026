# ============================================================
# tests/test_config.py
#
# Unit tests for the centralised configuration module.
# ============================================================

import sys
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import config


class TestPaths:

    def test_project_dir_exists(self):
        assert config.PROJECT_DIR.exists()

    def test_data_dir_is_subdir_of_project(self):
        assert config.DATA_DIR.parent == config.PROJECT_DIR

    def test_model_input_columns_is_list(self):
        assert isinstance(config.MODEL_INPUT_COLUMNS, list)
        assert len(config.MODEL_INPUT_COLUMNS) > 0

    def test_numeric_columns_subset_of_input_columns(self):
        for col in config.NUMERIC_MODEL_COLUMNS:
            assert col in config.MODEL_INPUT_COLUMNS, (
                f"{col} is in NUMERIC_MODEL_COLUMNS "
                f"but not in MODEL_INPUT_COLUMNS"
            )


class TestSettings:

    def test_flask_port_is_int(self):
        assert isinstance(config.FLASK_PORT, int)
        assert 1 <= config.FLASK_PORT <= 65535

    def test_thresholds_valid(self):
        assert 0 < config.ATTRITION_MEDIUM_THRESHOLD < config.ATTRITION_HIGH_THRESHOLD < 1

    def test_shap_background_positive(self):
        assert config.SHAP_BACKGROUND_SAMPLES > 0

    def test_page_size_logical(self):
        assert config.DEFAULT_PAGE_SIZE <= config.MAX_PAGE_SIZE
