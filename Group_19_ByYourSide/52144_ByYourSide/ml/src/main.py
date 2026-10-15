from pathlib import Path

import joblib
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel


BASE_DIR = Path(__file__).resolve().parent.parent
MODEL_DIR = BASE_DIR / "models"

MODEL_PATH = MODEL_DIR / "checkon_text_classifier.joblib"
VECTORIZER_PATH = MODEL_DIR / "checkon_tfidf_vectorizer.joblib"

model = joblib.load(MODEL_PATH)
vectorizer = joblib.load(VECTORIZER_PATH)

app = FastAPI(title="ByYourSide ML Service")


class PredictionRequest(BaseModel):
    text: str


@app.get("/health")
def health():
    return {
        "status": "ok",
        "message": "ByYourSide ML service is running",
    }


@app.post("/predict")
def predict(request: PredictionRequest):
    text = request.text.strip()

    if not text:
        raise HTTPException(
            status_code=400,
            detail="Text is required",
        )

    transformed_text = vectorizer.transform([text])
    prediction = model.predict(transformed_text)[0]

    return {
        "prediction": str(prediction),
    }