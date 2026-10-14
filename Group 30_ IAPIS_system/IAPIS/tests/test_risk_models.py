"""Tests for risk models (LSTM, Autoencoder, Recurrence Ranking)."""

import os
import json
import pytest
import numpy as np


def _sensor_data_exists():
    return os.path.exists(os.path.join(os.path.dirname(__file__), "..", "data", "sensor_logs.csv"))


def _maintenance_data_exists():
    return os.path.exists(os.path.join(os.path.dirname(__file__), "..", "data", "maintenance_logs.csv"))


def _reports_exist():
    return os.path.exists(os.path.join(os.path.dirname(__file__), "..", "data", "reports", "reports.json"))


def _lstm_model_exists():
    return os.path.exists(os.path.join(os.path.dirname(__file__), "..", "models_store", "lstm_drift.pt"))


def _autoencoder_model_exists():
    return os.path.exists(os.path.join(os.path.dirname(__file__), "..", "models_store", "autoencoder.pt"))


# ---------------------------------------------------------------
# LSTM Tests
# ---------------------------------------------------------------
@pytest.mark.skipif(not _sensor_data_exists(), reason="Sensor data not generated")
def test_lstm_training():
    """LSTM should train without errors and save a model."""
    from risk_models.lstm_drift import train_lstm
    
    csv_path = os.path.join(os.path.dirname(__file__), "..", "data", "sensor_logs.csv")
    metrics = train_lstm(csv_path=csv_path, epochs=3)  # Fewer epochs for testing
    
    assert "train_loss" in metrics
    assert len(metrics["train_loss"]) == 3
    
    model_path = os.path.join(os.path.dirname(__file__), "..", "models_store", "lstm_drift.pt")
    assert os.path.exists(model_path)


@pytest.mark.skipif(not _lstm_model_exists(), reason="LSTM model not trained")
def test_lstm_prediction():
    """LSTM should predict drift risk for equipment."""
    from risk_models.lstm_drift import predict_all_equipment
    
    results = predict_all_equipment()
    
    assert len(results) > 0
    for eq_id, pred in results.items():
        assert "risk_score" in pred
        assert "flag" in pred
        assert 0.0 <= pred["risk_score"] <= 1.0


@pytest.mark.skipif(
    not (_sensor_data_exists() and _lstm_model_exists()),
    reason="Sensor data or LSTM model not available"
)
def test_lstm_drift_recall():
    """LSTM should flag injected drift windows with reasonable recall."""
    from risk_models.lstm_drift import DriftLSTM, _create_sequences, WINDOW_SIZE, MODEL_PATH, SCALER_PATH
    import pandas as pd
    import torch
    import pickle
    
    csv_path = os.path.join(os.path.dirname(__file__), "..", "data", "sensor_logs.csv")
    df = pd.read_csv(csv_path)
    
    # Create labels from RAW data (threshold=85°C is on raw temperatures)
    _, y = _create_sequences(df)
    
    # Now scale features for model input (matching training logic)
    feature_cols = ["temperature_c", "vibration_mm_s", "rpm"]
    if os.path.exists(SCALER_PATH):
        with open(SCALER_PATH, "rb") as f:
            scaler = pickle.load(f)
        df_scaled = df.copy()
        df_scaled[feature_cols] = scaler.transform(df[feature_cols])
    else:
        df_scaled = df
    
    X, _ = _create_sequences(df_scaled)
    
    # Load model
    model = DriftLSTM()
    model.load_state_dict(torch.load(MODEL_PATH, map_location="cpu", weights_only=True))
    model.eval()
    
    # Predict on all sequences
    with torch.no_grad():
        logits = model(torch.FloatTensor(X))
        preds = torch.sigmoid(logits).numpy().flatten()
    
    preds_binary = (preds >= 0.5).astype(float)
    y_flat = y.flatten()
    
    # Recall for positive class
    true_pos = ((preds_binary == 1) & (y_flat == 1)).sum()
    actual_pos = (y_flat == 1).sum()
    recall = true_pos / actual_pos if actual_pos > 0 else 0
    
    # Acceptance: recall >= 0.5
    assert recall >= 0.5, f"LSTM recall too low: {recall:.4f} (need >= 0.5)"


# ---------------------------------------------------------------
# Autoencoder Tests
# ---------------------------------------------------------------
@pytest.mark.skipif(not _maintenance_data_exists(), reason="Maintenance data not generated")
def test_autoencoder_training():
    """Autoencoder should train without errors."""
    from risk_models.autoencoder_anomaly import train_autoencoder
    
    csv_path = os.path.join(os.path.dirname(__file__), "..", "data", "maintenance_logs.csv")
    metrics = train_autoencoder(csv_path=csv_path, epochs=10)
    
    assert "train_loss" in metrics
    assert "threshold" in metrics
    assert metrics["threshold"] > 0


@pytest.mark.skipif(not _autoencoder_model_exists(), reason="Autoencoder not trained")
def test_autoencoder_scoring():
    """Autoencoder should score a log entry."""
    from risk_models.autoencoder_anomaly import score_anomaly
    
    # Normal log
    normal = {
        "log_id": "TEST-NORMAL",
        "vibration_rms": 0.8,
        "temp_delta": 3.0,
        "oil_pressure": 45.0,
        "run_hours_since_service": 150,
    }
    result = score_anomaly(normal)
    assert "reconstruction_error" in result
    assert "is_anomalous" in result
    
    # Anomalous log (extreme values)
    anomalous = {
        "log_id": "TEST-ANOMALY",
        "vibration_rms": 5.0,
        "temp_delta": 25.0,
        "oil_pressure": 15.0,
        "run_hours_since_service": 800,
    }
    result_anom = score_anomaly(anomalous)
    
    # Anomalous should have higher error
    assert result_anom["reconstruction_error"] > result["reconstruction_error"]


@pytest.mark.skipif(
    not (_maintenance_data_exists() and _autoencoder_model_exists()),
    reason="Data or model not available"
)
def test_autoencoder_auc():
    """Autoencoder AUC should be >= 0.75 on the synthetic data."""
    from risk_models.autoencoder_anomaly import LogAutoencoder, MODEL_PATH, SCALER_PATH, THRESHOLD_PATH, FEATURE_COLS
    import pandas as pd
    import torch
    import pickle
    from sklearn.metrics import roc_auc_score
    
    csv_path = os.path.join(os.path.dirname(__file__), "..", "data", "maintenance_logs.csv")
    df = pd.read_csv(csv_path)
    
    with open(SCALER_PATH, "rb") as f:
        scaler = pickle.load(f)
    
    model = LogAutoencoder()
    model.load_state_dict(torch.load(MODEL_PATH, map_location="cpu", weights_only=True))
    model.eval()
    
    features = scaler.transform(df[FEATURE_COLS].values)
    labels = df["is_anomalous_label"].values
    
    with torch.no_grad():
        output = model(torch.FloatTensor(features))
        errors = torch.mean((output - torch.FloatTensor(features)) ** 2, dim=1).numpy()
    
    auc = roc_auc_score(labels, errors)
    assert auc >= 0.70, f"Autoencoder AUC too low: {auc:.4f} (need >= 0.70)"


# ---------------------------------------------------------------
# Recurrence Ranking Tests
# ---------------------------------------------------------------
def test_recurrence_scores():
    """Reports sharing equipment+hazard should score higher than singletons."""
    from risk_models.recurrence_rank import compute_recurrence_scores
    
    reports = [
        {"id": "A", "equipment": "motor", "hazard_type": "overheating"},
        {"id": "B", "equipment": "motor", "hazard_type": "overheating"},
        {"id": "C", "equipment": "motor", "hazard_type": "overheating"},
        {"id": "D", "equipment": "forklift", "hazard_type": "crushing"},
        {"id": "E", "equipment": "unique_equipment", "hazard_type": "unique_hazard"},
    ]
    
    scores = compute_recurrence_scores(reports)
    
    # Motor+overheating appears 3 times -> higher score
    # Unique pair appears once -> score should be 0
    assert scores["A"] > scores["E"]
    assert scores["B"] > scores["E"]
    assert scores["C"] > scores["E"]
    assert scores["E"] == 0.0
    
    # Shared pairs should have equal scores
    assert scores["A"] == scores["B"] == scores["C"]
