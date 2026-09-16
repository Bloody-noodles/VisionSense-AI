# VisionSense-AI

> Real-time human detection, tracking, movement analysis, and session intelligence powered by YOLO11n, ByteTrack, FastAPI, and Next.js.

VisionSense-AI is a computer-vision portfolio project designed to turn a live or recorded video stream into useful, human-readable scene intelligence.

## Demo

- **Web dashboard:** https://vision-sense-ai-wine.vercel.app/
- **FastAPI backend:** https://visionsense-ai-ozln.onrender.com/

The hosted deployment uses a demo video rather than a user's webcam, allowing the project to be demonstrated without access to a local camera.

## What It Does

VisionSense-AI combines object detection, multi-object tracking, movement analysis, event detection, and session analytics into a single dashboard.

### Core capabilities

- Human/person detection with a custom-trained YOLO11n model
- Persistent person tracking with ByteTrack
- Real-time movement state detection
  - Stationary
  - Moving
  - Fast movement
- Direction estimation
  - Up
  - Down
  - Left
  - Right
- Entry and exit event detection
- Occupancy monitoring
- Peak occupancy tracking
- Unique tracker-ID counting
- Movement statistics
- Dominant movement direction
- Activity/event timeline
- CSV event logging
- REST API for analytics and system status
- WebSocket event stream
- Browser-based monitoring dashboard

## Architecture

```text
                    Video Source
                         |
                         v
                 YOLO11n Detection
                         |
                         v
                   ByteTrack
                         |
          +--------------+--------------+
          |              |              |
          v              v              v
      Movement       Event Engine   Analytics
       Engine                           |
          |              |              |
          +--------------+--------------+
                         |
                         v
                     FastAPI
                         |
              +----------+----------+
              |                     |
              v                     v
        Next.js Dashboard      WebSocket
              |
              v
             User
```

## Technology Stack

### Computer Vision

- Python
- OpenCV
- Ultralytics YOLO11n
- ByteTrack

### Backend

- FastAPI
- Uvicorn
- WebSockets
- CSV-based event logging

### Frontend

- Next.js
- React
- TypeScript
- Tailwind CSS

### Deployment

- Vercel — frontend
- Render — FastAPI backend
- GitHub — source control

## Model Training

The person detector was trained using a custom dataset prepared and annotated through Roboflow.

Training setup:

- Model: YOLO11n
- Image size: 640×640
- Training epochs: 50
- Batch size: 16
- Hardware: NVIDIA Tesla T4

The resulting trained model is stored as:

```text
model/person/best.pt
```

The trained detector achieved approximately:

- **Test mAP50:** 57.8%
- **Test mAP50-95:** 34.5%

These metrics describe the held-out test evaluation for this project and should not be interpreted as general performance across every real-world environment.

## Local Setup

### 1. Clone the repository

```bash
git clone https://github.com/Bloody-noodles/VisionSense-AI.git
cd VisionSense-AI
```

### 2. Create a virtual environment

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Run the FastAPI backend

```bash
uvicorn src.api:app --host 0.0.0.0 --port 8000
```

The API will be available at:

```text
http://127.0.0.1:8000
```

### 5. Run the Next.js dashboard

```bash
cd frontend
npm install
npm run dev
```

Open:

```text
http://localhost:3000
```

## Backend Modes

VisionSense-AI supports a local camera mode and a hosted/demo video mode.

### Local webcam

Default mode:

```text
VISIONSENSE_MODE=local
```

### Demo video

For a hosted environment:

```text
VISIONSENSE_MODE=demo
```

The default demo source is:

```text
demo/demo.mp4
```

A different demo video can be supplied with:

```text
VISIONSENSE_DEMO_VIDEO=/path/to/video.mp4
```

## API Endpoints

| Endpoint | Purpose |
|---|---|
| `/health` | Service health information |
| `/status` | Current system status |
| `/analytics` | Session analytics |
| `/events` | Event history |
| `/events/latest` | Most recent event |
| `/timeline` | Activity timeline |
| `/video_feed` | MJPEG processed video stream |
| `/ws/events` | Real-time WebSocket events |

## Project Structure

```text
VisionSense-AI/
├── demo/
│   └── demo.mp4
├── frontend/
│   └── src/
│       └── app/
├── model/
│   └── person/
│       └── best.pt
├── src/
│   ├── api.py
│   ├── event_engine.py
│   ├── face_detection.py
│   ├── main.py
│   ├── movement_engine.py
│   ├── session_analytics.py
│   └── tracking.py
├── requirements.txt
└── README.md
```

## Design Decisions

VisionSense-AI was built with a lightweight architecture so that the core system can run on modest hardware.

The main person detector is custom-trained, while other computer-vision components use lightweight/pretrained approaches where appropriate. Movement and event intelligence are implemented as deterministic application logic rather than requiring another large model.

The local inference pipeline also uses reduced resolution and frame skipping to improve usability on CPU-only hardware.

## Limitations

- Tracker IDs represent tracked objects, not guaranteed real-world identities.
- Direction and movement states are estimates based on tracked bounding-box movement.
- The hosted demo processes a prerecorded video rather than a visitor's webcam.
- Model performance depends on camera angle, lighting, scene density, and the similarity of the scene to the training data.
- Computer-vision attribute estimates should not be treated as definitive personal characteristics.
- The free cloud deployment is intended primarily as a portfolio demonstration and may have resource/performance limitations.

## Portfolio Context

VisionSense-AI was built as a practical computer-vision portfolio project demonstrating an end-to-end workflow:

```text
Dataset Collection
      ↓
Data Cleaning
      ↓
Annotation
      ↓
YOLO11n Training
      ↓
Local Inference
      ↓
Object Tracking
      ↓
Movement & Event Intelligence
      ↓
FastAPI Backend
      ↓
Next.js Dashboard
      ↓
Cloud Deployment
```

The project demonstrates not only model training, but also the engineering work required to turn a computer-vision model into an interactive application.

## License

This project is provided for portfolio and educational purposes.
