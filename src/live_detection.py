import cv2
from ultralytics import YOLO
import time

model = YOLO("model/person/best.pt")

cap = cv2.VideoCapture(0)

# Reduce webcam workload
cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 360)
cap.set(cv2.CAP_PROP_FPS, 15)

if not cap.isOpened():
    print("ERROR: Could not open webcam.")
    exit()

print("VisionSense-AI started.")
print("Press Q to quit.")

frame_count = 0
last_results = None
prev_time = time.time()
fps = 0

while True:
    ret, frame = cap.read()

    if not ret:
        break

    frame_count += 1

    # Run YOLO only every 3rd frame
    if frame_count % 3 == 0:
        results = model(
            frame,
            imgsz=320,
            conf=0.70,
            verbose=False
        )
        last_results = results[0].plot()

    # Reuse previous detection frames
    if last_results is not None:
        display = last_results
    else:
        display = frame

    # FPS
    current_time = time.time()
    fps = 1 / max(current_time - prev_time, 0.001)
    prev_time = current_time

    cv2.putText(
        display,
        f"FPS: {fps:.1f}",
        (10, 30),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.7,
        (0, 255, 0),
        2
    )

    cv2.imshow("VisionSense-AI", display)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()