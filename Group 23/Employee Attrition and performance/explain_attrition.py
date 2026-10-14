from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import shap
import matplotlib.pyplot as plt

from tensorflow import keras


# ==========================================================
# PATHS
# ==========================================================

PROJECT_DIR = Path(__file__).resolve().parent

PROCESSED_DIR = PROJECT_DIR / "processed_data"
ARTIFACT_DIR = PROJECT_DIR / "artifacts"
MODEL_DIR = PROJECT_DIR / "models"
RESULT_DIR = PROJECT_DIR / "results"

MODEL_PATH = MODEL_DIR / "attrition_deep_learning.keras"
PREPROCESSOR_PATH = ARTIFACT_DIR / "attrition_preprocessor.pkl"
FEATURE_NAMES_PATH = ARTIFACT_DIR / "attrition_feature_names.csv"

RESULT_DIR.mkdir(exist_ok=True)


# ==========================================================
# LOAD MODEL
# ==========================================================

print("=" * 70)
print("ATTRITION EXPLAINABLE AI (SHAP)")
print("=" * 70)

print("\nLoading model...")

model = keras.models.load_model(
    MODEL_PATH
)

print("Model loaded successfully.")


# ==========================================================
# LOAD PREPROCESSOR
# ==========================================================

print("\nLoading preprocessor...")

preprocessor = joblib.load(
    PREPROCESSOR_PATH
)

print("Preprocessor loaded successfully.")


# ==========================================================
# LOAD FEATURE NAMES
# ==========================================================

feature_names = pd.read_csv(
    FEATURE_NAMES_PATH
).iloc[:, 0].tolist()

print(
    f"\nNumber of processed features: "
    f"{len(feature_names)}"
)


# ==========================================================
# LOAD TEST DATA
# ==========================================================

X_test = np.load(
    PROCESSED_DIR / "attrition_X_test.npy"
)

y_test = np.load(
    PROCESSED_DIR / "attrition_y_test.npy"
)

print(
    f"Test samples: {X_test.shape[0]}"
)


# ==========================================================
# PREDICTION FUNCTION
# ==========================================================

def model_predict(X):
    """
    SHAP-compatible prediction function.

    Input:
        Processed feature matrix

    Output:
        Attrition probability
    """

    X = np.asarray(
        X,
        dtype=np.float32
    )

    return model.predict(
        X,
        verbose=0
    ).reshape(-1)


# ==========================================================
# CREATE BACKGROUND DATASET
# ==========================================================

# SHAP does not need all 4000 training samples.
# A smaller representative background dataset
# keeps computation faster.

background_size = min(
    100,
    X_test.shape[0]
)

background_data = X_test[
    :background_size
]


# ==========================================================
# CREATE EXPLAINER
# ==========================================================

print("\nCreating SHAP explainer...")

explainer = shap.KernelExplainer(
    model_predict,
    background_data
)

print("SHAP explainer created.")


# ==========================================================
# EXPLAIN TEST SAMPLES
# ==========================================================

sample_size = min(
    100,
    X_test.shape[0]
)

X_sample = X_test[
    :sample_size
]

y_sample = y_test[
    :sample_size
]


print(
    f"\nCalculating SHAP values for "
    f"{sample_size} employees..."
)

shap_values = explainer.shap_values(
    X_sample,
    nsamples=100
)

# SHAP can return a list in some versions.
if isinstance(shap_values, list):
    shap_values = shap_values[0]

shap_values = np.asarray(
    shap_values
)


print(
    "SHAP calculation completed."
)


# ==========================================================
# GLOBAL FEATURE IMPORTANCE
# ==========================================================

mean_abs_shap = np.mean(
    np.abs(shap_values),
    axis=0
)

importance_df = pd.DataFrame(
    {
        "Feature": feature_names,
        "Mean_Absolute_SHAP": mean_abs_shap
    }
)

importance_df = importance_df.sort_values(
    by="Mean_Absolute_SHAP",
    ascending=False
).reset_index(drop=True)


# ==========================================================
# PRINT TOP FEATURES
# ==========================================================

print("\n" + "=" * 70)
print("TOP ATTRITION FEATURES")
print("=" * 70)

print(
    importance_df.head(20).to_string(
        index=False
    )
)


# ==========================================================
# SAVE GLOBAL IMPORTANCE
# ==========================================================

importance_df.to_csv(
    RESULT_DIR / "attrition_shap_feature_importance.csv",
    index=False
)


# ==========================================================
# GLOBAL FEATURE IMPORTANCE PLOT
# ==========================================================

top_n = 15

top_features = importance_df.head(
    top_n
).sort_values(
    by="Mean_Absolute_SHAP"
)


plt.figure(
    figsize=(10, 7)
)

plt.barh(
    top_features["Feature"],
    top_features["Mean_Absolute_SHAP"]
)

plt.xlabel(
    "Mean Absolute SHAP Value"
)

plt.ylabel(
    "Feature"
)

plt.title(
    "Top Features Influencing Employee Attrition"
)

plt.tight_layout()

plt.savefig(
    RESULT_DIR / "attrition_shap_feature_importance.png",
    dpi=300,
    bbox_inches="tight"
)

plt.show()


# ==========================================================
# INDIVIDUAL EMPLOYEE EXPLANATION
# ==========================================================

employee_index = 0

employee_features = X_sample[
    employee_index
]

employee_shap = shap_values[
    employee_index
]

employee_probability = model_predict(
    employee_features.reshape(1, -1)
)[0]


# ==========================================================
# INDIVIDUAL FEATURE CONTRIBUTIONS
# ==========================================================

individual_df = pd.DataFrame(
    {
        "Feature": feature_names,
        "SHAP_Value": employee_shap,
        "Absolute_SHAP": np.abs(
            employee_shap
        )
    }
)

individual_df = individual_df.sort_values(
    by="Absolute_SHAP",
    ascending=False
).reset_index(drop=True)


# ==========================================================
# DISPLAY INDIVIDUAL EXPLANATION
# ==========================================================

print("\n" + "=" * 70)
print("INDIVIDUAL EMPLOYEE EXPLANATION")
print("=" * 70)

print(
    f"Employee test index: "
    f"{employee_index}"
)

print(
    f"Actual attrition: "
    f"{'Yes' if y_sample[employee_index] == 1 else 'No'}"
)

print(
    f"Predicted attrition probability: "
    f"{employee_probability:.2%}"
)


print("\nTop contributing features:")

print(
    individual_df[
        [
            "Feature",
            "SHAP_Value"
        ]
    ]
    .head(10)
    .to_string(index=False)
)


# ==========================================================
# SAVE INDIVIDUAL EXPLANATION
# ==========================================================

individual_df.to_csv(
    RESULT_DIR /
    "attrition_employee_0_shap.csv",
    index=False
)


# ==========================================================
# POSITIVE / NEGATIVE CONTRIBUTIONS
# ==========================================================

positive = (
    individual_df[
        individual_df["SHAP_Value"] > 0
    ]
    .head(10)
)

negative = (
    individual_df[
        individual_df["SHAP_Value"] < 0
    ]
    .sort_values(
        by="SHAP_Value"
    )
    .head(10)
)


print("\nFactors increasing attrition risk:")

print(
    positive[
        ["Feature", "SHAP_Value"]
    ].to_string(
        index=False
    )
)


print("\nFactors reducing attrition risk:")

print(
    negative[
        ["Feature", "SHAP_Value"]
    ].to_string(
        index=False
    )
)


print("\n" + "=" * 70)
print("SHAP ANALYSIS COMPLETED")
print("=" * 70)

print("\nGenerated files:")

print(
    "results/attrition_shap_feature_importance.csv"
)

print(
    "results/attrition_shap_feature_importance.png"
)

print(
    "results/attrition_employee_0_shap.csv"
)