# ==========================================================
# train_hr_classifier.py
#
# HR Document Classification using:
#   TF-IDF
#   Support Vector Machine (SVM)
# ==========================================================

from pathlib import Path

import joblib
import pandas as pd

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.svm import LinearSVC
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
)


# ==========================================================
# PATHS
# ==========================================================

PROJECT_DIR = Path(__file__).resolve().parent

HR_DOCUMENT_DIR = (
    PROJECT_DIR / "hr_documents"
)

IR_ARTIFACT_DIR = (
    PROJECT_DIR / "ir_artifacts"
)

MODEL_DIR = (
    PROJECT_DIR / "models"
)

RESULT_DIR = (
    PROJECT_DIR / "results"
)

MODEL_DIR.mkdir(exist_ok=True)
RESULT_DIR.mkdir(exist_ok=True)
IR_ARTIFACT_DIR.mkdir(exist_ok=True)


# ==========================================================
# LOAD DOCUMENTS
# ==========================================================

def load_documents():

    documents = []

    # Each subfolder represents a class/category
    category_folders = [
        folder
        for folder in HR_DOCUMENT_DIR.iterdir()
        if folder.is_dir()
    ]

    if not category_folders:

        raise ValueError(
            f"No category folders found in "
            f"{HR_DOCUMENT_DIR}"
        )

    for category_folder in sorted(
        category_folders
    ):

        category = category_folder.name

        for file_path in sorted(
            category_folder.glob("*.txt")
        ):

            try:

                with open(
                    file_path,
                    "r",
                    encoding="utf-8",
                    errors="replace"
                ) as file:

                    text = file.read().strip()

                if not text:
                    continue

                documents.append(
                    {
                        "document": file_path.name,
                        "category": category,
                        "text": text,
                    }
                )

            except Exception as error:

                print(
                    f"Could not read "
                    f"{file_path}: {error}"
                )

    return pd.DataFrame(
        documents
    )


# ==========================================================
# MAIN
# ==========================================================

def main():

    print("=" * 70)
    print("HR DOCUMENT CLASSIFICATION - SVM")
    print("=" * 70)

    # ------------------------------------------------------
    # Load data
    # ------------------------------------------------------

    df = load_documents()

    if df.empty:

        raise ValueError(
            "No documents available for training."
        )

    print(
        f"\nTotal documents: {len(df)}"
    )

    print(
        "\nDocuments per category:"
    )

    print(
        df["category"]
        .value_counts()
        .sort_index()
        .to_string()
    )

    # ------------------------------------------------------
    # Validate dataset size
    # ------------------------------------------------------

    category_counts = (
        df["category"]
        .value_counts()
    )

    insufficient_categories = (
        category_counts[
            category_counts < 2
        ]
    )

    if not insufficient_categories.empty:

        print(
            "\nWARNING:"
        )

        print(
            "The following categories have fewer "
            "than 2 documents:"
        )

        print(
            insufficient_categories
            .to_string()
        )

        print(
            "\nSVM training requires more documents "
            "per category for meaningful evaluation."
        )

        print(
            "\nAdd at least 3-5 documents per category "
            "and run this script again."
        )

        return

    # ------------------------------------------------------
    # Prepare data
    # ------------------------------------------------------

    X = df["text"]

    y = df["category"]

    # ------------------------------------------------------
    # Train/test split
    # ------------------------------------------------------

    X_train, X_test, y_train, y_test = (
        train_test_split(
            X,
            y,
            test_size=0.25,
            random_state=42,
            stratify=y
        )
    )

    print(
        f"\nTraining documents: "
        f"{len(X_train)}"
    )

    print(
        f"Testing documents: "
        f"{len(X_test)}"
    )

    # ------------------------------------------------------
    # TF-IDF + SVM
    # ------------------------------------------------------

    classifier = Pipeline(
        steps=[

            (
                "tfidf",
                TfidfVectorizer(
                    lowercase=True,
                    stop_words="english",
                    ngram_range=(1, 2),
                    min_df=1,
                    sublinear_tf=True
                )
            ),

            (
                "svm",
                LinearSVC(
                    C=1.0,
                    class_weight="balanced",
                    random_state=42
                )
            )
        ]
    )

    # ------------------------------------------------------
    # Train
    # ------------------------------------------------------

    print(
        "\nTraining TF-IDF + SVM..."
    )

    classifier.fit(
        X_train,
        y_train
    )

    print(
        "Training completed."
    )

    # ------------------------------------------------------
    # Predict
    # ------------------------------------------------------

    y_pred = classifier.predict(
        X_test
    )

    # ------------------------------------------------------
    # Evaluation
    # ------------------------------------------------------

    accuracy = accuracy_score(
        y_test,
        y_pred
    )

    print(
        "\n" + "=" * 70
    )

    print(
        "CLASSIFICATION RESULTS"
    )

    print(
        "=" * 70
    )

    print(
        f"\nAccuracy: {accuracy:.4f}"
    )

    print(
        "\nClassification Report:"
    )

    print(
        classification_report(
            y_test,
            y_pred,
            zero_division=0
        )
    )

    # ------------------------------------------------------
    # Confusion Matrix
    # ------------------------------------------------------

    labels = sorted(
        df["category"].unique()
    )

    cm = confusion_matrix(
        y_test,
        y_pred,
        labels=labels
    )

    confusion_df = pd.DataFrame(
        cm,
        index=[
            f"Actual_{label}"
            for label in labels
        ],
        columns=[
            f"Predicted_{label}"
            for label in labels
        ]
    )

    print(
        "\nConfusion Matrix:"
    )

    print(
        confusion_df
    )

    # ------------------------------------------------------
    # Save model
    # ------------------------------------------------------

    model_path = (
        MODEL_DIR /
        "hr_document_svm_classifier.pkl"
    )

    joblib.dump(
        classifier,
        model_path
    )

    print(
        f"\nModel saved to:"
    )

    print(
        model_path
    )

    # ------------------------------------------------------
    # Save test results
    # ------------------------------------------------------

    prediction_results = pd.DataFrame(
        {
            "document": df.loc[
                y_test.index,
                "document"
            ].values,

            "actual_category":
                y_test.values,

            "predicted_category":
                y_pred,
        }
    )

    prediction_results.to_csv(
        RESULT_DIR /
        "hr_document_classification_results.csv",
        index=False
    )

    confusion_df.to_csv(
        RESULT_DIR /
        "hr_document_confusion_matrix.csv"
    )

    # ------------------------------------------------------
    # Save classifier metadata
    # ------------------------------------------------------

    metadata = {
        "model": "LinearSVC",
        "vectorizer": "TF-IDF",
        "categories": labels,
        "accuracy": float(accuracy),
        "training_documents": len(X_train),
        "testing_documents": len(X_test),
    }

    joblib.dump(
        metadata,
        IR_ARTIFACT_DIR /
        "hr_classifier_metadata.pkl"
    )

    print(
        "\nClassification results saved."
    )

    print(
        "\n" + "=" * 70
    )

    print(
        "SVM CLASSIFIER TRAINING COMPLETED"
    )

    print(
        "=" * 70
    )


# ==========================================================
# RUN
# ==========================================================

if __name__ == "__main__":

    main()