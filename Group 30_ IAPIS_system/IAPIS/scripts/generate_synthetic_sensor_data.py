"""
Generate Synthetic Sensor Data

Produces:
1. sensor_logs.csv — hourly time-series for >=3 equipment IDs over >=30 days
   with injected "drift" windows (gradual temperature ramp).
2. maintenance_logs.csv — numeric feature vectors with ~10% injected anomalies.
"""

import os
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

# Seed for reproducibility
np.random.seed(42)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
EQUIPMENT_IDS = ["M-01", "M-05", "M-12", "M-15", "M-18"]
DAYS = 35  # >= 30 days
HOURS_PER_DAY = 24
TOTAL_HOURS = DAYS * HOURS_PER_DAY

# Baseline parameters per equipment (temperature_c, vibration_mm_s, rpm)
BASELINES = {
    "M-01": {"temp": 60.0, "vib": 1.0, "rpm": 1450},
    "M-05": {"temp": 55.0, "vib": 0.9, "rpm": 1480},
    "M-12": {"temp": 62.0, "vib": 1.1, "rpm": 1450},
    "M-15": {"temp": 58.0, "vib": 0.95, "rpm": 1470},
    "M-18": {"temp": 65.0, "vib": 1.2, "rpm": 1440},
}

# Drift injection config: each equipment gets 2 drift windows
# (start_hour_offset, duration_hours, temp_increase)
DRIFT_WINDOWS = {
    "M-01": [(120, 10, 35), (500, 8, 40)],
    "M-05": [(200, 12, 30), (600, 9, 38)],
    "M-12": [(80, 10, 45), (450, 12, 42)],
    "M-15": [(300, 8, 33), (700, 10, 36)],
    "M-18": [(150, 11, 40), (550, 9, 44)],
}

# Noise parameters
TEMP_NOISE_STD = 2.0
VIB_NOISE_STD = 0.15
RPM_NOISE_STD = 5.0

# Maintenance logs config
NUM_MAINTENANCE_LOGS = 300
ANOMALY_FRACTION = 0.10


def generate_sensor_logs(output_path=None):
    """Generate hourly sensor time-series with injected drift events."""
    if output_path is None:
        output_path = os.path.join(os.path.dirname(__file__), "..", "data", "sensor_logs.csv")
    
    rows = []
    start_time = datetime(2024, 1, 1, 0, 0, 0)
    
    for eq_id in EQUIPMENT_IDS:
        baseline = BASELINES[eq_id]
        drifts = DRIFT_WINDOWS[eq_id]
        
        # Generate baseline signals with sinusoidal daily pattern + noise
        for hour_idx in range(TOTAL_HOURS):
            timestamp = start_time + timedelta(hours=hour_idx)
            
            # Daily cycle: temperature slightly higher during afternoon
            daily_cycle = 3.0 * np.sin(2 * np.pi * (hour_idx % 24) / 24 - np.pi / 2)
            
            temp = baseline["temp"] + daily_cycle + np.random.normal(0, TEMP_NOISE_STD)
            vib = baseline["vib"] + np.random.normal(0, VIB_NOISE_STD)
            rpm = baseline["rpm"] + np.random.normal(0, RPM_NOISE_STD)
            
            # Inject drift if within a drift window
            for drift_start, drift_duration, drift_increase in drifts:
                if drift_start <= hour_idx < drift_start + drift_duration:
                    # Linear ramp within the drift window
                    progress = (hour_idx - drift_start) / drift_duration
                    temp += drift_increase * progress
                    # Vibration also increases during drift
                    vib += 2.0 * progress
                    # RPM may drop slightly
                    rpm -= 20 * progress
            
            # Clamp values to realistic ranges
            temp = max(30.0, temp)
            vib = max(0.1, vib)
            rpm = max(1000, rpm)
            
            rows.append({
                "timestamp": timestamp.isoformat(),
                "equipment_id": eq_id,
                "temperature_c": round(temp, 1),
                "vibration_mm_s": round(vib, 2),
                "rpm": round(rpm, 0),
            })
    
    df = pd.DataFrame(rows)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=False)
    print(f"Generated sensor_logs.csv: {len(df)} rows, {len(EQUIPMENT_IDS)} equipment IDs, {DAYS} days")
    print(f"  Drift windows injected per equipment: {len(drifts)}")
    return df


def generate_maintenance_logs(output_path=None):
    """Generate maintenance log feature vectors with ~10% injected anomalies."""
    if output_path is None:
        output_path = os.path.join(os.path.dirname(__file__), "..", "data", "maintenance_logs.csv")
    
    num_anomalies = int(NUM_MAINTENANCE_LOGS * ANOMALY_FRACTION)
    num_normal = NUM_MAINTENANCE_LOGS - num_anomalies
    
    rows = []
    
    # Normal logs
    for i in range(num_normal):
        eq_id = np.random.choice(EQUIPMENT_IDS)
        rows.append({
            "log_id": f"LOG-{i+1:04d}",
            "equipment_id": eq_id,
            "vibration_rms": round(np.random.normal(0.8, 0.15), 2),
            "temp_delta": round(np.random.normal(3.0, 1.0), 1),
            "oil_pressure": round(np.random.normal(45.0, 3.0), 1),
            "run_hours_since_service": int(np.random.normal(150, 40)),
            "is_anomalous_label": 0,
        })
    
    # Anomalous logs (outlier values)
    for i in range(num_anomalies):
        eq_id = np.random.choice(EQUIPMENT_IDS)
        anomaly_type = np.random.choice(["high_vib", "high_temp", "low_pressure", "long_run", "multi"])
        
        vib = round(np.random.normal(0.8, 0.15), 2)
        temp_d = round(np.random.normal(3.0, 1.0), 1)
        oil_p = round(np.random.normal(45.0, 3.0), 1)
        run_h = int(np.random.normal(150, 40))
        
        if anomaly_type == "high_vib":
            vib = round(np.random.uniform(2.5, 5.0), 2)
        elif anomaly_type == "high_temp":
            temp_d = round(np.random.uniform(12.0, 25.0), 1)
        elif anomaly_type == "low_pressure":
            oil_p = round(np.random.uniform(15.0, 25.0), 1)
        elif anomaly_type == "long_run":
            run_h = int(np.random.uniform(400, 800))
        elif anomaly_type == "multi":
            vib = round(np.random.uniform(2.0, 4.0), 2)
            temp_d = round(np.random.uniform(10.0, 20.0), 1)
            oil_p = round(np.random.uniform(20.0, 30.0), 1)
        
        rows.append({
            "log_id": f"LOG-{num_normal + i + 1:04d}",
            "equipment_id": eq_id,
            "vibration_rms": max(0.1, vib),
            "temp_delta": max(0.0, temp_d),
            "oil_pressure": max(5.0, oil_p),
            "run_hours_since_service": max(10, run_h),
            "is_anomalous_label": 1,
        })
    
    # Shuffle so anomalies aren't all at the end
    np.random.shuffle(rows)
    
    df = pd.DataFrame(rows)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_csv(output_path, index=False)
    
    anomaly_count = df["is_anomalous_label"].sum()
    print(f"Generated maintenance_logs.csv: {len(df)} rows ({anomaly_count} anomalies, {len(df) - anomaly_count} normal)")
    return df


if __name__ == "__main__":
    generate_sensor_logs()
    generate_maintenance_logs()
