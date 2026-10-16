"""Object detection module (Deep Learning part).

Uses the same YOLOv8 model and the same calls as detect.py:
    model = YOLO("yolov8n.pt");  results = model(img)[0];  results.plot()
The only additions are returning the detections as data instead of printing
them, and a lock so two browser requests never use the model at once.
"""
import threading

import numpy as np

from ultralytics import YOLO

MODEL_PATH = "yolov8n.pt"


class Detector:
    def __init__(self, model_path=MODEL_PATH):
        self.model = YOLO(model_path)
        self.names = self.model.names          # {0: 'person', 1: 'bicycle', ...} 80 COCO classes
        self._lock = threading.Lock()
        self.model(np.zeros((320, 320, 3), np.uint8), verbose=False)   # warm-up so the first real request is fast

    def detect(self, bgr_image, conf=0.25):
        """Runs YOLOv8 on one image.
        Returns (detections, annotated_image). Each detection is
        {"label", "confidence", "box": [x1, y1, x2, y2]} in pixels."""
        with self._lock:
            result = self.model(bgr_image, conf=conf, verbose=False)[0]
            annotated = result.plot()            # same drawing as detect.py
        detections = []
        for box in result.boxes:
            x1, y1, x2, y2 = (float(v) for v in box.xyxy[0])
            detections.append({
                "label": self.names[int(box.cls)],
                "confidence": round(float(box.conf), 4),
                "box": [round(x1, 1), round(y1, 1), round(x2, 1), round(y2, 1)],
            })
        detections.sort(key=lambda d: -d["confidence"])
        return detections, annotated
