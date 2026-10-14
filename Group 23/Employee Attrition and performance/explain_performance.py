# ==========================================================
# explain_performance.py
# Explainable AI (SHAP) for Employee Performance Prediction
# ==========================================================

from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import shap

from tensorflow import keras


# ==========================================================
# PATHS
# ==========================================================

PROJECT_DIR = Path(__file__).resolve().parent

PROCESSED_DIR = PROJECT_DIR / "processed_data"
ARTIFACT_DIR = PROJECT_DIR / "artifacts"
MODEL_DIR = PROJECT_DIR / "models"
RESULT_DIR = PROJECT_DIR / "results"

MODEL_PATH = (
    MODEL_DIR /
    "performance_deep_learning.keras"
)

FEATURE_NAMES_PATH = (
    ARTIFACT_DIR /
    "performance_feature_names.csv"
)

RESULT_DIR.mkdir(exist_ok=True)


# ==========================================================
# PERFORMANCE CLASS MAPPING
# ==========================================================

CLASS_TO_RATING = {
    0: 2,
    1: 3,
    2: 4,
    3: 5,
}


# ==========================================================
# LOAD MODEL
# ==========================================================

print("=" * 70)
print("PERFORMANCE EXPLAINABLE AI (SHAP)")
print("=" * 70)

print("\nLoading performance model...")

model = keras.models.load_model(
    MODEL_PATH
)

print("Model loaded successfully.")


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
    PROCESSED_DIR /
    "performance_X_test.npy"
)

y_test = np.load(
    PROCESSED_DIR /
    "performance_y_test.npy"
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

    Returns probability for:
        Class 0 -> Rating 2
        Class 1 -> Rating 3
        Class 2 -> Rating 4
        Class 3 -> Rating 5
    """

    X = np.asarray(
        X,
        dtype=np.float32
    )

    return model.predict(
        X,
        verbose=0
    )


# ==========================================================
# CREATE BACKGROUND DATA
# ==========================================================

# Use a limited number of examples to keep Kernel SHAP
# computation manageable.

background_size = min(
    100,
    X_test.shape[0]
)

background_data = X_test[
    :background_size
]


# ==========================================================
# CREATE SHAP EXPLAINER
# ==========================================================

print("\nCreating SHAP explainer...")

explainer = shap.KernelExplainer(
    model_predict,
    background_data
)

print("SHAP explainer created.")


# ==========================================================
# SELECT SAMPLES TO EXPLAIN
# ==========================================================

sample_size = min(
    50,
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


# ==========================================================
# CALCULATE SHAP VALUES
# ==========================================================

shap_values = explainer.shap_values(
    X_sample,
    nsamples=100
)

print("SHAP calculation completed.")


# ==========================================================
# HANDLE SHAP OUTPUT FORMAT
# ==========================================================

shap_values = np.asarray(
    shap_values
)

print(
    "SHAP values shape:",
    shap_values.shape
)


# Depending on the SHAP version, multiclass output may be:

# Shape A:
# (samples, features, classes)

# Shape B:
# (classes, samples, features)

# We convert it to:
# (samples, features, classes)

if shap_values.ndim != 3:
    raise ValueError(
        "Unexpected SHAP output shape: "
        f"{shap_values.shape}"
    )


if shap_values.shape[0] == len(X_sample):

    # Already:
    # samples, features, classes

    shap_values_normalized = shap_values

elif shap_values.shape[1] == len(X_sample):

    # Currently:
    # classes, samples, features

    shap_values_normalized = np.transpose(
        shap_values,
        (1, 2, 0)
    )

else:

    raise ValueError(
        "Unable to determine SHAP output format."
    )


# ==========================================================
# GLOBAL FEATURE IMPORTANCE
# ==========================================================

# Average absolute SHAP across:
# samples and classes

mean_abs_shap = np.mean(
    np.abs(
        shap_values_normalized
    ),
    axis=(0, 2)
)


global_importance = pd.DataFrame(
    {
        "Feature": feature_names,
        "Mean_Absolute_SHAP": mean_abs_shap,
    }
)

global_importance = (
    global_importance
    .sort_values(
        by="Mean_Absolute_SHAP",
        ascending=False
    )
    .reset_index(drop=True)
)


# ==========================================================
# PRINT TOP FEATURES
# ==========================================================

print("\n" + "=" * 70)
print("TOP FEATURES INFLUENCING PERFORMANCE")
print("=" * 70)

print(
    global_importance
    .head(20)
    .to_string(index=False)
)


# ==========================================================
# SAVE GLOBAL IMPORTANCE
# ==========================================================

global_importance.to_csv(
    RESULT_DIR /
    "performance_shap_feature_importance.csv",
    index=False
)


# ==========================================================
# GLOBAL FEATURE IMPORTANCE PLOT
# ==========================================================

top_n = 15

top_features = (
    global_importance
    .head(top_n)
    .sort_values(
        by="Mean_Absolute_SHAP"
    )
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
    "Top Features Influencing Employee Performance"
)

plt.tight_layout()

plt.savefig(
    RESULT_DIR /
    "performance_shap_feature_importance.png",
    dpi=300,
    bbox_inches="tight"
)

plt.show()


# ==========================================================
# INDIVIDUAL EMPLOYEE EXPLANATION
# ==========================================================

employee_index = 0

employee_features = (
    X_sample[
        employee_index
    ]
)

employee_shap = (
    shap_values_normalized[
        employee_index
    ]
)


# ==========================================================
# MODEL PREDICTION
# ==========================================================

employee_probabilities = model_predict(
    employee_features.reshape(1, -1)
)[0]


predicted_class = int(
    np.argmax(
        employee_probabilities
    )
)

predicted_rating = CLASS_TO_RATING[
    predicted_class
]

actual_class = int(
    y_sample[
        employee_index
    ]
)

actual_rating = CLASS_TO_RATING[
    actual_class
]


# ==========================================================
# INDIVIDUAL SHAP VALUES FOR PREDICTED CLASS
# ==========================================================

# Select SHAP values corresponding to
# the predicted performance class.

employee_class_shap = (
    employee_shap[
        :,
        predicted_class
    ]
)


individual_df = pd.DataFrame(
    {
        "Feature": feature_names,
        "SHAP_Value": employee_class_shap,
        "Absolute_SHAP": np.abs(
            employee_class_shap
        ),
    }
)


individual_df = (
    individual_df
    .sort_values(
        by="Absolute_SHAP",
        ascending=False
    )
    .reset_index(drop=True)
)


# ==========================================================
# DISPLAY INDIVIDUAL EXPLANATION
# ==========================================================

print("\n" + "=" * 70)
print("INDIVIDUAL EMPLOYEE PERFORMANCE EXPLANATION")
print("=" * 70)

print(
    f"Employee test index : {employee_index}"
)

print(
    f"Actual rating       : {actual_rating}"
)

print(
    f"Predicted rating    : {predicted_rating}"
)

print("\nPrediction probabilities:")

for class_id, probability in enumerate(
    employee_probabilities
):

    rating = CLASS_TO_RATING[
        class_id
    ]

    print(
        f"Rating {rating}: "
        f"{probability:.2%}"
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
# FACTORS INCREASING PERFORMANCE PREDICTION
# ==========================================================

positive_factors = (
    individual_df[
        individual_df["SHAP_Value"] > 0
    ]
    .sort_values(
        by="SHAP_Value",
        ascending=False
    )
    .head(10)
)


# ==========================================================
# FACTORS DECREASING PERFORMANCE PREDICTION
# ==========================================================

negative_factors = (
    individual_df[
        individual_df["SHAP_Value"] < 0
    ]
    .sort_values(
        by="SHAP_Value",
        ascending=True
    )
    .head(10)
)


print(
    "\nFactors increasing predicted performance:"
)

if len(positive_factors) > 0:

    print(
        positive_factors[
            [
                "Feature",
                "SHAP_Value"
            ]
        ].to_string(
            index=False
        )
    )

else:

    print("No positive factors found.")


print(
    "\nFactors decreasing predicted performance:"
)

if len(negative_factors) > 0:

    print(
        negative_factors[
            [
                "Feature",
                "SHAP_Value"
            ]
        ].to_string(
            index=False
        )
    )

else:

    print("No negative factors found.")


# ==========================================================
# SAVE INDIVIDUAL EXPLANATION
# ==========================================================

individual_df.to_csv(
    RESULT_DIR /
    "performance_employee_0_shap.csv",
    index=False
)


# ==========================================================
# CLASS-SPECIFIC GLOBAL IMPORTANCE
# ==========================================================

print("\n" + "=" * 70)
print("CLASS-SPECIFIC SHAP ANALYSIS")
print("=" * 70)


for class_id in range(4):

    rating = CLASS_TO_RATING[
        class_id
    ]

    class_shap = (
        shap_values_normalized[
            :,
            :,
            class_id
        ]
    )

    class_importance = np.mean(
        np.abs(class_shap),
        axis=0
    )

    class_df = pd.DataFrame(
        {
            "Feature": feature_names,
            "Mean_Absolute_SHAP": class_importance,
        }
    )

    class_df = (
        class_df
        .sort_values(
            by="Mean_Absolute_SHAP",
            ascending=False
        )
        .reset_index(drop=True)
    )

    print(
        f"\nTop factors for Rating {rating}:"
    )

    print(
        class_df
        .head(10)
        .to_string(index=False)
    )

    class_df.to_csv(
        RESULT_DIR /
        f"performance_rating_{rating}_shap.csv",
        index=False
    )


# ==========================================================
# FINAL MESSAGE
# ==========================================================

print("\n" + "=" * 70)
print("PERFORMANCE SHAP ANALYSIS COMPLETED")
print("=" * 70)

print("\nGenerated files:")

print(
    "results/performance_shap_feature_importance.csv"
)

print(
    "results/performance_shap_feature_importance.png"
)

print(
    "results/performance_employee_0_shap.csv"
)

print(
    "results/performance_rating_2_shap.csv"
)

print(
    "results/performance_rating_3_shap.csv"
)

print(
    "results/performance_rating_4_shap.csv"
)

print(
    "results/performance_rating_5_shap.csv"
)