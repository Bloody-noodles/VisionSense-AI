import cv2
from ultralytics import YOLO

# Our trained person detector
model = YOLO("model/person/best.pt")

# OpenCV's built-in face detector
face_cascade = cv2.CascadeClassifier(
    cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
)

cap = cv2.VideoCapture(0)

cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 360)
cap.set(cv2.CAP_PROP_FPS, 15)

if not cap.isOpened():
    print("ERROR: Could not open webcam.")
    exit()

print("VisionSense-AI Face Detection Started.")
print("Press Q to quit.")

while True:

    ret, frame = cap.read()

    if not ret:
        break

    # Person detection + tracking
    results = model.track(
        frame,
        imgsz=320,
        conf=0.60,
        persist=True,
        tracker="bytetrack.yaml",
        verbose=False
    )

    annotated = results[0].plot()

    # Detect faces
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    faces = face_cascade.detectMultiScale(
        gray,
        scaleFactor=1.1,
        minNeighbors=5,
        minSize=(40, 40)
    )

    # Draw face boxes
    for (x, y, w, h) in faces:

        cv2.rectangle(
            annotated,
            (x, y),
            (x + w, y + h),
            (255, 0, 0),
            2
        )

        cv2.putText(
            annotated,
            "Face",
            (x, y - 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (255, 0, 0),
            2
        )

    cv2.imshow(
        "VisionSense-AI - Person + Face Detection",
        annotated
    )

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cap.release()
cv2.destroyAllWindows()