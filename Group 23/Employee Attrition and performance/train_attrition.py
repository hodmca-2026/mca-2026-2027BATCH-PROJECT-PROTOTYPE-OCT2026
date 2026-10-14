from pathlib import Path

import joblib
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    classification_report,
    confusion_matrix,
    ConfusionMatrixDisplay,
)
from sklearn.utils.class_weight import compute_class_weight

import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers


# ==========================================================
# CONFIGURATION
# ==========================================================

RANDOM_STATE = 42
EPOCHS = 100
BATCH_SIZE = 32

np.random.seed(RANDOM_STATE)
tf.random.set_seed(RANDOM_STATE)


# ==========================================================
# PATHS
# ==========================================================

PROJECT_DIR = Path(__file__).resolve().parent

PROCESSED_DIR = PROJECT_DIR / "processed_data"
ARTIFACT_DIR = PROJECT_DIR / "artifacts"
MODEL_DIR = PROJECT_DIR / "models"
RESULT_DIR = PROJECT_DIR / "results"

MODEL_DIR.mkdir(exist_ok=True)
RESULT_DIR.mkdir(exist_ok=True)


# ==========================================================
# LOAD PROCESSED DATA
# ==========================================================

print("=" * 70)
print("EMPLOYEE ATTRITION MODEL TRAINING")
print("=" * 70)

X_train = np.load(
    PROCESSED_DIR / "attrition_X_train.npy"
)

X_test = np.load(
    PROCESSED_DIR / "attrition_X_test.npy"
)

y_train = np.load(
    PROCESSED_DIR / "attrition_y_train.npy"
)

y_test = np.load(
    PROCESSED_DIR / "attrition_y_test.npy"
)


print("\nData loaded successfully")

print("X_train shape:", X_train.shape)
print("X_test shape :", X_test.shape)
print("y_train shape:", y_train.shape)
print("y_test shape :", y_test.shape)


# ==========================================================
# CLASS DISTRIBUTION
# ==========================================================

print("\n" + "=" * 70)
print("CLASS DISTRIBUTION")
print("=" * 70)

print(
    "Training - No Attrition:",
    int(np.sum(y_train == 0))
)

print(
    "Training - Attrition:",
    int(np.sum(y_train == 1))
)

print(
    "Testing - No Attrition:",
    int(np.sum(y_test == 0))
)

print(
    "Testing - Attrition:",
    int(np.sum(y_test == 1))
)


# ==========================================================
# CLASS WEIGHTS
# ==========================================================

classes = np.unique(y_train)

weights = compute_class_weight(
    class_weight="balanced",
    classes=classes,
    y=y_train
)

class_weights = {
    int(cls): float(weight)
    for cls, weight in zip(classes, weights)
}

print("\nClass weights:")
print(class_weights)


# ==========================================================
# HELPER FUNCTION
# ==========================================================

def evaluate_model(
    model_name,
    y_true,
    y_pred,
    y_probability
):
    """
    Calculate classification metrics.
    """

    accuracy = accuracy_score(
        y_true,
        y_pred
    )

    precision = precision_score(
        y_true,
        y_pred,
        zero_division=0
    )

    recall = recall_score(
        y_true,
        y_pred,
        zero_division=0
    )

    f1 = f1_score(
        y_true,
        y_pred,
        zero_division=0
    )

    auc = roc_auc_score(
        y_true,
        y_probability
    )

    print("\n" + "-" * 70)
    print(model_name)
    print("-" * 70)

    print(f"Accuracy : {accuracy:.4f}")
    print(f"Precision: {precision:.4f}")
    print(f"Recall   : {recall:.4f}")
    print(f"F1 Score : {f1:.4f}")
    print(f"ROC-AUC  : {auc:.4f}")

    print("\nClassification Report:")
    print(
        classification_report(
            y_true,
            y_pred,
            target_names=[
                "No Attrition",
                "Attrition"
            ],
            zero_division=0
        )
    )

    return {
        "Model": model_name,
        "Accuracy": accuracy,
        "Precision": precision,
        "Recall": recall,
        "F1_Score": f1,
        "ROC_AUC": auc,
    }


# ==========================================================
# 1. LOGISTIC REGRESSION
# ==========================================================

print("\n" + "=" * 70)
print("TRAINING LOGISTIC REGRESSION")
print("=" * 70)

logistic_model = LogisticRegression(
    max_iter=2000,
    class_weight="balanced",
    random_state=RANDOM_STATE
)

logistic_model.fit(
    X_train,
    y_train
)

logistic_probability = (
    logistic_model
    .predict_proba(X_test)[:, 1]
)

logistic_prediction = (
    logistic_probability >= 0.5
).astype(int)

logistic_results = evaluate_model(
    "Logistic Regression",
    y_test,
    logistic_prediction,
    logistic_probability
)


# ==========================================================
# 2. RANDOM FOREST
# ==========================================================

print("\n" + "=" * 70)
print("TRAINING RANDOM FOREST")
print("=" * 70)

random_forest_model = RandomForestClassifier(
    n_estimators=300,
    max_depth=None,
    min_samples_split=2,
    min_samples_leaf=1,
    class_weight="balanced",
    random_state=RANDOM_STATE,
    n_jobs=-1
)

random_forest_model.fit(
    X_train,
    y_train
)

rf_probability = (
    random_forest_model
    .predict_proba(X_test)[:, 1]
)

rf_prediction = (
    rf_probability >= 0.5
).astype(int)

rf_results = evaluate_model(
    "Random Forest",
    y_test,
    rf_prediction,
    rf_probability
)


# ==========================================================
# 3. BUILD DEEP NEURAL NETWORK
# ==========================================================

print("\n" + "=" * 70)
print("BUILDING DEEP NEURAL NETWORK")
print("=" * 70)

input_features = X_train.shape[1]

dnn_model = keras.Sequential(
    [
        layers.Input(
            shape=(input_features,)
        ),

        layers.Dense(
            128,
            activation="relu"
        ),

        layers.BatchNormalization(),

        layers.Dropout(0.30),

        layers.Dense(
            64,
            activation="relu"
        ),

        layers.BatchNormalization(),

        layers.Dropout(0.30),

        layers.Dense(
            32,
            activation="relu"
        ),

        layers.Dropout(0.20),

        layers.Dense(
            1,
            activation="sigmoid"
        ),
    ]
)


# ==========================================================
# COMPILE
# ==========================================================

dnn_model.compile(
    optimizer=keras.optimizers.Adam(
        learning_rate=0.001
    ),
    loss="binary_crossentropy",
    metrics=[
        "accuracy",
        keras.metrics.Precision(
            name="precision"
        ),
        keras.metrics.Recall(
            name="recall"
        ),
        keras.metrics.AUC(
            name="auc"
        ),
    ]
)


print("\nModel architecture:")
dnn_model.summary()


# ==========================================================
# CALLBACKS
# ==========================================================

early_stopping = keras.callbacks.EarlyStopping(
    monitor="val_auc",
    mode="max",
    patience=12,
    restore_best_weights=True,
    verbose=1
)

reduce_lr = keras.callbacks.ReduceLROnPlateau(
    monitor="val_loss",
    factor=0.5,
    patience=5,
    min_lr=1e-6,
    verbose=1
)


# ==========================================================
# TRAIN DNN
# ==========================================================

print("\n" + "=" * 70)
print("TRAINING DEEP NEURAL NETWORK")
print("=" * 70)

history = dnn_model.fit(
    X_train,
    y_train,

    validation_split=0.20,

    epochs=EPOCHS,

    batch_size=BATCH_SIZE,

    class_weight=class_weights,

    callbacks=[
        early_stopping,
        reduce_lr
    ],

    verbose=1
)


# ==========================================================
# DNN PREDICTIONS
# ==========================================================

dnn_probability = (
    dnn_model
    .predict(
        X_test,
        verbose=0
    )
    .ravel()
)

dnn_prediction = (
    dnn_probability >= 0.5
).astype(int)


# ==========================================================
# EVALUATE DNN
# ==========================================================

dnn_results = evaluate_model(
    "Deep Neural Network",
    y_test,
    dnn_prediction,
    dnn_probability
)


# ==========================================================
# MODEL COMPARISON
# ==========================================================

results = pd.DataFrame(
    [
        logistic_results,
        rf_results,
        dnn_results,
    ]
)

results = results.sort_values(
    by="F1_Score",
    ascending=False
).reset_index(drop=True)


print("\n" + "=" * 70)
print("MODEL COMPARISON")
print("=" * 70)

print(
    results.to_string(
        index=False
    )
)


# ==========================================================
# SAVE RESULTS
# ==========================================================

results.to_csv(
    RESULT_DIR / "attrition_model_comparison.csv",
    index=False
)


# ==========================================================
# SAVE MODELS
# ==========================================================

joblib.dump(
    logistic_model,
    MODEL_DIR / "attrition_logistic_regression.pkl"
)

joblib.dump(
    random_forest_model,
    MODEL_DIR / "attrition_random_forest.pkl"
)

dnn_model.save(
    MODEL_DIR / "attrition_deep_learning.keras"
)


# ==========================================================
# SAVE DNN TRAINING HISTORY
# ==========================================================

history_df = pd.DataFrame(
    history.history
)

history_df.to_csv(
    RESULT_DIR / "attrition_training_history.csv",
    index=False
)


# ==========================================================
# CONFUSION MATRIX - DNN
# ==========================================================

cm = confusion_matrix(
    y_test,
    dnn_prediction
)

print("\n" + "=" * 70)
print("DNN CONFUSION MATRIX")
print("=" * 70)

print(cm)


plt.figure(
    figsize=(7, 6)
)

disp = ConfusionMatrixDisplay(
    confusion_matrix=cm,
    display_labels=[
        "No Attrition",
        "Attrition"
    ]
)

disp.plot(
    values_format="d"
)

plt.title(
    "Deep Neural Network - Attrition Confusion Matrix"
)

plt.tight_layout()

plt.savefig(
    RESULT_DIR / "attrition_confusion_matrix.png",
    dpi=300
)

plt.show()


# ==========================================================
# TRAINING CURVES
# ==========================================================

plt.figure(
    figsize=(8, 5)
)

plt.plot(
    history.history["loss"],
    label="Training Loss"
)

plt.plot(
    history.history["val_loss"],
    label="Validation Loss"
)

plt.title(
    "Attrition Model Loss"
)

plt.xlabel("Epoch")

plt.ylabel("Loss")

plt.legend()

plt.tight_layout()

plt.savefig(
    RESULT_DIR / "attrition_loss_curve.png",
    dpi=300
)

plt.show()


# ==========================================================
# AUC CURVE
# ==========================================================

plt.figure(
    figsize=(8, 5)
)

plt.plot(
    history.history["auc"],
    label="Training AUC"
)

plt.plot(
    history.history["val_auc"],
    label="Validation AUC"
)

plt.title(
    "Attrition Model AUC"
)

plt.xlabel("Epoch")

plt.ylabel("ROC-AUC")

plt.legend()

plt.tight_layout()

plt.savefig(
    RESULT_DIR / "attrition_auc_curve.png",
    dpi=300
)

plt.show()


# ==========================================================
# BEST MODEL
# ==========================================================

best_model_name = results.iloc[0]["Model"]

print("\n" + "=" * 70)
print("BEST MODEL")
print("=" * 70)

print(
    "Best model based on F1-score:",
    best_model_name
)

print("\nAll trained models are saved in:")
print(MODEL_DIR)

print("\nTraining completed successfully!")