# Eye Gaze Tracking System

A real-time AI-powered eye gaze tracking system for mobile devices, designed to enable hands-free navigation in educational applications.

## 🎯 Features

- **Real-time Eye Tracking**: Uses MediaPipe Face Mesh for robust face and eye detection
- **Gaze Estimation**: Maps eye gaze to screen coordinates with calibration support
- **Blink Detection**: Detects intentional blinks for click/select interactions
- **Interaction Handling**: Dwell-time selection, hover detection, and gaze-based scrolling
- **WebSocket Server**: Low-latency streaming for mobile app integration
- **Adaptive Smoothing**: Kalman filter and 1€ filter for stable gaze points
- **Calibration System**: 5 or 9-point calibration for personalized accuracy

## 📁 Project Structure

```
Eye Tracking Project/
├── main.py                 # Main entry point
├── requirements.txt        # Python dependencies
├── README.md
└── src/
    ├── __init__.py
    ├── config.py           # System configuration
    ├── pipeline.py         # Main gaze tracking pipeline
    ├── server.py           # FastAPI WebSocket server
    ├── calibration.py      # Calibration system
    ├── interactions.py     # Interaction handlers
    ├── models/
    │   ├── __init__.py
    │   ├── face_detector.py    # MediaPipe face detection
    │   ├── eye_tracker.py      # Eye tracking & iris detection
    │   ├── gaze_estimator.py   # Gaze to screen mapping
    │   └── blink_detector.py   # Blink detection
    └── utils/
        ├── __init__.py
        └── filters.py          # Kalman & 1€ filters
```

## 🚀 Getting Started

### Installation

1. **Clone or set up the project**

2. **Create a virtual environment** (recommended):

```bash
python -m venv venv
venv\Scripts\activate  # Windows
# or
source venv/bin/activate  # Linux/Mac
```

3. **Install dependencies**:

```bash
pip install -r requirements.txt
```

### Running the System

#### Option 1: Local Demo (Webcam)

Test the system with your webcam:

```bash
python main.py demo
```

**Controls:**

- `q` - Quit
- `c` - Start calibration
- `r` - Reset calibration
- `s` - Toggle smoothing

#### Option 2: WebSocket Server

Start the server for mobile app integration:

```bash
python main.py server --host 0.0.0.0 --port 8000
```

Or simply:

```bash
python main.py
```

Then open the demo page at: `http://localhost:8000/demo`

## 📡 API Reference

### WebSocket Endpoint

`ws://[host]:[port]/ws/gaze/{client_id}`

### Message Types

#### Send Frame

```json
{
  "type": "frame",
  "data": "<base64_image>",
  "timestamp": 1234567890
}
```

#### Receive Gaze Data

```json
{
  "x": 512,
  "y": 923,
  "confidence": 0.94,
  "blink": false,
  "processing_time_ms": 15.2
}
```

#### Configure Screen

```json
{
  "type": "configure",
  "screen_width": 1080,
  "screen_height": 1920
}
```

#### Start Calibration

```json
{
  "type": "calibrate_start",
  "num_points": 9
}
```

#### Add Calibration Sample

```json
{
  "type": "calibrate_sample",
  "frame_data": "<base64_image>",
  "screen_x": 100,
  "screen_y": 200
}
```

#### Register UI Element

```json
{
  "type": "register_element",
  "id": "button_1",
  "x": 100,
  "y": 200,
  "width": 150,
  "height": 50,
  "selectable": true,
  "scrollable": false
}
```

## ⚙️ Configuration

Edit `src/config.py` or use environment variables:

| Variable           | Default | Description             |
| ------------------ | ------- | ----------------------- |
| `GAZE_SERVER_HOST` | 0.0.0.0 | Server bind address     |
| `GAZE_SERVER_PORT` | 8000    | Server port             |
| `GAZE_ENABLE_GPU`  | false   | Enable GPU acceleration |
| `GAZE_TARGET_FPS`  | 30      | Target frame rate       |

## 📱 Mobile Integration

### React Native / Flutter

1. Capture camera frames
2. Encode frames as base64 JPEG
3. Send via WebSocket
4. Map returned coordinates to UI elements

Example (React Native):

```javascript
// Send frame
ws.send(
  JSON.stringify({
    type: "frame",
    data: base64Image,
    timestamp: Date.now(),
  }),
);

// Handle response
ws.onmessage = (event) => {
  const { x, y, confidence, blink } = JSON.parse(event.data);
  // Update UI based on gaze position
};
```

## 🔧 Performance

- **Target FPS**: 30+
- **Latency**: <50ms end-to-end
- **Processing Time**: ~15-25ms per frame (CPU)

### Optimization Tips

1. Reduce image resolution (640x480 recommended)
2. Use JPEG compression (quality 70-80%)
3. Enable GPU if available (ONNX Runtime GPU)
4. Adjust smoothing parameters for responsiveness vs stability

## 🧪 Testing

Run the local demo to test:

```bash
python main.py demo
```

Verify:

- ✅ Face detection (green bounding box)
- ✅ Eye tracking (green contours)
- ✅ Iris detection (red dots)
- ✅ Gaze point (yellow/red circle)
- ✅ Blink detection (red "BLINK!" text)

## 📝 License

MIT License - See LICENSE file for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Submit a pull request

## 📚 References

- [MediaPipe Face Mesh](https://google.github.io/mediapipe/solutions/face_mesh)
- [1€ Filter Paper](https://cristal.univ-lille.fr/~casiez/1euro/)
- [Eye Aspect Ratio for Blink Detection](https://www.pyimagesearch.com/2017/04/24/eye-blink-detection-opencv-python-dlib/)
