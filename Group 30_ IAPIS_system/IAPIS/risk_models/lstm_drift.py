"""
LSTM Sensor Drift Detection Model

Implements DL Unit IV — RNN/LSTM sequence learning applied to sensor time-series.
Selective forget/write gates allow the model to retain long-range temperature
trend while ignoring short noise spikes.

Uses a sliding-window approach on hourly sensor data to predict whether
equipment is at risk of thermal drift in the next 6 hours.
"""

import os
import logging
from typing import Dict, Optional

import numpy as np
import pandas as pd
import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader
from sklearn.preprocessing import StandardScaler
import pickle

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
WINDOW_SIZE = 24  # 24 hours lookback
PREDICTION_HORIZON = 6  # Predict drift risk in next 6 hours
DRIFT_TEMP_THRESHOLD = 85.0  # Temperature above this = drift risk
INPUT_SIZE = 3  # temperature_c, vibration_mm_s, rpm
HIDDEN_SIZE = 32
NUM_LAYERS = 2
DROPOUT = 0.2
LEARNING_RATE = 0.001
BATCH_SIZE = 32

MODELS_DIR = os.path.join(os.path.dirname(__file__), "..", "models_store")
MODEL_PATH = os.path.join(MODELS_DIR, "lstm_drift.pt")
SCALER_PATH = os.path.join(MODELS_DIR, "lstm_scaler.pkl")


# ---------------------------------------------------------------------------
# Model Definition
# ---------------------------------------------------------------------------
class DriftLSTM(nn.Module):
    """
    LSTM model for sensor drift detection.
    
    Architecture:
    - Input: (batch, seq_len=24, features=3) — temperature, vibration, rpm
    - 2-layer LSTM with hidden size 32
    - Linear head: hidden -> 1 (sigmoid) for binary drift risk classification
    
    Implements DL Unit IV — RNN/LSTM sequence learning. The selective
    forget/write gates allow the model to retain long-range temperature
    trend while ignoring short noise spikes.
    """
    
    def __init__(
        self,
        input_size: int = INPUT_SIZE,
        hidden_size: int = HIDDEN_SIZE,
        num_layers: int = NUM_LAYERS,
        dropout: float = DROPOUT,
    ):
        super(DriftLSTM, self).__init__()
        
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        
        self.lstm = nn.LSTM(
            input_size=input_size,
            hidden_size=hidden_size,
            num_layers=num_layers,
            batch_first=True,
            dropout=dropout if num_layers > 1 else 0,
        )
        
        self.classifier = nn.Sequential(
            nn.Linear(hidden_size, 16),
            nn.ReLU(),
            nn.Dropout(dropout),
            nn.Linear(16, 1),
        )
    
    def forward(self, x):
        """
        Forward pass.
        
        Args:
            x: (batch, seq_len, input_size) sensor readings
        
        Returns:
            (batch, 1) drift risk probability
        """
        # LSTM output: (batch, seq_len, hidden_size)
        lstm_out, (h_n, c_n) = self.lstm(x)
        
        # Use the last hidden state for classification
        last_hidden = lstm_out[:, -1, :]  # (batch, hidden_size)
        
        # Classify
        risk = self.classifier(last_hidden)  # (batch, 1)
        return risk


# ---------------------------------------------------------------------------
# Dataset
# ---------------------------------------------------------------------------
class SensorDataset(Dataset):
    """Sliding-window dataset for sensor time-series."""
    
    def __init__(self, features: np.ndarray, labels: np.ndarray):
        self.features = torch.FloatTensor(features)
        self.labels = torch.FloatTensor(labels)
    
    def __len__(self):
        return len(self.features)
    
    def __getitem__(self, idx):
        return self.features[idx], self.labels[idx]


def _create_sequences(
    df: pd.DataFrame,
    window_size: int = WINDOW_SIZE,
    horizon: int = PREDICTION_HORIZON,
    threshold: float = DRIFT_TEMP_THRESHOLD,
) -> tuple:
    """
    Create sliding-window sequences and binary drift labels.
    
    For each window of `window_size` hours, the label is 1 if the maximum
    temperature in the next `horizon` hours exceeds the threshold.
    """
    feature_cols = ["temperature_c", "vibration_mm_s", "rpm"]
    
    sequences = []
    labels = []
    
    for eq_id in df["equipment_id"].unique():
        eq_data = df[df["equipment_id"] == eq_id].sort_values("timestamp").reset_index(drop=True)
        values = eq_data[feature_cols].values
        
        for i in range(len(values) - window_size - horizon):
            # Input window
            window = values[i : i + window_size]
            
            # Label: max temperature in the prediction horizon
            future_temps = values[i + window_size : i + window_size + horizon, 0]
            label = 1.0 if future_temps.max() > threshold else 0.0
            
            sequences.append(window)
            labels.append(label)
    
    return np.array(sequences), np.array(labels).reshape(-1, 1)


# ---------------------------------------------------------------------------
# Training
# ---------------------------------------------------------------------------
def train_lstm(csv_path: str = None, epochs: int = 15) -> Dict:
    """
    Train the LSTM drift detection model.
    
    Args:
        csv_path: Path to sensor_logs.csv
        epochs: Number of training epochs
    
    Returns:
        Dict with training metrics
    """
    if csv_path is None:
        csv_path = os.path.join(os.path.dirname(__file__), "..", "data", "sensor_logs.csv")
    
    logger.info(f"Loading sensor data from {csv_path}")
    df = pd.read_csv(csv_path)
    
    # Create labels from RAW (unscaled) temperatures so the 85°C threshold is meaningful
    feature_cols = ["temperature_c", "vibration_mm_s", "rpm"]
    X, y = _create_sequences(df)
    logger.info(f"Created {len(X)} sequences (positive rate: {y.mean():.2%})")
    
    # Now fit scaler on the raw feature columns and re-create sequences with scaled features
    scaler = StandardScaler()
    df_scaled = df.copy()
    df_scaled[feature_cols] = scaler.fit_transform(df[feature_cols])
    
    # Re-create sequences with scaled features (but keep the same raw-data labels)
    X_scaled, _ = _create_sequences(df_scaled)
    X = X_scaled  # Use scaled features for training
    
    # Train/val split (80/20)
    split_idx = int(len(X) * 0.8)
    X_train, X_val = X[:split_idx], X[split_idx:]
    y_train, y_val = y[:split_idx], y[split_idx:]
    
    train_dataset = SensorDataset(X_train, y_train)
    val_dataset = SensorDataset(X_val, y_val)
    
    train_loader = DataLoader(train_dataset, batch_size=BATCH_SIZE, shuffle=True)
    val_loader = DataLoader(val_dataset, batch_size=BATCH_SIZE, shuffle=False)
    
    # Model, loss, optimizer
    model = DriftLSTM()
    
    # Handle class imbalance with pos_weight (ratio of negatives to positives)
    pos_count = y_train.sum()
    neg_count = len(y_train) - pos_count
    pos_weight_val = neg_count / max(pos_count, 1)
    pos_weight_tensor = torch.FloatTensor([pos_weight_val])
    logger.info(f"Class balance: {int(pos_count)} positives, {int(neg_count)} negatives, pos_weight={pos_weight_val:.2f}")
    
    criterion = nn.BCEWithLogitsLoss(pos_weight=pos_weight_tensor)
    optimizer = torch.optim.Adam(model.parameters(), lr=LEARNING_RATE)
    
    # Training loop — save best model based on RECALL (not val_loss)
    # because with extreme imbalance, lowest loss = predict-all-zeros
    best_recall = -1.0
    metrics = {"train_loss": [], "val_loss": [], "val_accuracy": []}
    
    for epoch in range(epochs):
        # Train
        model.train()
        train_loss = 0.0
        for batch_X, batch_y in train_loader:
            optimizer.zero_grad()
            output = model(batch_X)
            loss = criterion(output, batch_y)
            loss.backward()
            optimizer.step()
            train_loss += loss.item()
        
        train_loss /= len(train_loader)
        
        # Validate
        model.eval()
        val_loss = 0.0
        correct = 0
        total = 0
        all_preds = []
        all_labels = []
        
        with torch.no_grad():
            for batch_X, batch_y in val_loader:
                output = model(batch_X)
                loss = criterion(output, batch_y)
                val_loss += loss.item()
                
                # Apply sigmoid for predictions (BCEWithLogitsLoss uses raw logits)
                probs = torch.sigmoid(output)
                preds = (probs >= 0.5).float()
                correct += (preds == batch_y).sum().item()
                total += batch_y.size(0)
                
                all_preds.extend(preds.numpy().flatten())
                all_labels.extend(batch_y.numpy().flatten())
        
        val_loss /= len(val_loader)
        val_accuracy = correct / total if total > 0 else 0
        
        # Compute recall for positive class
        all_preds = np.array(all_preds)
        all_labels = np.array(all_labels)
        true_pos = ((all_preds == 1) & (all_labels == 1)).sum()
        actual_pos = (all_labels == 1).sum()
        recall = true_pos / actual_pos if actual_pos > 0 else 0.0
        
        metrics["train_loss"].append(train_loss)
        metrics["val_loss"].append(val_loss)
        metrics["val_accuracy"].append(val_accuracy)
        
        logger.info(
            f"Epoch {epoch+1}/{epochs}: "
            f"train_loss={train_loss:.4f} val_loss={val_loss:.4f} "
            f"val_acc={val_accuracy:.4f} recall={recall:.4f}"
        )
        
        # Save best model by recall (what we actually care about)
        if recall > best_recall:
            best_recall = recall
            os.makedirs(MODELS_DIR, exist_ok=True)
            torch.save(model.state_dict(), MODEL_PATH)
            with open(SCALER_PATH, "wb") as f:
                pickle.dump(scaler, f)
    
    logger.info(f"Training complete. Best recall={best_recall:.4f}")
    logger.info(f"Model saved to {MODEL_PATH}")
    
    metrics["final_recall"] = float(recall)
    return metrics


# ---------------------------------------------------------------------------
# Inference
# ---------------------------------------------------------------------------
def predict_drift_risk(
    equipment_id: str,
    recent_window: pd.DataFrame,
) -> Dict:
    """
    Predict drift risk for a given equipment based on recent sensor readings.
    
    Args:
        equipment_id: Equipment identifier (e.g., "M-12")
        recent_window: DataFrame with columns [temperature_c, vibration_mm_s, rpm],
                       at least WINDOW_SIZE rows of recent readings.
    
    Returns:
        {equipment_id, risk_score: float 0-1, flag: bool}
    """
    # Load model
    model = DriftLSTM()
    if os.path.exists(MODEL_PATH):
        model.load_state_dict(torch.load(MODEL_PATH, map_location="cpu", weights_only=True))
    else:
        logger.warning(f"LSTM model not found at {MODEL_PATH}. Returning default risk.")
        return {"equipment_id": equipment_id, "risk_score": 0.0, "flag": False}
    
    model.eval()
    
    # Load scaler
    if os.path.exists(SCALER_PATH):
        with open(SCALER_PATH, "rb") as f:
            scaler = pickle.load(f)
    else:
        logger.warning("LSTM scaler not found. Using unscaled features.")
        scaler = None
    
    # Prepare input
    feature_cols = ["temperature_c", "vibration_mm_s", "rpm"]
    window_data = recent_window[feature_cols].values
    
    if len(window_data) < WINDOW_SIZE:
        # Pad with the first row repeated
        pad_size = WINDOW_SIZE - len(window_data)
        padding = np.tile(window_data[0], (pad_size, 1))
        window_data = np.vstack([padding, window_data])
    
    window_data = window_data[-WINDOW_SIZE:]  # Take last WINDOW_SIZE readings
    
    if scaler is not None:
        window_data = scaler.transform(window_data)
    
    # Predict
    input_tensor = torch.FloatTensor(window_data).unsqueeze(0)  # (1, seq_len, features)
    
    with torch.no_grad():
        logits = model(input_tensor)
        risk_score = torch.sigmoid(logits).item()
    
    return {
        "equipment_id": equipment_id,
        "risk_score": round(risk_score, 4),
        "flag": risk_score >= 0.5,
    }


def predict_all_equipment(csv_path: str = None) -> Dict[str, Dict]:
    """
    Predict drift risk for all equipment in the sensor logs.
    
    Returns:
        Dict mapping equipment_id -> {risk_score, flag}
    """
    if csv_path is None:
        csv_path = os.path.join(os.path.dirname(__file__), "..", "data", "sensor_logs.csv")
    
    df = pd.read_csv(csv_path)
    results = {}
    
    for eq_id in df["equipment_id"].unique():
        eq_data = df[df["equipment_id"] == eq_id].sort_values("timestamp")
        # Use the last WINDOW_SIZE readings
        recent = eq_data.tail(WINDOW_SIZE)
        result = predict_drift_risk(eq_id, recent)
        results[eq_id] = result
    
    return results


if __name__ == "__main__":
    train_lstm()
    
    # Test predictions
    results = predict_all_equipment()
    print("\nDrift risk predictions:")
    for eq_id, result in results.items():
        flag_str = "[!] AT RISK" if result["flag"] else "[OK] Normal"
        print(f"  {eq_id}: score={result['risk_score']:.4f} {flag_str}")
