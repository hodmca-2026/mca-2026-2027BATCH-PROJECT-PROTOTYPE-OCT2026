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

DATASET_PATH = PROJECT_DIR / "employee_attrition_hr_2026.csv"
PROCESSED_DIR = PROJECT_DIR / "processed_data"
ARTIFACT_DIR = PROJECT_DIR / "artifacts"

PROCESSED_DIR.mkdir(exist_ok=True)
ARTIFACT_DIR.mkdir(exist_ok=True)


# ==========================================================
# LOAD DATA
# ==========================================================

df = pd.read_csv(DATASET_PATH)

print("=" * 70)
print("DATASET INFORMATION")
print("=" * 70)

print(f"Shape: {df.shape}")
print("\nColumns:")
print(df.columns.tolist())

print("\nMissing values:")
print(df.isnull().sum().sum())

print("\nDuplicate rows:")
print(df.duplicated().sum())


# ==========================================================
# BASIC CLEANING
# ==========================================================

# Remove duplicate rows
df = df.drop_duplicates().reset_index(drop=True)

# Remove duplicate employee IDs if any
df = df.drop_duplicates(subset=["employee_id"]).reset_index(drop=True)


# ==========================================================
# REMOVE ID COLUMN
# ==========================================================

# employee_id is only an identifier.
# It should NOT be given to the ML/DL model.

df = df.drop(columns=["employee_id"])


# ==========================================================
# CLEAN BOOLEAN COLUMN
# ==========================================================

# Convert True/False -> 1/0
df["uses_ai_tools_at_work"] = (
    df["uses_ai_tools_at_work"]
    .astype(int)
)


# ==========================================================
# CLEAN TARGET COLUMN
# ==========================================================

# Attrition:
# No  -> 0
# Yes -> 1

df["attrition"] = (
    df["attrition"]
    .map({"No": 0, "Yes": 1})
)

if df["attrition"].isnull().any():
    raise ValueError("Unexpected values found in attrition column.")


# ==========================================================
# CHECK PERFORMANCE TARGET
# ==========================================================

if "performance_rating" not in df.columns:
    raise ValueError(
        "performance_rating column was not found in the dataset."
    )


# ==========================================================
# SEPARATE TARGETS
# ==========================================================

# We keep performance_rating as a separate prediction target.
# Do NOT use performance_rating as an input feature for attrition
# unless you explicitly decide that this rating is available
# at prediction time.

X = df.drop(columns=["attrition"])

y_attrition = df["attrition"]


# ==========================================================
# FEATURES
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
# VALIDATE FEATURES
# ==========================================================

all_expected_features = categorical_features + numeric_features

missing_features = [
    col for col in all_expected_features
    if col not in X.columns
]

if missing_features:
    raise ValueError(
        f"Missing expected features: {missing_features}"
    )


# ==========================================================
# TRAIN / TEST SPLIT
# ==========================================================

X_train, X_test, y_train, y_test = train_test_split(
    X,
    y_attrition,
    test_size=0.20,
    random_state=42,
    stratify=y_attrition
)


# ==========================================================
# PREPROCESSING PIPELINE
# ==========================================================

numeric_pipeline = Pipeline(
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


categorical_pipeline = Pipeline(
    steps=[
        (
            "imputer",
            SimpleImputer(strategy="most_frequent")
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
            numeric_pipeline,
            numeric_features
        ),
        (
            "categorical",
            categorical_pipeline,
            categorical_features
        ),
    ],
    remainder="drop"
)


# ==========================================================
# FIT ON TRAINING DATA ONLY
# ==========================================================

X_train_processed = preprocessor.fit_transform(X_train)

X_test_processed = preprocessor.transform(X_test)


# ==========================================================
# CONVERT TO NUMPY FLOAT32
# ==========================================================

X_train_processed = np.asarray(
    X_train_processed,
    dtype=np.float32
)

X_test_processed = np.asarray(
    X_test_processed,
    dtype=np.float32
)


y_train = np.asarray(
    y_train,
    dtype=np.float32
)

y_test = np.asarray(
    y_test,
    dtype=np.float32
)


# ==========================================================
# SAVE PROCESSED DATA
# ==========================================================

np.save(
    PROCESSED_DIR / "X_train.npy",
    X_train_processed
)

np.save(
    PROCESSED_DIR / "X_test.npy",
    X_test_processed
)

np.save(
    PROCESSED_DIR / "y_train.npy",
    y_train
)

np.save(
    PROCESSED_DIR / "y_test.npy",
    y_test
)


# ==========================================================
# SAVE PREPROCESSOR
# ==========================================================

joblib.dump(
    preprocessor,
    ARTIFACT_DIR / "preprocessor.pkl"
)


# ==========================================================
# SAVE FEATURE NAMES
# ==========================================================

feature_names = preprocessor.get_feature_names_out()

pd.Series(feature_names).to_csv(
    ARTIFACT_DIR / "processed_feature_names.csv",
    index=False,
    header=["feature"]
)


# ==========================================================
# SUMMARY
# ==========================================================

print("\n" + "=" * 70)
print("PREPROCESSING COMPLETED")
print("=" * 70)

print(f"Original rows: {len(df)}")
print(f"Training rows: {len(X_train_processed)}")
print(f"Testing rows : {len(X_test_processed)}")
print(f"Processed features: {X_train_processed.shape[1]}")

print("\nAttrition distribution:")
print(
    pd.Series(y_attrition)
    .value_counts()
    .rename(index={0: "No", 1: "Yes"})
)

print("\nSaved files:")

print(PROCESSED_DIR / "X_train.npy")
print(PROCESSED_DIR / "X_test.npy")
print(PROCESSED_DIR / "y_train.npy")
print(PROCESSED_DIR / "y_test.npy")
print(ARTIFACT_DIR / "preprocessor.pkl")
print(ARTIFACT_DIR / "processed_feature_names.csv")
