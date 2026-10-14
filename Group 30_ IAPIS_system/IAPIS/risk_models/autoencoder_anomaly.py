"""
Autoencoder Anomaly Detection for Maintenance Logs

Implements DL Unit V — deep autoencoder for anomaly detection, directly
analogous to the course's network-traffic anomaly-detection case study,
re-applied to maintenance-log feature vectors.

Trained only on "normal" maintenance logs (is_anomalous_label == 0).
Anomalies are detected by high reconstruction error (mean + 2*std threshold).
"""

import os
import logging
from typing import Dict, List

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
FEATURE_COLS = ["vibration_rms", "temp_delta", "oil_pressure", "run_hours_since_service"]
INPUT_DIM = len(FEATURE_COLS)  # 4
ENCODING_DIM = 3
HIDDEN_DIM = 8
LEARNING_RATE = 0.001
BATCH_SIZE = 32
THRESHOLD_MULTIPLIER = 2.0  # threshold = mean + THRESHOLD_MULTIPLIER * std

MODELS_DIR = os.path.join(os.path.dirname(__file__), "..", "models_store")
MODEL_PATH = os.path.join(MODELS_DIR, "autoencoder.pt")
SCALER_PATH = os.path.join(MODELS_DIR, "ae_scaler.pkl")
THRESHOLD_PATH = os.path.join(MODELS_DIR, "ae_threshold.pkl")


# ---------------------------------------------------------------------------
# Model Definition
# ---------------------------------------------------------------------------
class LogAutoencoder(nn.Module):
    """
    Dense autoencoder for maintenance log anomaly detection.
    
    Architecture:
    - Encoder: 4 → 8 → 3 (compress to latent space)
    - Decoder: 3 → 8 → 4 (reconstruct)
    
    Implements DL Unit V — deep autoencoder for anomaly detection.
    Reconstruction error is used as the anomaly score. Normal data
    is reconstructed well (low error); anomalous data produces high error.
    """
    
    def __init__(self, input_dim: int = INPUT_DIM, hidden_dim: int = HIDDEN_DIM, encoding_dim: int = ENCODING_DIM):
        super(LogAutoencoder, self).__init__()
        
        self.encoder = nn.Sequential(
            nn.Linear(input_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, encoding_dim),
            nn.ReLU(),
        )
        
        self.decoder = nn.Sequential(
            nn.Linear(encoding_dim, hidden_dim),
            nn.ReLU(),
            nn.Linear(hidden_dim, input_dim),
        )
    
    def forward(self, x):
        encoded = self.encoder(x)
        decoded = self.decoder(encoded)
        return decoded
    
    def encode(self, x):
        """Get the latent representation (useful for visualization)."""
        return self.encoder(x)


# ---------------------------------------------------------------------------
# Dataset
# ---------------------------------------------------------------------------
class MaintenanceDataset(Dataset):
    def __init__(self, features: np.ndarray):
        self.features = torch.FloatTensor(features)
    
    def __len__(self):
        return len(self.features)
    
    def __getitem__(self, idx):
        return self.features[idx]


# ---------------------------------------------------------------------------
# Training
# ---------------------------------------------------------------------------
def train_autoencoder(csv_path: str = None, epochs: int = 50) -> Dict:
    """
    Train the autoencoder on normal maintenance logs.
    
    Training is UNSUPERVISED on normal data only (is_anomalous_label == 0).
    The threshold for anomaly detection is set based on the training
    reconstruction error distribution: threshold = mean + 2*std.
    
    Args:
        csv_path: Path to maintenance_logs.csv
        epochs: Number of training epochs
    
    Returns:
        Dict with training metrics
    """
    if csv_path is None:
        csv_path = os.path.join(os.path.dirname(__file__), "..", "data", "maintenance_logs.csv")
    
    logger.info(f"Loading maintenance logs from {csv_path}")
    df = pd.read_csv(csv_path)
    
    # Split: train on normal only, validate on all
    normal_df = df[df["is_anomalous_label"] == 0]
    
    # Fit scaler on normal data only
    scaler = StandardScaler()
    normal_features = scaler.fit_transform(normal_df[FEATURE_COLS].values)
    
    # 80/20 split for normal data
    split_idx = int(len(normal_features) * 0.8)
    train_features = normal_features[:split_idx]
    val_normal_features = normal_features[split_idx:]
    
    # Also prepare all data for threshold computation
    all_features = scaler.transform(df[FEATURE_COLS].values)
    all_labels = df["is_anomalous_label"].values
    
    train_dataset = MaintenanceDataset(train_features)
    train_loader = DataLoader(train_dataset, batch_size=BATCH_SIZE, shuffle=True)
    
    # Model, loss, optimizer
    model = LogAutoencoder()
    criterion = nn.MSELoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=LEARNING_RATE)
    
    # Training loop
    best_val_loss = float("inf")
    metrics = {"train_loss": [], "val_loss": []}
    
    for epoch in range(epochs):
        # Train
        model.train()
        train_loss = 0.0
        for batch in train_loader:
            optimizer.zero_grad()
            output = model(batch)
            loss = criterion(output, batch)
            loss.backward()
            optimizer.step()
            train_loss += loss.item()
        
        train_loss /= len(train_loader)
        
        # Validate on held-out normal data
        model.eval()
        with torch.no_grad():
            val_tensor = torch.FloatTensor(val_normal_features)
            val_output = model(val_tensor)
            val_loss = criterion(val_output, val_tensor).item()
        
        metrics["train_loss"].append(train_loss)
        metrics["val_loss"].append(val_loss)
        
        if (epoch + 1) % 10 == 0 or epoch == 0:
            logger.info(f"Epoch {epoch+1}/{epochs}: train_loss={train_loss:.6f} val_loss={val_loss:.6f}")
        
        if val_loss < best_val_loss:
            best_val_loss = val_loss
    
    # Compute threshold from training reconstruction errors
    model.eval()
    with torch.no_grad():
        train_tensor = torch.FloatTensor(train_features)
        train_output = model(train_tensor)
        train_errors = torch.mean((train_output - train_tensor) ** 2, dim=1).numpy()
    
    threshold = float(train_errors.mean() + THRESHOLD_MULTIPLIER * train_errors.std())
    
    # Save model, scaler, and threshold
    os.makedirs(MODELS_DIR, exist_ok=True)
    torch.save(model.state_dict(), MODEL_PATH)
    with open(SCALER_PATH, "wb") as f:
        pickle.dump(scaler, f)
    with open(THRESHOLD_PATH, "wb") as f:
        pickle.dump(threshold, f)
    
    # Compute AUC on full dataset
    with torch.no_grad():
        all_tensor = torch.FloatTensor(all_features)
        all_output = model(all_tensor)
        all_errors = torch.mean((all_output - all_tensor) ** 2, dim=1).numpy()
    
    try:
        from sklearn.metrics import roc_auc_score
        auc = roc_auc_score(all_labels, all_errors)
        metrics["auc"] = float(auc)
        logger.info(f"AUC on full dataset: {auc:.4f}")
    except Exception as e:
        logger.warning(f"Could not compute AUC: {e}")
        metrics["auc"] = None
    
    logger.info(f"Training complete. Threshold={threshold:.6f}")
    logger.info(f"Model saved to {MODEL_PATH}")
    
    metrics["threshold"] = threshold
    return metrics


# ---------------------------------------------------------------------------
# Inference
# ---------------------------------------------------------------------------
def score_anomaly(log_row: dict) -> Dict:
    """
    Score a single maintenance log entry for anomaly.
    
    Args:
        log_row: dict with keys matching FEATURE_COLS
                 (vibration_rms, temp_delta, oil_pressure, run_hours_since_service)
    
    Returns:
        {log_id, reconstruction_error: float, is_anomalous: bool}
    """
    # Load model
    model = LogAutoencoder()
    if os.path.exists(MODEL_PATH):
        model.load_state_dict(torch.load(MODEL_PATH, map_location="cpu", weights_only=True))
    else:
        logger.warning(f"Autoencoder model not found at {MODEL_PATH}.")
        return {
            "log_id": log_row.get("log_id", "unknown"),
            "reconstruction_error": 0.0,
            "is_anomalous": False,
        }
    
    model.eval()
    
    # Load scaler and threshold
    if os.path.exists(SCALER_PATH):
        with open(SCALER_PATH, "rb") as f:
            scaler = pickle.load(f)
    else:
        scaler = None
    
    if os.path.exists(THRESHOLD_PATH):
        with open(THRESHOLD_PATH, "rb") as f:
            threshold = pickle.load(f)
    else:
        threshold = 0.5  # Default
    
    # Prepare features
    features = np.array([[
        log_row.get("vibration_rms", 0.0),
        log_row.get("temp_delta", 0.0),
        log_row.get("oil_pressure", 0.0),
        log_row.get("run_hours_since_service", 0),
    ]], dtype=np.float32)
    
    if scaler is not None:
        features = scaler.transform(features)
    
    # Compute reconstruction error
    with torch.no_grad():
        input_tensor = torch.FloatTensor(features)
        output = model(input_tensor)
        error = torch.mean((output - input_tensor) ** 2).item()
    
    return {
        "log_id": log_row.get("log_id", "unknown"),
        "reconstruction_error": round(error, 6),
        "is_anomalous": error > threshold,
    }


def score_all_logs(csv_path: str = None) -> List[Dict]:
    """Score all maintenance logs for anomalies."""
    if csv_path is None:
        csv_path = os.path.join(os.path.dirname(__file__), "..", "data", "maintenance_logs.csv")
    
    df = pd.read_csv(csv_path)
    results = []
    
    for _, row in df.iterrows():
        result = score_anomaly(row.to_dict())
        results.append(result)
    
    anomaly_count = sum(1 for r in results if r["is_anomalous"])
    logger.info(f"Scored {len(results)} logs: {anomaly_count} flagged as anomalous")
    
    return results


if __name__ == "__main__":
    metrics = train_autoencoder()
    print(f"\nTraining metrics: AUC={metrics.get('auc', 'N/A')}, threshold={metrics['threshold']:.6f}")
    
    # Test scoring
    results = score_all_logs()
    anomalies = [r for r in results if r["is_anomalous"]]
    print(f"\nAnomalies detected: {len(anomalies)} / {len(results)}")
