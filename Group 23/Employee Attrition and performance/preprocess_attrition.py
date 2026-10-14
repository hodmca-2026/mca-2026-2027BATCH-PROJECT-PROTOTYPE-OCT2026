# preprocessing/preprocess_attrition.py

from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import OneHotEncoder, StandardScaler


# ==========================================================
# PATHS
# ==========================================================

PROJECT_DIR = Path(__file__).resolve().parent

DATASET_PATH = PROJECT_DIR / "data" / "employee_attrition_hr_2026.csv"

ARTIFACT_DIR = PROJECT_DIR / "artifacts"
PROCESSED_DIR = PROJECT_DIR / "processed_data"

ARTIFACT_DIR.mkdir(exist_ok=True)
PROCESSED_DIR.mkdir(exist_ok=True)


# ==========================================================
# LOAD DATA
# ==========================================================

df = pd.read_csv(DATASET_PATH)

print("=" * 70)
print("ATTRITION DATA PREPROCESSING")
print("=" * 70)

print(f"Original shape: {df.shape}")


# ==========================================================
# BASIC CLEANING
# ==========================================================

# Remove duplicate rows
df = df.drop_duplicates().reset_index(drop=True)

# Remove duplicate employee IDs
df = df.drop_duplicates(
    subset="employee_id"
).reset_index(drop=True)

print(f"Shape after cleaning: {df.shape}")


# ==========================================================
# CHECK REQUIRED COLUMNS
# ==========================================================

required_columns = [
    "employee_id",
    "attrition",
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

missing_columns = [
    col for col in required_columns
    if col not in df.columns
]

if missing_columns:
    raise ValueError(
        f"Missing columns: {missing_columns}"
    )


# ==========================================================
# CONVERT BOOLEAN
# ==========================================================

df["uses_ai_tools_at_work"] = (
    df["uses_ai_tools_at_work"]
    .astype(int)
)


# ==========================================================
# TARGET ENCODING
# ==========================================================

df["attrition"] = (
    df["attrition"]
    .map({
        "No": 0,
        "Yes": 1
    })
)

if df["attrition"].isnull().any():
    raise ValueError(
        "Invalid values found in attrition column."
    )


# ==========================================================
# FEATURES / TARGET
# ==========================================================

# Remove only the identifier and target
X = df.drop(
    columns=[
        "employee_id",
        "attrition"
    ]
)

y = df["attrition"]


# ==========================================================
# FEATURE GROUPS
# ==========================================================

categorical_features = [
    "gender",
    "marital_status",
    "education_level",
    "department",
    "job_role",
    "work_mode",
]

numeric_features = [
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
    "uses_ai_tools_at_work",
    "perceived_ai_job_risk",
]


# ==========================================================
# TRAIN / TEST SPLIT
# ==========================================================

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.20,
    random_state=42,
    stratify=y
)


# ==========================================================
# NUMERICAL PIPELINE
# ==========================================================

numeric_pipeline = Pipeline = __import__(
    "sklearn.pipeline",
    fromlist=["Pipeline"]
).Pipeline

numeric_transformer = numeric_pipeline(
    steps=[
        (
            "imputer",
            SimpleImputer(strategy="median")
        ),
        (
            "scaler",
            StandardScaler()
        ),
    ]
)


# ==========================================================
# CATEGORICAL PIPELINE
# ==========================================================

categorical_transformer = numeric_pipeline(
    steps=[
        (
            "imputer",
            SimpleImputer(
                strategy="most_frequent"
            )
        ),
        (
            "onehot",
            OneHotEncoder(
                handle_unknown="ignore",
                sparse_output=False
            )
        ),
    ]
)


# ==========================================================
# COMBINED PREPROCESSOR
# ==========================================================

preprocessor = ColumnTransformer(
    transformers=[
        (
            "numeric",
            numeric_transformer,
            numeric_features
        ),
        (
            "categorical",
            categorical_transformer,
            categorical_features
        ),
    ]
)


# ==========================================================
# FIT ONLY ON TRAINING DATA
# ==========================================================

X_train_processed = preprocessor.fit_transform(
    X_train
)

X_test_processed = preprocessor.transform(
    X_test
)


# ==========================================================
# CONVERT TO FLOAT32
# ==========================================================

X_train_processed = np.asarray(
    X_train_processed,
    dtype=np.float32
)

X_test_processed = np.asarray(
    X_test_processed,
    dtype=np.float32
)

y_train = y_train.to_numpy(
    dtype=np.float32
)

y_test = y_test.to_numpy(
    dtype=np.float32
)


# ==========================================================
# SAVE
# ==========================================================

np.save(
    PROCESSED_DIR / "attrition_X_train.npy",
    X_train_processed
)

np.save(
    PROCESSED_DIR / "attrition_X_test.npy",
    X_test_processed
)

np.save(
    PROCESSED_DIR / "attrition_y_train.npy",
    y_train
)

np.save(
    PROCESSED_DIR / "attrition_y_test.npy",
    y_test
)


# Save preprocessing pipeline
joblib.dump(
    preprocessor,
    ARTIFACT_DIR / "attrition_preprocessor.pkl"
)


# Save feature names
feature_names = (
    preprocessor
    .get_feature_names_out()
)

pd.Series(feature_names).to_csv(
    ARTIFACT_DIR / "attrition_feature_names.csv",
    index=False
)


# ==========================================================
# SUMMARY
# ==========================================================

print("\n" + "=" * 70)
print("ATTRITION PREPROCESSING COMPLETE")
print("=" * 70)

print("Training samples :", X_train_processed.shape[0])
print("Testing samples  :", X_test_processed.shape[0])
print("Input features   :", X_train_processed.shape[1])

print("\nClass distribution:")

print(
    pd.Series(y)
    .value_counts()
    .sort_index()
    .rename({
        0: "No Attrition",
        1: "Attrition"
    })
)

print("\nSaved:")
print("processed_data/attrition_X_train.npy")
print("processed_data/attrition_X_test.npy")
print("processed_data/attrition_y_train.npy")
print("processed_data/attrition_y_test.npy")
print("artifacts/attrition_preprocessor.pkl")
print("artifacts/attrition_feature_names.csv")