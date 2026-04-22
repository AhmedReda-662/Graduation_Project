"""
FastAPI WebSocket Server for Real-time Gaze Tracking
Handles video frame streaming and gaze coordinate responses.
"""
import asyncio
import base64
import json
import time
import cv2
import numpy as np
from typing import Dict, Set, Optional
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import uvicorn

from .pipeline import GazeTrackingPipeline
from .config import config, load_config_from_env
from .interactions import InteractionHandler, UIElement


# Initialize FastAPI app
app = FastAPI(
    title="Eye Gaze Tracking API",
    description="Real-time eye gaze tracking for educational applications",
    version="1.0.0"
)

# CORS middleware for mobile app access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Connection manager for WebSocket clients
class ConnectionManager:
    """Manages WebSocket connections"""
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.pipelines: Dict[str, GazeTrackingPipeline] = {}
        self.interactions: Dict[str, InteractionHandler] = {}
        
    async def connect(self, websocket: WebSocket, client_id: str):
        await websocket.accept()
        self.active_connections[client_id] = websocket
        
        # Create pipeline for this client
        self.pipelines[client_id] = GazeTrackingPipeline(
            screen_width=config.screen_width,
            screen_height=config.screen_height,
            enable_smoothing=config.gaze.smoothing_enabled
        )
        
        # Create interaction handler
        self.interactions[client_id] = InteractionHandler(
            dwell_time_ms=config.interaction.dwell_time_ms,
            scroll_threshold=config.interaction.scroll_threshold,
            scroll_speed=config.interaction.scroll_speed,
            hover_radius=config.interaction.hover_radius
        )
        
    def disconnect(self, client_id: str):
        if client_id in self.active_connections:
            del self.active_connections[client_id]
        if client_id in self.pipelines:
            self.pipelines[client_id].close()
            del self.pipelines[client_id]
        if client_id in self.interactions:
            del self.interactions[client_id]
    
    async def send_json(self, client_id: str, data: dict):
        if client_id in self.active_connections:
            await self.active_connections[client_id].send_json(data)
    
    def get_pipeline(self, client_id: str) -> Optional[GazeTrackingPipeline]:
        return self.pipelines.get(client_id)
    
    def get_interactions(self, client_id: str) -> Optional[InteractionHandler]:
        return self.interactions.get(client_id)


manager = ConnectionManager()


# Pydantic models for API
class ScreenConfig(BaseModel):
    width: int
    height: int


class CalibrationRequest(BaseModel):
    num_points: int = 9


class UIElementRequest(BaseModel):
    id: str
    x: int
    y: int
    width: int
    height: int
    selectable: bool = True
    scrollable: bool = False


# REST Endpoints
@app.get("/")
async def root():
    return {"message": "Eye Gaze Tracking API", "version": "1.0.0"}


@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": time.time()}


@app.post("/config/screen")
async def set_screen_config(screen: ScreenConfig):
    """Update screen dimensions"""
    config.screen_width = screen.width
    config.screen_height = screen.height
    return {"status": "updated", "screen": screen.dict()}


# WebSocket endpoint for real-time gaze tracking
@app.websocket("/ws/gaze/{client_id}")
async def websocket_gaze_endpoint(websocket: WebSocket, client_id: str):
    """
    WebSocket endpoint for real-time gaze tracking.
    
    Protocol:
    - Client sends: {"type": "frame", "data": "<base64_image>"}
    - Server responds: {"x": int, "y": int, "confidence": float, "blink": bool}
    
    Additional message types:
    - {"type": "configure", "screen_width": int, "screen_height": int}
    - {"type": "calibrate_start", "num_points": int}
    - {"type": "calibrate_sample", "screen_x": int, "screen_y": int}
    - {"type": "calibrate_finish"}
    - {"type": "register_element", ...element data}
    """
    await manager.connect(websocket, client_id)
    
    try:
        while True:
            # Receive message
            data = await websocket.receive_text()
            message = json.loads(data)
            
            msg_type = message.get("type", "frame")
            
            if msg_type == "frame":
                # Process video frame
                response = await process_frame(client_id, message)
                await manager.send_json(client_id, response)
                
            elif msg_type == "configure":
                # Configure screen size
                pipeline = manager.get_pipeline(client_id)
                if pipeline:
                    pipeline.set_screen_size(
                        message.get("screen_width", config.screen_width),
                        message.get("screen_height", config.screen_height)
                    )
                await manager.send_json(client_id, {"status": "configured"})
                
            elif msg_type == "calibrate_start":
                # Start calibration
                response = await start_calibration(client_id, message)
                await manager.send_json(client_id, response)
                
            elif msg_type == "calibrate_sample":
                # Add calibration sample
                response = await add_calibration_sample(client_id, message)
                await manager.send_json(client_id, response)
                
            elif msg_type == "calibrate_finish":
                # Finish calibration
                response = await finish_calibration(client_id)
                await manager.send_json(client_id, response)
                
            elif msg_type == "register_element":
                # Register UI element for interaction
                response = await register_element(client_id, message)
                await manager.send_json(client_id, response)
                
            elif msg_type == "clear_elements":
                # Clear all registered elements
                interactions = manager.get_interactions(client_id)
                if interactions:
                    interactions.clear_elements()
                await manager.send_json(client_id, {"status": "cleared"})
                
            elif msg_type == "export_calibration":
                # Export calibration data
                pipeline = manager.get_pipeline(client_id)
                if pipeline:
                    cal_data = pipeline.export_calibration()
                    await manager.send_json(client_id, {"calibration": cal_data})
                    
            elif msg_type == "import_calibration":
                # Import calibration data
                pipeline = manager.get_pipeline(client_id)
                if pipeline:
                    success = pipeline.import_calibration(message.get("calibration", {}))
                    await manager.send_json(client_id, {"status": "imported" if success else "failed"})
                
    except WebSocketDisconnect:
        manager.disconnect(client_id)
    except Exception as e:
        print(f"WebSocket error for {client_id}: {e}")
        manager.disconnect(client_id)


async def process_frame(client_id: str, message: dict) -> dict:
    """Process a video frame and return gaze coordinates"""
    pipeline = manager.get_pipeline(client_id)
    interactions = manager.get_interactions(client_id)
    
    if not pipeline:
        return {"error": "Pipeline not initialized"}
    
    # Decode base64 image
    try:
        image_data = message.get("data", "")
        if image_data.startswith("data:image"):
            # Remove data URL prefix
            image_data = image_data.split(",")[1]
        
        image_bytes = base64.b64decode(image_data)
        nparr = np.frombuffer(image_bytes, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if frame is None:
            return {"error": "Failed to decode image"}
            
    except Exception as e:
        return {"error": f"Image decode error: {str(e)}"}
    
    # Process through pipeline
    timestamp = message.get("timestamp", time.time() * 1000)
    result = pipeline.process_frame(frame, timestamp)
    
    # Build response
    response = result.to_response()
    
    # Add interaction events if gaze detected
    if result.success and result.gaze_point and interactions:
        events = interactions.update(
            result.gaze_point.x,
            result.gaze_point.y,
            timestamp,
            result.blink_event is not None
        )
        
        if events:
            response["interactions"] = [
                {
                    "type": e.type.value,
                    "element_id": e.element_id,
                    "duration_ms": e.duration_ms
                }
                for e in events
            ]
        
        # Add dwell progress
        element_id, progress = interactions.get_dwell_progress()
        if element_id:
            response["dwell"] = {
                "element_id": element_id,
                "progress": progress
            }
    
    response["processing_time_ms"] = result.processing_time_ms
    
    return response


async def start_calibration(client_id: str, message: dict) -> dict:
    """Start calibration process"""
    pipeline = manager.get_pipeline(client_id)
    if not pipeline:
        return {"error": "Pipeline not initialized"}
    
    num_points = message.get("num_points", 9)
    calibration_points = pipeline.start_calibration(num_points)
    
    return {
        "status": "calibration_started",
        "points": [{"x": p[0], "y": p[1]} for p in calibration_points]
    }


async def add_calibration_sample(client_id: str, message: dict) -> dict:
    """Add a calibration sample"""
    pipeline = manager.get_pipeline(client_id)
    if not pipeline:
        return {"error": "Pipeline not initialized"}
    
    # Decode frame
    try:
        image_data = message.get("frame_data", "")
        if image_data.startswith("data:image"):
            image_data = image_data.split(",")[1]
        
        image_bytes = base64.b64decode(image_data)
        nparr = np.frombuffer(image_bytes, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if frame is None:
            return {"error": "Failed to decode image"}
            
    except Exception as e:
        return {"error": f"Image decode error: {str(e)}"}
    
    screen_x = message.get("screen_x", 0)
    screen_y = message.get("screen_y", 0)
    
    success = pipeline.add_calibration_sample(frame, screen_x, screen_y)
    
    return {
        "status": "sample_added" if success else "sample_failed",
        "point": {"x": screen_x, "y": screen_y}
    }


async def finish_calibration(client_id: str) -> dict:
    """Finish calibration and compute mapping"""
    pipeline = manager.get_pipeline(client_id)
    if not pipeline:
        return {"error": "Pipeline not initialized"}
    
    success = pipeline.finish_calibration()
    
    return {
        "status": "calibration_complete" if success else "calibration_failed",
        "is_calibrated": pipeline.gaze_estimator.is_calibrated
    }


async def register_element(client_id: str, message: dict) -> dict:
    """Register a UI element for interaction"""
    interactions = manager.get_interactions(client_id)
    if not interactions:
        return {"error": "Interaction handler not initialized"}
    
    element = UIElement(
        id=message.get("id"),
        x=message.get("x", 0),
        y=message.get("y", 0),
        width=message.get("width", 100),
        height=message.get("height", 100),
        selectable=message.get("selectable", True),
        scrollable=message.get("scrollable", False)
    )
    
    interactions.register_element(element)
    
    return {"status": "element_registered", "id": element.id}


# Demo HTML page
@app.get("/demo", response_class=HTMLResponse)
async def demo_page():
    """Serve demo HTML page for testing"""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Eye Gaze Tracking Demo</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; background: #1a1a2e; color: white; }
            #video { transform: scaleX(-1); border-radius: 8px; }
            #canvas { display: none; }
            #gazeIndicator {
                position: fixed;
                width: 30px;
                height: 30px;
                border-radius: 50%;
                background: rgba(255, 0, 0, 0.7);
                border: 3px solid yellow;
                pointer-events: none;
                transform: translate(-50%, -50%);
                transition: all 0.05s ease;
                z-index: 1000;
            }
            .stats { margin-top: 20px; padding: 10px; background: #16213e; border-radius: 8px; }
            .controls { margin: 20px 0; }
            button { 
                padding: 10px 20px; 
                margin: 5px;
                background: #e94560;
                color: white;
                border: none;
                border-radius: 5px;
                cursor: pointer;
            }
            button:hover { background: #ff6b6b; }
            .status { color: #00ff88; }
        </style>
    </head>
    <body>
        <h1>🎯 Eye Gaze Tracking Demo</h1>
        
        <div class="controls">
            <button onclick="startTracking()">Start Tracking</button>
            <button onclick="stopTracking()">Stop Tracking</button>
            <button onclick="startCalibration()">Calibrate</button>
        </div>
        
        <video id="video" width="640" height="480" autoplay></video>
        <canvas id="canvas" width="640" height="480"></canvas>
        
        <div id="gazeIndicator" style="display: none;"></div>
        
        <div class="stats">
            <p>Status: <span id="status" class="status">Disconnected</span></p>
            <p>FPS: <span id="fps">0</span></p>
            <p>Gaze: (<span id="gazeX">0</span>, <span id="gazeY">0</span>)</p>
            <p>Confidence: <span id="confidence">0</span></p>
            <p>Processing Time: <span id="procTime">0</span>ms</p>
        </div>
        
        <script>
            const video = document.getElementById('video');
            const canvas = document.getElementById('canvas');
            const ctx = canvas.getContext('2d');
            const gazeIndicator = document.getElementById('gazeIndicator');
            
            let ws = null;
            let tracking = false;
            let frameCount = 0;
            let lastFpsUpdate = Date.now();
            
            // Get camera
            navigator.mediaDevices.getUserMedia({ video: true })
                .then(stream => {
                    video.srcObject = stream;
                    document.getElementById('status').textContent = 'Camera ready';
                })
                .catch(err => {
                    document.getElementById('status').textContent = 'Camera error: ' + err;
                });
            
            function connectWebSocket() {
                const clientId = 'demo_' + Date.now();
                ws = new WebSocket(`ws://${window.location.host}/ws/gaze/${clientId}`);
                
                ws.onopen = () => {
                    document.getElementById('status').textContent = 'Connected';
                    // Configure screen size
                    ws.send(JSON.stringify({
                        type: 'configure',
                        screen_width: window.innerWidth,
                        screen_height: window.innerHeight
                    }));
                };
                
                ws.onmessage = (event) => {
                    const data = JSON.parse(event.data);
                    if (data.x !== undefined) {
                        updateGaze(data);
                    }
                };
                
                ws.onclose = () => {
                    document.getElementById('status').textContent = 'Disconnected';
                    tracking = false;
                };
            }
            
            function startTracking() {
                if (!ws || ws.readyState !== WebSocket.OPEN) {
                    connectWebSocket();
                    setTimeout(() => { tracking = true; sendFrame(); }, 500);
                } else {
                    tracking = true;
                    sendFrame();
                }
                gazeIndicator.style.display = 'block';
            }
            
            function stopTracking() {
                tracking = false;
                gazeIndicator.style.display = 'none';
            }
            
            function sendFrame() {
                if (!tracking || !ws || ws.readyState !== WebSocket.OPEN) return;
                
                ctx.drawImage(video, 0, 0);
                const frameData = canvas.toDataURL('image/jpeg', 0.8);
                
                ws.send(JSON.stringify({
                    type: 'frame',
                    data: frameData,
                    timestamp: Date.now()
                }));
                
                // Update FPS
                frameCount++;
                const now = Date.now();
                if (now - lastFpsUpdate >= 1000) {
                    document.getElementById('fps').textContent = frameCount;
                    frameCount = 0;
                    lastFpsUpdate = now;
                }
                
                requestAnimationFrame(sendFrame);
            }
            
            function updateGaze(data) {
                document.getElementById('gazeX').textContent = data.x;
                document.getElementById('gazeY').textContent = data.y;
                document.getElementById('confidence').textContent = data.confidence.toFixed(2);
                document.getElementById('procTime').textContent = data.processing_time_ms?.toFixed(1) || '0';
                
                // Move gaze indicator
                gazeIndicator.style.left = data.x + 'px';
                gazeIndicator.style.top = data.y + 'px';
                
                // Change color based on confidence
                const hue = data.confidence * 120; // 0=red, 120=green
                gazeIndicator.style.background = `hsla(${hue}, 100%, 50%, 0.7)`;
            }
            
            function startCalibration() {
                if (!ws || ws.readyState !== WebSocket.OPEN) {
                    alert('Connect first!');
                    return;
                }
                ws.send(JSON.stringify({ type: 'calibrate_start', num_points: 9 }));
            }
        </script>
    </body>
    </html>
    """


def run_server(host: str = None, port: int = None):
    """Run the FastAPI server"""
    load_config_from_env()
    uvicorn.run(
        app,
        host=host or config.server.host,
        port=port or config.server.port,
        log_level="info"
    )


if __name__ == "__main__":
    run_server()
