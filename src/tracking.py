import cv2
from ultralytics import YOLO
import time

model = YOLO("model/person/best.pt")

cap = cv2.VideoCapture(0)

cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 360)
cap.set(cv2.CAP_PROP_FPS, 15)

if not cap.isOpened():
    print("ERROR: Could not open webcam.")
    exit()

print("VisionSense-AI Tracking Started.")
print("Press Q to quit.")

while True:
    ret, frame = cap.read()

    if not ret:
        break

    # YOLO detection + ByteTrack tracking
    results = model.track(
        frame,
        imgsz=320,
        conf=0.60,
        persist=True,
        tracker="bytetrack.yaml",
        verbose=False
    )

    annotated = results[0].plot()

    cv2.imshow(
        "VisionSense-AI - Person Tracking",
        annotated
    )

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()