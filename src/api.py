import asyncio
import threading
import time

import cv2
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from ultralytics import YOLO

from .event_engine import EventEngine
from .movement_engine import MovementEngine
from .session_analytics import SessionAnalytics
from .activity_timeline import ActivityTimeline


# ============================================================
# CONFIGURATION
# ============================================================

MODEL_PATH = "model/person/best.pt"

CONFIDENCE = 0.60
IMG_SIZE = 320

CAMERA_WIDTH = 640
CAMERA_HEIGHT = 360
CAMERA_FPS = 15


# ============================================================
# FASTAPI
# ============================================================

app = FastAPI(
    title="VisionSense API",
    description="Real-time computer vision intelligence backend",
    version="1.0.0"
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


# ============================================================
# VISION COMPONENTS
# ============================================================

event_engine = EventEngine()

movement_engine = MovementEngine()

session_analytics = SessionAnalytics()

activity_timeline = ActivityTimeline()


# ============================================================
# YOLO MODEL
# ============================================================

model = YOLO(MODEL_PATH)


# ============================================================
# CAMERA
# ============================================================

cap = None

camera_thread = None

main_loop = None


# ============================================================
# LIVE VIDEO FRAME
# ============================================================

latest_frame = None

frame_lock = threading.Lock()


# ============================================================
# SYSTEM STATE
# ============================================================

system_state = {
    "running": False,
    "camera": "OFFLINE",
    "model": "YOLO11n",
    "tracker": "ByteTrack",
    "analytics": "ONLINE",
    "current_people": 0,
    "last_update": None
}


# ============================================================
# WEBSOCKET CLIENTS
# ============================================================

connected_clients = set()

last_event_sequence = -1


# ============================================================
# EVENT BROADCAST
# ============================================================

async def broadcast_event(event):

    disconnected = set()

    for websocket in connected_clients:

        try:

            await websocket.send_json(event)

        except Exception:

            disconnected.add(websocket)


    for websocket in disconnected:

        connected_clients.discard(websocket)


# ============================================================
# CAMERA PROCESSING
# ============================================================

def process_camera():

    global cap
    global latest_frame
    global last_event_sequence


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

        system_state["camera"] = "OFFLINE"

        system_state["running"] = False

        print(
            "ERROR: Camera could not be opened."
        )

        return


    system_state["camera"] = "ONLINE"

    system_state["running"] = True


    print(
        "=================================================="
    )

    print(
        " VisionSense-AI | FastAPI Vision Engine"
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

    print(
        "Video Feed: ONLINE"
    )

    print(
        "API: ONLINE"
    )

    print(
        "=================================================="
    )


    while system_state["running"]:

        ret, frame = cap.read()


        if not ret:

            continue


        # ====================================================
        # YOLO TRACKING
        # ====================================================

        results = model.track(
            frame,
            imgsz=IMG_SIZE,
            conf=CONFIDENCE,
            persist=True,
            tracker="bytetrack.yaml",
            verbose=False
        )


        current_ids = []


        # ====================================================
        # DETECTIONS
        # ====================================================

        if results[0].boxes is not None:

            for box in results[0].boxes:

                if box.id is None:

                    continue


                coords = (
                    box.xyxy[0]
                    .cpu()
                    .numpy()
                    .astype(int)
                )


                x1, y1, x2, y2 = coords


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


                person_id = int(
                    box.id[0]
                )


                center_x = int(
                    (x1 + x2) / 2
                )

                center_y = int(
                    (y1 + y2) / 2
                )


                # ====================================================
                # MOVEMENT
                # ====================================================

                movement = movement_engine.update(
                    person_id,
                    (
                        center_x,
                        center_y
                    )
                )


                # ====================================================
                # EVENTS
                # ====================================================

                event_engine.update_movement(
                    person_id,
                    movement["state"],
                    movement["direction"],
                    movement["speed"]
                )


                # ====================================================
                # ANALYTICS
                # ====================================================

                session_analytics.record_movement(
                    movement["state"],
                    movement["direction"]
                )


                current_ids.append(
                    person_id
                )


                # ====================================================
                # DRAW DETECTION BOX
                # ====================================================

                cv2.rectangle(
                    frame,
                    (x1, y1),
                    (x2, y2),
                    (255, 255, 255),
                    2
                )


                # ====================================================
                # PERSON LABEL
                # ====================================================

                label = (
                    f"ID {person_id}  "
                    f"{movement['state']}"
                )


                label_y = max(
                    y1 - 10,
                    20
                )


                cv2.putText(
                    frame,
                    label,
                    (x1, label_y),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.5,
                    (255, 255, 255),
                    1,
                    cv2.LINE_AA
                )


        # ====================================================
        # CLEAN OLD TRACKS
        # ====================================================

        movement_engine.remove_old_tracks()


        # ====================================================
        # ENTRY / EXIT EVENTS
        # ====================================================

        entered, exited = event_engine.update_people(
            current_ids
        )


        # ====================================================
        # SESSION ANALYTICS
        # ====================================================

        session_analytics.update_people(
            current_ids
        )


        for person_id in entered:

            session_analytics.record_entry(
                person_id
            )


        for person_id in exited:

            session_analytics.record_exit(
                person_id
            )


        # ====================================================
        # NEW EVENTS
        # ====================================================

        new_events = event_engine.get_events_since(
            last_event_sequence
        )


        if new_events:

            activity_timeline.add_events(
                new_events
            )


            last_event_sequence = (
                new_events[-1]["sequence"]
            )


            if main_loop is not None:

                for event in new_events:

                    try:

                        asyncio.run_coroutine_threadsafe(
                            broadcast_event(event),
                            main_loop
                        )

                    except Exception:

                        pass


        # ====================================================
        # UPDATE SYSTEM STATE
        # ====================================================

        stats = session_analytics.get_stats()


        system_state["current_people"] = (
            stats["current_people"]
        )


        system_state["last_update"] = (
            time.time()
        )


        # ====================================================
        # CAMERA STATUS OVERLAY
        # ====================================================

        cv2.putText(
            frame,
            "VISIONSENSE",
            (15, 25),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.65,
            (255, 255, 255),
            2,
            cv2.LINE_AA
        )


        cv2.putText(
            frame,
            f"PEOPLE: {stats['current_people']}",
            (15, 50),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (255, 255, 255),
            1,
            cv2.LINE_AA
        )


        # ====================================================
        # ENCODE FRAME FOR WEB STREAM
        # ====================================================

        success, encoded = cv2.imencode(
            ".jpg",
            frame,
            [
                cv2.IMWRITE_JPEG_QUALITY,
                80
            ]
        )


        if success:

            with frame_lock:

                latest_frame = encoded.tobytes()


    # ============================================================
    # SHUTDOWN CAMERA
    # ============================================================

    if cap is not None:

        cap.release()


    with frame_lock:

        latest_frame = None


    system_state["camera"] = "OFFLINE"

    system_state["running"] = False


# ============================================================
# VIDEO STREAM GENERATOR
# ============================================================

def generate_video():

    while True:

        with frame_lock:

            frame = latest_frame


        if frame is None:

            time.sleep(0.05)

            continue


        yield (
            b"--frame\r\n"
            b"Content-Type: image/jpeg\r\n\r\n"
            + frame
            + b"\r\n"
        )


        time.sleep(
            1 / CAMERA_FPS
        )


# ============================================================
# STARTUP
# ============================================================

@app.on_event("startup")
async def startup_event():

    global camera_thread
    global main_loop


    main_loop = asyncio.get_running_loop()


    camera_thread = threading.Thread(
        target=process_camera,
        daemon=True
    )


    camera_thread.start()


# ============================================================
# SHUTDOWN
# ============================================================

@app.on_event("shutdown")
def shutdown_event():

    system_state["running"] = False


# ============================================================
# HEALTH
# ============================================================

@app.get("/health")
def health():

    return {
        "status": "online",
        "camera": system_state["camera"],
        "model": system_state["model"],
        "tracker": system_state["tracker"],
        "analytics": system_state["analytics"]
    }


# ============================================================
# VIDEO FEED
# ============================================================

@app.get("/video_feed")
def video_feed():

    return StreamingResponse(
        generate_video(),
        media_type=(
            "multipart/x-mixed-replace; "
            "boundary=frame"
        )
    )


# ============================================================
# ANALYTICS
# ============================================================

@app.get("/analytics")
def analytics():

    return session_analytics.get_stats()


# ============================================================
# STATUS
# ============================================================

@app.get("/status")
def status():

    return system_state


# ============================================================
# EVENTS
# ============================================================

@app.get("/events")
def events(
    limit: int = 20
):

    recent_events = (
        event_engine.get_recent_events(
            limit
        )
    )


    return {
        "count": len(recent_events),
        "events": recent_events
    }


# ============================================================
# TIMELINE
# ============================================================

@app.get("/timeline")
def timeline(
    limit: int = 20
):

    recent_events = (
        activity_timeline.get_recent(
            limit
        )
    )


    return {
        "count": len(recent_events),
        "events": recent_events
    }


# ============================================================
# LATEST EVENT
# ============================================================

@app.get("/events/latest")
def latest_event():

    return activity_timeline.get_latest()


# ============================================================
# WEBSOCKET
# ============================================================

@app.websocket("/ws/events")
async def websocket_events(
    websocket: WebSocket
):

    await websocket.accept()


    connected_clients.add(
        websocket
    )


    try:

        recent_events = (
            event_engine.get_recent_events(
                10
            )
        )


        for event in recent_events:

            await websocket.send_json(
                event
            )


        while True:

            await websocket.receive_text()


    except WebSocketDisconnect:

        connected_clients.discard(
            websocket
        )


    except Exception:

        connected_clients.discard(
            websocket
        )