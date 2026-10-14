"""
PPE Detection using YOLOv8

Uses pretrained YOLOv8n for object detection. If a PPE-specific
fine-tuned weights file is present at models_store/ppe_yolo.pt,
it will be preferred.

Course mapping: DL Unit VI — Object detection, image segmentation,
project pipeline for computer vision applications.
"""

import os
import logging
from typing import List, Dict

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

MODELS_DIR = os.path.join(os.path.dirname(__file__), "..", "models_store")
PPE_WEIGHTS_PATH = os.path.join(MODELS_DIR, "ppe_yolo.pt")

# PPE-related class names from COCO that are relevant
PPE_RELEVANT_CLASSES = {
    "person", "helmet", "hard hat", "vest", "safety vest",
    "gloves", "glasses", "goggles", "mask", "boot",
    # COCO default class names that might be relevant
    "tie", "handbag", "backpack",
}


def detect_ppe(image_path: str) -> List[Dict]:
    """
    Detect objects in an image using YOLOv8.
    
    Uses pretrained YOLOv8n (general COCO detector) unless a PPE-specific
    fine-tuned model exists at models_store/ppe_yolo.pt.
    
    Args:
        image_path: Path to the image file.
    
    Returns:
        List of dicts: [{class_name, confidence, bbox: [x1, y1, x2, y2]}, ...]
    """
    try:
        from ultralytics import YOLO
    except ImportError:
        logger.warning("ultralytics not installed. PPE detection unavailable.")
        return []
    
    # Choose model weights
    if os.path.exists(PPE_WEIGHTS_PATH):
        model_path = PPE_WEIGHTS_PATH
        logger.info(f"Using PPE-specific model: {model_path}")
    else:
        model_path = "yolov8n.pt"
        logger.info(f"Using pretrained YOLOv8n: {model_path}")
    
    try:
        model = YOLO(model_path)
        results = model(image_path, verbose=False)
        
        detections = []
        for result in results:
            boxes = result.boxes
            if boxes is not None:
                for i in range(len(boxes)):
                    class_id = int(boxes.cls[i])
                    class_name = result.names[class_id]
                    confidence = float(boxes.conf[i])
                    bbox = boxes.xyxy[i].tolist()
                    
                    detections.append({
                        "class_name": class_name,
                        "confidence": round(confidence, 4),
                        "bbox": [round(b, 2) for b in bbox],
                    })
        
        logger.info(f"Detected {len(detections)} objects in {image_path}")
        return detections
    
    except Exception as e:
        logger.error(f"PPE detection failed: {e}")
        return []


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        image_path = sys.argv[1]
        results = detect_ppe(image_path)
        print(f"\nDetections for {image_path}:")
        for d in results:
            print(f"  {d['class_name']}: {d['confidence']:.2%} at {d['bbox']}")
    else:
        print("Usage: python -m cv_branch.ppe_detect <image_path>")
