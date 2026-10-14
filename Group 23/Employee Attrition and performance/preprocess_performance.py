# preprocessing/preprocess_performance.py

from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
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
# LOAD
# ==========================================================

df = pd.read_csv(DATASET_PATH)

print("=" * 70)
print("PERFORMANCE DATA PREPROCESSING")
print("=" * 70)

print(f"Original shape: {df.shape}")


# ==========================================================
# BASIC CLEANING
# ==========================================================

df = df.drop_duplicates().reset_index(drop=True)

df = df.drop_duplicates(
    subset="employee_id"
).reset_index(drop=True)

print(f"Shape after cleaning: {df.shape}")


# ==========================================================
# BOOLEAN
# ==========================================================

df["uses_ai_tools_at_work"] = (
    df["uses_ai_tools_at_work"]
    .astype(int)
)


# ==========================================================
# TARGET
# ==========================================================

# Performance ratings in this dataset:
# 2, 3, 4, 5
#
# Convert them to:
# 0 -> rating 2
# 1 -> rating 3
# 2 -> rating 4
# 3 -> rating 5

performance_mapping = {
    2: 0,
    3: 1,
    4: 2,
    5: 3
}

df["performance_target"] = (
    df["performance_rating"]
    .map(performance_mapping)
)

if df["performance_target"].isnull().any():
    raise ValueError(
        "Unexpected performance rating found."
    )


# ==========================================================
# FEATURES / TARGET
# ==========================================================

X = df.drop(
    columns=[
        "employee_id",
        "performance_rating",
        "performance_target"
    ]
)

y = df["performance_target"]


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
# PREPROCESSING
# ==========================================================

numeric_transformer = Pipeline(
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

categorical_transformer = Pipeline(
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
# FIT
# ==========================================================

X_train_processed = preprocessor.fit_transform(
    X_train
)

X_test_processed = preprocessor.transform(
    X_test
)


# ==========================================================
# NUMPY
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
    dtype=np.int64
)

y_test = y_test.to_numpy(
    dtype=np.int64
)


# ==========================================================
# SAVE
# ==========================================================

np.save(
    PROCESSED_DIR / "performance_X_train.npy",
    X_train_processed
)

np.save(
    PROCESSED_DIR / "performance_X_test.npy",
    X_test_processed
)

np.save(
    PROCESSED_DIR / "performance_y_train.npy",
    y_train
)

np.save(
    PROCESSED_DIR / "performance_y_test.npy",
    y_test
)


# Save preprocessor
joblib.dump(
    preprocessor,
    ARTIFACT_DIR / "performance_preprocessor.pkl"
)


# Save feature names
feature_names = (
    preprocessor
    .get_feature_names_out()
)

pd.Series(feature_names).to_csv(
    ARTIFACT_DIR / "performance_feature_names.csv",
    index=False
)


# ==========================================================
# SUMMARY
# ==========================================================

print("\n" + "=" * 70)
print("PERFORMANCE PREPROCESSING COMPLETE")
print("=" * 70)

print("Training samples :", X_train_processed.shape[0])
print("Testing samples  :", X_test_processed.shape[0])
print("Input features   :", X_train_processed.shape[1])

print("\nPerformance distribution:")

print(
    df["performance_rating"]
    .value_counts()
    .sort_index()
)

print("\nSaved:")
print("processed_data/performance_X_train.npy")
print("processed_data/performance_X_test.npy")
print("processed_data/performance_y_train.npy")
print("processed_data/performance_y_test.npy")
print("artifacts/performance_preprocessor.pkl")
print("artifacts/performance_feature_names.csv")