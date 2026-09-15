import cv2
import numpy as np
from ultralytics import YOLO

# Our trained person detector
model = YOLO("model/person/best.pt")

cap = cv2.VideoCapture(0)

cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 360)
cap.set(cv2.CAP_PROP_FPS, 15)

if not cap.isOpened():
    print("ERROR: Could not open webcam.")
    exit()

print("VisionSense-AI Attribute Analysis Started.")
print("Press Q to quit.")


def get_dominant_color(image):
    """Estimate the dominant clothing color."""

    if image.size == 0:
        return "Unknown"

    # Resize for speed
    small = cv2.resize(image, (50, 50))

    # Ignore very dark pixels and very bright pixels
    pixels = small.reshape(-1, 3)

    # Convert BGR → HSV
    hsv = cv2.cvtColor(small, cv2.COLOR_BGR2HSV)
    hsv_pixels = hsv.reshape(-1, 3)

    valid = (
        (hsv_pixels[:, 2] > 40) &
        (hsv_pixels[:, 2] < 245)
    )

    if not np.any(valid):
        return "Unknown"

    avg_bgr = np.mean(pixels[valid], axis=0)

    b, g, r = avg_bgr

    # Simple color classification
    if max(r, g, b) - min(r, g, b) < 25:
        if r < 80:
            return "Black/Dark"
        elif r > 190:
            return "White/Light"
        else:
            return "Gray"

    if r > g * 1.25 and r > b * 1.25:
        return "Red"

    if g > r * 1.2 and g > b * 1.2:
        return "Green"

    if b > r * 1.2 and b > g * 1.1:
        return "Blue"

    if r > 140 and g > 90 and b < 100:
        return "Brown/Orange"

    if r > 130 and g > 100 and b > 80:
        return "Yellow/Beige"

    return "Mixed"


def estimate_skin_tone(face):
    """Very rough skin-tone estimate from face pixels."""

    if face.size == 0:
        return "Unknown"

    hsv = cv2.cvtColor(face, cv2.COLOR_BGR2HSV)

    h = hsv[:, :, 0]
    s = hsv[:, :, 1]
    v = hsv[:, :, 2]

    # Approximate skin-color mask.
    mask = (
        (h >= 0) &
        (h <= 25) &
        (s >= 30) &
        (s <= 200) &
        (v >= 40)
    )

    if np.sum(mask) < 50:
        return "Unknown"

    brightness = np.mean(v[mask])

    if brightness < 80:
        return "Dark"
    elif brightness < 140:
        return "Medium"
    elif brightness < 190:
        return "Light"
    else:
        return "Very Light"


while True:

    ret, frame = cap.read()

    if not ret:
        break

    results = model.track(
        frame,
        imgsz=320,
        conf=0.60,
        persist=True,
        tracker="bytetrack.yaml",
        verbose=False
    )

    annotated = results[0].plot()

    # Analyze detected people
    if results[0].boxes is not None:

        for box in results[0].boxes:

            coords = box.xyxy[0].cpu().numpy().astype(int)

            x1, y1, x2, y2 = coords

            # Keep coordinates inside frame
            x1 = max(0, x1)
            y1 = max(0, y1)
            x2 = min(frame.shape[1], x2)
            y2 = min(frame.shape[0], y2)

            person_crop = frame[y1:y2, x1:x2]

            if person_crop.size == 0:
                continue

            # Clothing region: lower ~60% of person
            person_h = person_crop.shape[0]

            clothing = person_crop[
                int(person_h * 0.35):
            ]

            clothing_color = get_dominant_color(clothing)

            # Face region: upper ~35% of person
            face_h = int(person_h * 0.35)

            face = person_crop[:face_h]

            skin_tone = estimate_skin_tone(face)

            # Tracking ID
            if box.id is not None:
                track_id = int(box.id[0])
            else:
                track_id = 0

            label = (
                f"ID {track_id} | "
                f"Clothing: {clothing_color} | "
                f"Skin: {skin_tone}"
            )

            cv2.putText(
                annotated,
                label,
                (x1, max(y1 - 10, 20)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.45,
                (0, 255, 0),
                1
            )

    cv2.imshow(
        "VisionSense-AI - Attribute Analysis",
        annotated
    )

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break


cap.release()
cv2.destroyAllWindows()