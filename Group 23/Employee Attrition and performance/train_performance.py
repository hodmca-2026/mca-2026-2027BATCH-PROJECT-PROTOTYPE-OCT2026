# ==========================================================
# train_performance.py
# Employee Performance Prediction
# ==========================================================

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
# PROJECT PATHS
# ==========================================================

PROJECT_DIR = Path(__file__).resolve().parent

PROCESSED_DIR = PROJECT_DIR / "processed_data"
MODEL_DIR = PROJECT_DIR / "models"
RESULT_DIR = PROJECT_DIR / "results"

MODEL_DIR.mkdir(exist_ok=True)
RESULT_DIR.mkdir(exist_ok=True)


# ==========================================================
# LOAD DATA
# ==========================================================

print("=" * 70)
print("EMPLOYEE PERFORMANCE MODEL TRAINING")
print("=" * 70)

X_train = np.load(
    PROCESSED_DIR / "performance_X_train.npy"
)

X_test = np.load(
    PROCESSED_DIR / "performance_X_test.npy"
)

y_train = np.load(
    PROCESSED_DIR / "performance_y_train.npy"
)

y_test = np.load(
    PROCESSED_DIR / "performance_y_test.npy"
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
print("PERFORMANCE CLASS DISTRIBUTION")
print("=" * 70)

class_names = {
    0: "Rating 2",
    1: "Rating 3",
    2: "Rating 4",
    3: "Rating 5",
}

for class_id in sorted(np.unique(y_train)):
    print(
        f"Class {class_id} "
        f"({class_names.get(class_id, str(class_id))}): "
        f"{np.sum(y_train == class_id)}"
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
# EVALUATION FUNCTION
# ==========================================================

def evaluate_model(
    model_name,
    y_true,
    y_pred
):
    """
    Evaluate a multiclass performance model.
    """

    accuracy = accuracy_score(
        y_true,
        y_pred
    )

    precision_macro = precision_score(
        y_true,
        y_pred,
        average="macro",
        zero_division=0
    )

    recall_macro = recall_score(
        y_true,
        y_pred,
        average="macro",
        zero_division=0
    )

    f1_macro = f1_score(
        y_true,
        y_pred,
        average="macro",
        zero_division=0
    )

    f1_weighted = f1_score(
        y_true,
        y_pred,
        average="weighted",
        zero_division=0
    )

    print("\n" + "-" * 70)
    print(model_name)
    print("-" * 70)

    print(f"Accuracy      : {accuracy:.4f}")
    print(f"Macro Precision: {precision_macro:.4f}")
    print(f"Macro Recall   : {recall_macro:.4f}")
    print(f"Macro F1       : {f1_macro:.4f}")
    print(f"Weighted F1    : {f1_weighted:.4f}")

    print("\nClassification Report:")

    print(
        classification_report(
            y_true,
            y_pred,
            labels=[0, 1, 2, 3],
            target_names=[
                "Rating 2",
                "Rating 3",
                "Rating 4",
                "Rating 5",
            ],
            zero_division=0
        )
    )

    return {
        "Model": model_name,
        "Accuracy": accuracy,
        "Macro_Precision": precision_macro,
        "Macro_Recall": recall_macro,
        "Macro_F1": f1_macro,
        "Weighted_F1": f1_weighted,
    }


# ==========================================================
# 1. LOGISTIC REGRESSION
# ==========================================================

print("\n" + "=" * 70)
print("TRAINING LOGISTIC REGRESSION")
print("=" * 70)

logistic_model = LogisticRegression(
    max_iter=3000,
    class_weight="balanced",
    random_state=RANDOM_STATE
)

logistic_model.fit(
    X_train,
    y_train
)

logistic_prediction = logistic_model.predict(
    X_test
)

logistic_results = evaluate_model(
    "Logistic Regression",
    y_test,
    logistic_prediction
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

rf_prediction = random_forest_model.predict(
    X_test
)

rf_results = evaluate_model(
    "Random Forest",
    y_test,
    rf_prediction
)


# ==========================================================
# 3. DEEP NEURAL NETWORK
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
            4,
            activation="softmax"
        ),
    ]
)


# ==========================================================
# COMPILE DNN
# ==========================================================

dnn_model.compile(
    optimizer=keras.optimizers.Adam(
        learning_rate=0.001
    ),
    loss="sparse_categorical_crossentropy",
    metrics=[
        "accuracy"
    ]
)

print("\nModel architecture:")

dnn_model.summary()


# ==========================================================
# CALLBACKS
# ==========================================================

early_stopping = keras.callbacks.EarlyStopping(
    monitor="val_loss",
    mode="min",
    patience=12,
    restore_best_weights=True,
    verbose=1
)

reduce_lr = keras.callbacks.ReduceLROnPlateau(
    monitor="val_loss",
    mode="min",
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

dnn_probability = dnn_model.predict(
    X_test,
    verbose=0
)

dnn_prediction = np.argmax(
    dnn_probability,
    axis=1
)


# ==========================================================
# EVALUATE DNN
# ==========================================================

dnn_results = evaluate_model(
    "Deep Neural Network",
    y_test,
    dnn_prediction
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
    by="Macro_F1",
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
    RESULT_DIR /
    "performance_model_comparison.csv",
    index=False
)


# ==========================================================
# SAVE MODELS
# ==========================================================

joblib.dump(
    logistic_model,
    MODEL_DIR /
    "performance_logistic_regression.pkl"
)

joblib.dump(
    random_forest_model,
    MODEL_DIR /
    "performance_random_forest.pkl"
)

dnn_model.save(
    MODEL_DIR /
    "performance_deep_learning.keras"
)


# ==========================================================
# SAVE TRAINING HISTORY
# ==========================================================

history_df = pd.DataFrame(
    history.history
)

history_df.to_csv(
    RESULT_DIR /
    "performance_training_history.csv",
    index=False
)


# ==========================================================
# DNN CONFUSION MATRIX
# ==========================================================

cm = confusion_matrix(
    y_test,
    dnn_prediction,
    labels=[0, 1, 2, 3]
)

print("\n" + "=" * 70)
print("DNN CONFUSION MATRIX")
print("=" * 70)

print(cm)


plt.figure(
    figsize=(8, 7)
)

disp = ConfusionMatrixDisplay(
    confusion_matrix=cm,
    display_labels=[
        "Rating 2",
        "Rating 3",
        "Rating 4",
        "Rating 5",
    ]
)

disp.plot(
    values_format="d"
)

plt.title(
    "Deep Neural Network - Performance Confusion Matrix"
)

plt.tight_layout()

plt.savefig(
    RESULT_DIR /
    "performance_confusion_matrix.png",
    dpi=300
)

plt.show()


# ==========================================================
# TRAINING LOSS CURVE
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
    "Performance Model Loss"
)

plt.xlabel("Epoch")

plt.ylabel("Loss")

plt.legend()

plt.tight_layout()

plt.savefig(
    RESULT_DIR /
    "performance_loss_curve.png",
    dpi=300
)

plt.show()


# ==========================================================
# TRAINING ACCURACY CURVE
# ==========================================================

plt.figure(
    figsize=(8, 5)
)

plt.plot(
    history.history["accuracy"],
    label="Training Accuracy"
)

plt.plot(
    history.history["val_accuracy"],
    label="Validation Accuracy"
)

plt.title(
    "Performance Model Accuracy"
)

plt.xlabel("Epoch")

plt.ylabel("Accuracy")

plt.legend()

plt.tight_layout()

plt.savefig(
    RESULT_DIR /
    "performance_accuracy_curve.png",
    dpi=300
)

plt.show()


# ==========================================================
# BEST MODEL
# ==========================================================

best_model_name = results.iloc[0]["Model"]

print("\n" + "=" * 70)
print("BEST PERFORMANCE MODEL")
print("=" * 70)

print(
    "Best model based on Macro F1:",
    best_model_name
)

print("\nSaved models:")
print(
    MODEL_DIR /
    "performance_logistic_regression.pkl"
)

print(
    MODEL_DIR /
    "performance_random_forest.pkl"
)

print(
    MODEL_DIR /
    "performance_deep_learning.keras"
)

print("\nTraining completed successfully!")