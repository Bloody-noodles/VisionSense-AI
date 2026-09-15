import cv2
import time

from ultralytics import YOLO

from event_engine import EventEngine
from movement_engine import MovementEngine
from session_analytics import SessionAnalytics
from activity_timeline import ActivityTimeline


# ================================================================
# CONFIGURATION
# ================================================================

MODEL_PATH = "model/person/best.pt"

CONFIDENCE = 0.60
IMG_SIZE = 320

CAMERA_WIDTH = 640
CAMERA_HEIGHT = 360
CAMERA_FPS = 15


# ================================================================
# INITIALIZE SYSTEMS
# ================================================================

event_engine = EventEngine()

movement_engine = MovementEngine()

session_analytics = SessionAnalytics()

activity_timeline = ActivityTimeline()


# ================================================================
# LOAD MODEL
# ================================================================

model = YOLO(
    MODEL_PATH
)


# ================================================================
# CAMERA
# ================================================================

cap = cv2.VideoCapture(0)

cap.set(
    cv2.CAP_PROP_FRAME_WIDTH,
    CAMERA_WIDTH
)

cap.set(
    cv2.CAP_PROP_FRAME_HEIGHT,
    CAMERA_HEIGHT
)

cap.set(
    cv2.CAP_PROP_FPS,
    CAMERA_FPS
)


if not cap.isOpened():

    print(
        "ERROR: Camera could not be opened."
    )

    exit()


# ================================================================
# STARTUP
# ================================================================

print(
    "=================================================="
)

print(
    " VisionSense-AI | Session Analytics"
)

print(
    "=================================================="
)

print(
    "Camera: ONLINE"
)

print(
    "Model: YOLO11n"
)

print(
    "Tracker: ByteTrack"
)

print(
    "Analytics: ONLINE"
)

print()

print(
    "Press Q to quit."
)

print(
    "=================================================="
)


# ================================================================
# SESSION STATE
# ================================================================

person_history = {}

start_time = time.time()

# Last EventEngine sequence processed
last_event_sequence = -1


# ================================================================
# MAIN LOOP
# ================================================================

while True:

    ret, frame = cap.read()

    if not ret:
        break


    # ============================================================
    # YOLO + BYTETRACK
    # ============================================================

    results = model.track(

        frame,

        imgsz=IMG_SIZE,

        conf=CONFIDENCE,

        persist=True,

        tracker="bytetrack.yaml",

        verbose=False
    )


    # ============================================================
    # OUTPUT FRAME
    # ============================================================

    output = frame.copy()


    # ============================================================
    # CURRENT PEOPLE
    # ============================================================

    current_people = 0

    current_ids = []


    # ============================================================
    # PROCESS DETECTIONS
    # ============================================================

    if results[0].boxes is not None:

        for box in results[0].boxes:


            # ----------------------------------------------------
            # Bounding box
            # ----------------------------------------------------

            coords = (
                box.xyxy[0]
                .cpu()
                .numpy()
                .astype(int)
            )

            x1, y1, x2, y2 = coords


            # Keep coordinates inside frame

            x1 = max(
                0,
                x1
            )

            y1 = max(
                0,
                y1
            )

            x2 = min(
                frame.shape[1],
                x2
            )

            y2 = min(
                frame.shape[0],
                y2
            )


            # ----------------------------------------------------
            # TRACK ID
            # ----------------------------------------------------

            if box.id is None:
                continue


            person_id = int(
                box.id[0]
            )


            # ----------------------------------------------------
            # PERSON CENTER
            # ----------------------------------------------------

            center_x = int(
                (x1 + x2) / 2
            )

            center_y = int(
                (y1 + y2) / 2
            )


            # ----------------------------------------------------
            # MOVEMENT ENGINE
            # ----------------------------------------------------

            movement = movement_engine.update(

                person_id,

                (
                    center_x,
                    center_y
                )
            )


            # ----------------------------------------------------
            # EVENT ENGINE
            # ----------------------------------------------------

            event_engine.update_movement(

                person_id,

                movement["state"],

                movement["direction"],

                movement["speed"]
            )


            # ----------------------------------------------------
            # SESSION ANALYTICS
            # ----------------------------------------------------

            session_analytics.record_movement(

                movement["state"],

                movement["direction"]
            )


            # ----------------------------------------------------
            # PEOPLE COUNT
            # ----------------------------------------------------

            current_people += 1

            current_ids.append(
                person_id
            )


            # ----------------------------------------------------
            # PERSON HISTORY
            # ----------------------------------------------------

            now = time.time()


            if person_id not in person_history:

                person_history[person_id] = {

                    "first_seen": now,

                    "last_seen": now
                }

            else:

                person_history[
                    person_id
                ][
                    "last_seen"
                ] = now


            # ----------------------------------------------------
            # TRACKING DURATION
            # ----------------------------------------------------

            duration = (
                now
                -
                person_history[
                    person_id
                ][
                    "first_seen"
                ]
            )


            # ====================================================
            # DRAW PERSON BOX
            # ====================================================

            cv2.rectangle(

                output,

                (
                    x1,
                    y1
                ),

                (
                    x2,
                    y2
                ),

                (
                    0,
                    255,
                    0
                ),

                2
            )


            # ====================================================
            # PERSON LABEL
            # ====================================================

            label = (

                f"ID {person_id} | "
                f"{movement['state']} | "
                f"{movement['direction']}"
            )


            cv2.putText(

                output,

                label,

                (
                    x1,
                    max(
                        y1 - 10,
                        20
                    )
                ),

                cv2.FONT_HERSHEY_SIMPLEX,

                0.45,

                (
                    0,
                    255,
                    0
                ),

                1,

                cv2.LINE_AA
            )


            # ====================================================
            # TRACKING TIME
            # ====================================================

            duration_label = (

                f"{duration:.1f}s"
            )


            cv2.putText(

                output,

                duration_label,

                (
                    x1,
                    min(
                        y2 + 18,
                        frame.shape[0] - 10
                    )
                ),

                cv2.FONT_HERSHEY_SIMPLEX,

                0.45,

                (
                    255,
                    255,
                    255
                ),

                1,

                cv2.LINE_AA
            )


    # ============================================================
    # REMOVE OLD MOVEMENT TRACKS
    # ============================================================

    movement_engine.remove_old_tracks()


    # ============================================================
    # UPDATE PEOPLE / ENTRY / EXIT EVENTS
    # ============================================================

    entered, exited = (
        event_engine.update_people(
            current_ids
        )
    )


    # ============================================================
    # SESSION PEOPLE ANALYTICS
    # ============================================================

    session_analytics.update_people(
        current_ids
    )


    # ============================================================
    # RECORD ENTRIES
    # ============================================================

    for person_id in entered:

        session_analytics.record_entry(
            person_id
        )


    # ============================================================
    # RECORD EXITS
    # ============================================================

    for person_id in exited:

        session_analytics.record_exit(
            person_id
        )


    # ============================================================
    # GET ONLY NEW EVENTS
    # ============================================================

    new_events = (
        event_engine.get_events_since(
            last_event_sequence
        )
    )


    # ============================================================
    # SEND NEW EVENTS TO TIMELINE
    # ============================================================

    if new_events:

        activity_timeline.add_events(
            new_events
        )

        last_event_sequence = (
            new_events[-1]["sequence"]
        )


    # ============================================================
    # SESSION STATS
    # ============================================================

    stats = (
        session_analytics.get_stats()
    )


    # ============================================================
    # ANALYTICS PANEL
    # ============================================================

    panel_x = 10

    panel_y = 10

    line_height = 20


    # ------------------------------------------------------------
    # Background panel
    # ------------------------------------------------------------

    cv2.rectangle(

        output,

        (
            panel_x,
            panel_y
        ),

        (
            245,
            175
        ),

        (
            20,
            20,
            20
        ),

        -1
    )


    # ------------------------------------------------------------
    # Title
    # ------------------------------------------------------------

    cv2.putText(

        output,

        "VISION SENSE",

        (
            20,
            32
        ),

        cv2.FONT_HERSHEY_SIMPLEX,

        0.55,

        (
            255,
            255,
            255
        ),

        1,

        cv2.LINE_AA
    )


    # ------------------------------------------------------------
    # Current people
    # ------------------------------------------------------------

    cv2.putText(

        output,

        f"People: {stats['current_people']}",

        (
            20,
            55
        ),

        cv2.FONT_HERSHEY_SIMPLEX,

        0.45,

        (
            255,
            255,
            255
        ),

        1,

        cv2.LINE_AA
    )


    # ------------------------------------------------------------
    # Peak occupancy
    # ------------------------------------------------------------

    cv2.putText(

        output,

        f"Peak: {stats['peak_occupancy']}",

        (
            20,
            75
        ),

        cv2.FONT_HERSHEY_SIMPLEX,

        0.45,

        (
            255,
            255,
            255
        ),

        1,

        cv2.LINE_AA
    )


    # ------------------------------------------------------------
    # Unique tracks
    # ------------------------------------------------------------

    cv2.putText(

        output,

        f"Tracked: {stats['unique_people']}",

        (
            20,
            95
        ),

        cv2.FONT_HERSHEY_SIMPLEX,

        0.45,

        (
            255,
            255,
            255
        ),

        1,

        cv2.LINE_AA
    )


    # ------------------------------------------------------------
    # Movement
    # ------------------------------------------------------------

    cv2.putText(

        output,

        f"Moving: {stats['moving_percent']}%",

        (
            20,
            115
        ),

        cv2.FONT_HERSHEY_SIMPLEX,

        0.45,

        (
            255,
            255,
            255
        ),

        1,

        cv2.LINE_AA
    )


    # ------------------------------------------------------------
    # Fast movements
    # ------------------------------------------------------------

    cv2.putText(

        output,

        f"Fast events: {stats['fast_movements']}",

        (
            20,
            135
        ),

        cv2.FONT_HERSHEY_SIMPLEX,

        0.45,

        (
            255,
            255,
            255
        ),

        1,

        cv2.LINE_AA
    )


    # ------------------------------------------------------------
    # Direction
    # ------------------------------------------------------------

    cv2.putText(

        output,

        f"Flow: {stats['most_common_direction']}",

        (
            20,
            155
        ),

        cv2.FONT_HERSHEY_SIMPLEX,

        0.45,

        (
            255,
            255,
            255
        ),

        1,

        cv2.LINE_AA
    )


    # ============================================================
    # ACTIVITY TIMELINE COUNT
    # ============================================================

    timeline_count = (
        activity_timeline.count()
    )


    cv2.putText(

        output,

        f"Events: {timeline_count}",

        (
            20,
            172
        ),

        cv2.FONT_HERSHEY_SIMPLEX,

        0.40,

        (
            200,
            200,
            200
        ),

        1,

        cv2.LINE_AA
    )


    # ============================================================
    # DISPLAY
    # ============================================================

    cv2.imshow(
        "VisionSense-AI",
        output
    )


    # ============================================================
    # QUIT
    # ============================================================

    key = cv2.waitKey(1) & 0xFF


    if key == ord("q"):

        break


# ================================================================
# CLEANUP
# ================================================================

cap.release()

cv2.destroyAllWindows()


# ================================================================
# FINAL SESSION REPORT
# ================================================================

final_stats = (
    session_analytics.get_stats()
)


print()

print(
    "=================================================="
)

print(
    " VisionSense-AI | Final Session Report"
)

print(
    "=================================================="
)

print(
    f"Session duration: "
    f"{final_stats['duration']} seconds"
)

print(
    f"Unique tracks: "
    f"{final_stats['unique_people']}"
)

print(
    f"Peak occupancy: "
    f"{final_stats['peak_occupancy']}"
)

print(
    f"Entries: "
    f"{final_stats['entries']}"
)

print(
    f"Exits: "
    f"{final_stats['exits']}"
)

print(
    f"Moving: "
    f"{final_stats['moving_percent']}%"
)

print(
    f"Stationary: "
    f"{final_stats['stationary_percent']}%"
)

print(
    f"Fast movements: "
    f"{final_stats['fast_movements']}"
)

print(
    f"Most common direction: "
    f"{final_stats['most_common_direction']}"
)

print(
    f"Timeline events: "
    f"{activity_timeline.count()}"
)

print(
    "=================================================="
)