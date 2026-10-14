# ============================================================
# config.py
#
# Centralised configuration management.
# All paths, model settings, and environment variables
# are resolved here — no hardcoded paths anywhere else.
# ============================================================

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env file if it exists (safe in production too)
load_dotenv()


# ============================================================
# BASE PATHS
# ============================================================

PROJECT_DIR  = Path(__file__).resolve().parent

DATA_DIR         = PROJECT_DIR / "data"
ARTIFACT_DIR     = PROJECT_DIR / "artifacts"
MODEL_DIR        = PROJECT_DIR / "models"
PROCESSED_DIR    = PROJECT_DIR / "processed_data"
RESULT_DIR       = PROJECT_DIR / "results"
IR_ARTIFACT_DIR  = PROJECT_DIR / "ir_artifacts"
HR_DOCS_DIR      = PROJECT_DIR / "hr_documents"
EXTRACTED_DIR    = PROJECT_DIR / "extracted_documents"
LOG_DIR          = PROJECT_DIR / "logs"

# Create directories that must exist at runtime
for _dir in [LOG_DIR]:
    _dir.mkdir(exist_ok=True)


# ============================================================
# DATA
# ============================================================

EMPLOYEE_DATA_PATH = DATA_DIR / "employee_attrition_hr_2026.csv"


# ============================================================
# MODEL ARTIFACTS
# ============================================================

# Attrition
ATTRITION_MODEL_PATH        = MODEL_DIR / "attrition_deep_learning.keras"
ATTRITION_RF_PATH           = MODEL_DIR / "attrition_random_forest.pkl"
ATTRITION_LR_PATH           = MODEL_DIR / "attrition_logistic_regression.pkl"
ATTRITION_PREPROCESSOR_PATH = ARTIFACT_DIR / "attrition_preprocessor.pkl"
ATTRITION_FEATURE_NAMES_PATH = ARTIFACT_DIR / "attrition_feature_names.csv"
ATTRITION_X_TRAIN_PATH      = PROCESSED_DIR / "attrition_X_train.npy"

# Performance
PERFORMANCE_MODEL_PATH        = MODEL_DIR / "performance_deep_learning.keras"
PERFORMANCE_RF_PATH           = MODEL_DIR / "performance_random_forest.pkl"
PERFORMANCE_LR_PATH           = MODEL_DIR / "performance_logistic_regression.pkl"
PERFORMANCE_PREPROCESSOR_PATH = ARTIFACT_DIR / "performance_preprocessor.pkl"
PERFORMANCE_FEATURE_NAMES_PATH = ARTIFACT_DIR / "performance_feature_names.csv"
PERFORMANCE_X_TRAIN_PATH      = PROCESSED_DIR / "performance_X_train.npy"

# Threshold
THRESHOLD_PATH = RESULT_DIR / "best_attrition_threshold.txt"


# ============================================================
# IR ARTIFACTS
# ============================================================

INVERTED_INDEX_PATH         = IR_ARTIFACT_DIR / "inverted_index.json"
DOCUMENT_FREQ_PATH          = IR_ARTIFACT_DIR / "document_frequency.json"
DOC_TERM_FREQ_PATH          = IR_ARTIFACT_DIR / "document_term_frequencies.json"
PROCESSED_DOCUMENTS_PATH    = IR_ARTIFACT_DIR / "processed_documents.json"
HR_CLASSIFIER_PATH          = IR_ARTIFACT_DIR / "hr_classifier_metadata.pkl"


# ============================================================
# APP SETTINGS
# ============================================================

# Server
FLASK_HOST  = os.getenv("FLASK_HOST", "0.0.0.0")
FLASK_PORT  = int(os.getenv("FLASK_PORT", "5000"))
FLASK_DEBUG = os.getenv("FLASK_DEBUG", "false").lower() == "true"
SECRET_KEY  = os.getenv("SECRET_KEY", "change-me-in-production-via-env")

# Environment name (development | staging | production)
ENV = os.getenv("APP_ENV", "development")

# SHAP background sample size (keep small for latency)
SHAP_BACKGROUND_SAMPLES = int(os.getenv("SHAP_BACKGROUND_SAMPLES", "50"))

# Risk thresholds (can be overridden via environment)
ATTRITION_HIGH_THRESHOLD   = float(os.getenv("ATTRITION_HIGH_THRESHOLD", "0.64"))
ATTRITION_MEDIUM_THRESHOLD = float(os.getenv("ATTRITION_MEDIUM_THRESHOLD", "0.40"))

# Pagination
DEFAULT_PAGE_SIZE = int(os.getenv("DEFAULT_PAGE_SIZE", "20"))
MAX_PAGE_SIZE     = int(os.getenv("MAX_PAGE_SIZE", "5000"))

# Logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")


# ============================================================
# MODEL INPUT COLUMNS
# (single source of truth — imported wherever needed)
# ============================================================

MODEL_INPUT_COLUMNS = [
    "age",
    "gender",
    "marital_status",
    "education_level",
    "department",
    "job_role",
    "job_level",
    "monthly_income",
    "stock_option_level",
    "salary_hike_pct",
    "years_at_company",
    "total_working_years",
    "years_since_promotion",
    "num_prior_companies",
    "work_mode",
    "commute_minutes",
    "overtime_hours_per_week",
    "business_travel_days_per_year",
    "training_hours",
    "manager_support_score",
    "burnout_score",
    "engagement_score",
    "work_life_balance_score",
    "performance_rating",
    "last_review_score",
    "uses_ai_tools_at_work",
    "perceived_ai_job_risk",
]

# Numeric subset (for validation ranges)
NUMERIC_MODEL_COLUMNS = {
    "age",
    "job_level",
    "monthly_income",
    "stock_option_level",
    "salary_hike_pct",
    "years_at_company",
    "total_working_years",
    "years_since_promotion",
    "num_prior_companies",
    "commute_minutes",
    "overtime_hours_per_week",
    "business_travel_days_per_year",
    "training_hours",
    "manager_support_score",
    "burnout_score",
    "engagement_score",
    "work_life_balance_score",
    "performance_rating",
    "last_review_score",
    "perceived_ai_job_risk",
}
