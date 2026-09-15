import cv2
import numpy as np
from ultralytics import YOLO

# =========================
# CONFIG
# =========================

MODEL_PATH = "model/person/best.pt"

CONFIDENCE = 0.60
IMG_SIZE = 320

# =========================
# MODELS
# =========================

model = YOLO(MODEL_PATH)

face_cascade = cv2.CascadeClassifier(
    cv2.data.haarcascades +
    "haarcascade_frontalface_default.xml"
)

# =========================
# CAMERA
# =========================

cap = cv2.VideoCapture(0)

cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 360)
cap.set(cv2.CAP_PROP_FPS, 15)

if not cap.isOpened():
    print("ERROR: Camera could not be opened.")
    exit()

print("=" * 45)
print(" VisionSense-AI")
print(" Real-Time Human Detection System")
print("=" * 45)
print("Press Q to quit.")


# =========================
# ATTRIBUTE FUNCTIONS
# =========================

def clothing_color(person):

    if person.size == 0:
        return "Unknown"

    h = person.shape[0]

    # Focus mostly on torso/lower body
    clothing = person[int(h * 0.35):]

    if clothing.size == 0:
        return "Unknown"

    # Resize for speed
    clothing = cv2.resize(clothing, (40, 40))

    hsv = cv2.cvtColor(clothing, cv2.COLOR_BGR2HSV)

    pixels = hsv.reshape(-1, 3)

    valid = pixels[pixels[:, 2] > 40]

    if len(valid) == 0:
        return "Unknown"

    avg_h = np.mean(valid[:, 0])
    avg_s = np.mean(valid[:, 1])
    avg_v = np.mean(valid[:, 2])

    # Low saturation = black/white/gray
    if avg_s < 35:

        if avg_v < 70:
            return "Black"

        if avg_v > 190:
            return "White"

        return "Gray"

    # HSV hue ranges
    if avg_h < 10 or avg_h >= 170:
        return "Red"

    if avg_h < 25:
        return "Orange"

    if avg_h < 35:
        return "Yellow"

    if avg_h < 85:
        return "Green"

    if avg_h < 130:
        return "Blue"

    if avg_h < 170:
        return "Purple"

    return "Mixed"


def detect_face(person):

    if person.size == 0:
        return None

    h, w = person.shape[:2]

    # Only search upper portion of person
    upper = person[:int(h * 0.45)]

    gray = cv2.cvtColor(upper, cv2.COLOR_BGR2GRAY)

    faces = face_cascade.detectMultiScale(
        gray,
        scaleFactor=1.1,
        minNeighbors=6,
        minSize=(35, 35)
    )

    if len(faces) == 0:
        return None

    # Choose largest detected face
    face = max(
        faces,
        key=lambda box: box[2] * box[3]
    )

    return face


def skin_tone(face):

    if face is None:
        return "Unknown"

    x, y, w, h = face

    crop = face_region[y:y+h, x:x+w]

    if crop.size == 0:
        return "Unknown"

    hsv = cv2.cvtColor(crop, cv2.COLOR_BGR2HSV)

    H = hsv[:, :, 0]
    S = hsv[:, :, 1]
    V = hsv[:, :, 2]

    mask = (
        (H >= 0) &
        (H <= 25) &
        (S >= 25) &
        (S <= 210) &
        (V >= 35)
    )

    if np.sum(mask) < 30:
        return "Unknown"

    brightness = np.mean(V[mask])

    if brightness < 80:
        return "Dark"

    elif brightness < 140:
        return "Medium"

    elif brightness < 190:
        return "Light"

    return "Very Light"


# =========================
# MAIN LOOP
# =========================

while True:

    ret, frame = cap.read()

    if not ret:
        break

    results = model.track(
        frame,
        imgsz=IMG_SIZE,
        conf=CONFIDENCE,
        persist=True,
        tracker="bytetrack.yaml",
        verbose=False
    )

    output = frame.copy()

    if results[0].boxes is not None:

        for box in results[0].boxes:

            coords = box.xyxy[0].cpu().numpy().astype(int)

            x1, y1, x2, y2 = coords

            x1 = max(0, x1)
            y1 = max(0, y1)
            x2 = min(frame.shape[1], x2)
            y2 = min(frame.shape[0], y2)

            person_crop = frame[y1:y2, x1:x2]

            if person_crop.size == 0:
                continue

            # Tracking ID
            if box.id is not None:
                person_id = int(box.id[0])
            else:
                person_id = 0

            # Attributes
            clothes = clothing_color(person_crop)

            # Face detection
            face_box = detect_face(person_crop)

            # Draw person box
            cv2.rectangle(
                output,
                (x1, y1),
                (x2, y2),
                (255, 0, 0),
                2
            )

            # Face box
            if face_box is not None:

                fx, fy, fw, fh = face_box

                cv2.rectangle(
                    output,
                    (x1 + fx, y1 + fy),
                    (x1 + fx + fw, y1 + fy + fh),
                    (0, 255, 0),
                    2
                )

            # Clean information panel
            label_y = y1 - 10

            if label_y < 55:
                label_y = y1 + 20

            cv2.putText(
                output,
                f"PERSON {person_id}",
                (x1, label_y),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.55,
                (255, 255, 255),
                2
            )

            cv2.putText(
                output,
                f"Clothing: {clothes}",
                (x1, label_y + 20),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.45,
                (255, 255, 255),
                1
            )

            cv2.putText(
                output,
                "Face: detected" if face_box is not None
                else "Face: searching",
                (x1, label_y + 40),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.45,
                (255, 255, 255),
                1
            )

    # =========================
    # UI
    # =========================

    cv2.putText(
        output,
        "VisionSense-AI",
        (10, 25),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.65,
        (255, 255, 255),
        2
    )

    cv2.imshow(
        "VisionSense-AI",
        output
    )

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break


cap.release()
cv2.destroyAllWindows()