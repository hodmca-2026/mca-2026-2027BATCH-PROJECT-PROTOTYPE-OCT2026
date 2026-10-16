import argparse
import cv2
from ultralytics import YOLO


def detect_image(model, path):
    img = cv2.imread(path)
    if img is None:
        print("Image nahi mili:", path)
        return
    results = model(img)[0]
    annotated = results.plot()
    print("\nDetected objects:")
    for box in results.boxes:
        print(f" - {model.names[int(box.cls)]}: {float(box.conf):.2f}")
    cv2.imwrite("output.jpg", annotated)
    print("\nResult 'output.jpg' me save ho gaya.")
    cv2.imshow("Result", annotated)
    cv2.waitKey(0)
    cv2.destroyAllWindows()


def detect_video(model, source):
    cap = cv2.VideoCapture(source)
    while cap.isOpened():
        ok, frame = cap.read()
        if not ok:
            break
        cv2.imshow("Result (press q to quit)", model(frame, verbose=False)[0].plot())
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break
    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--image")
    p.add_argument("--video")
    p.add_argument("--webcam", action="store_true")
    p.add_argument("--segment", action="store_true", help="image segmentation mode")
    a = p.parse_args()

    model = YOLO("yolov8n-seg.pt" if a.segment else "yolov8n.pt")

    if a.image:
        detect_image(model, a.image)
    elif a.video:
        detect_video(model, a.video)
    elif a.webcam:
        detect_video(model, 0)
    else:
        print("Use: python detect.py --image photo.jpg [--segment]")