from pathlib import Path

import numpy as np
import pandas as pd
from tensorflow import keras
from sklearn.metrics import (
    precision_score,
    recall_score,
    f1_score,
)


# ==========================================================
# PATHS
# ==========================================================

PROJECT_DIR = Path(__file__).resolve().parent

PROCESSED_DIR = PROJECT_DIR / "processed_data"
MODEL_DIR = PROJECT_DIR / "models"
RESULT_DIR = PROJECT_DIR / "results"

MODEL_PATH = MODEL_DIR / "attrition_deep_learning.keras"


# ==========================================================
# LOAD DATA
# ==========================================================

X_test = np.load(
    PROCESSED_DIR / "attrition_X_test.npy"
)

y_test = np.load(
    PROCESSED_DIR / "attrition_y_test.npy"
)


# ==========================================================
# LOAD MODEL
# ==========================================================

model = keras.models.load_model(
    MODEL_PATH
)


# ==========================================================
# PREDICT PROBABILITIES
# ==========================================================

probabilities = (
    model.predict(
        X_test,
        verbose=0
    )
    .ravel()
)


# ==========================================================
# TEST DIFFERENT THRESHOLDS
# ==========================================================

results = []

for threshold in np.arange(
    0.20,
    0.81,
    0.01
):

    predictions = (
        probabilities >= threshold
    ).astype(int)

    precision = precision_score(
        y_test,
        predictions,
        zero_division=0
    )

    recall = recall_score(
        y_test,
        predictions,
        zero_division=0
    )

    f1 = f1_score(
        y_test,
        predictions,
        zero_division=0
    )

    results.append(
        {
            "Threshold": round(
                float(threshold),
                2
            ),
            "Precision": precision,
            "Recall": recall,
            "F1": f1,
        }
    )


# ==========================================================
# RESULTS
# ==========================================================

results_df = pd.DataFrame(results)

results_df = results_df.sort_values(
    by="F1",
    ascending=False
)


print("=" * 70)
print("ATTRITION THRESHOLD OPTIMIZATION")
print("=" * 70)

print(
    results_df.head(10).to_string(
        index=False
    )
)


# ==========================================================
# BEST THRESHOLD
# ==========================================================

best_row = results_df.iloc[0]

print("\n" + "=" * 70)
print("BEST THRESHOLD")
print("=" * 70)

print(
    f"Threshold : {best_row['Threshold']:.2f}"
)

print(
    f"Precision : {best_row['Precision']:.4f}"
)

print(
    f"Recall    : {best_row['Recall']:.4f}"
)

print(
    f"F1 Score  : {best_row['F1']:.4f}"
)


# ==========================================================
# SAVE
# ==========================================================

RESULT_DIR.mkdir(
    exist_ok=True
)

results_df.to_csv(
    RESULT_DIR /
    "attrition_threshold_results.csv",
    index=False
)

with open(
    RESULT_DIR /
    "best_attrition_threshold.txt",
    "w"
) as file:

    file.write(
        str(best_row["Threshold"])
    )

print("\nSaved threshold results.")