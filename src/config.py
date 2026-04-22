# Eye Gaze Tracking System Configuration
from pydantic import BaseModel
from typing import Optional
import os


class CameraConfig(BaseModel):
    """Camera capture settings"""
    width: int = 640
    height: int = 480
    fps: int = 30
    flip_horizontal: bool = True


class GazeConfig(BaseModel):
    """Gaze estimation parameters"""
    smoothing_enabled: bool = True
    smoothing_factor: float = 0.3
    confidence_threshold: float = 0.5
    blink_threshold: float = 0.25  # Eye aspect ratio threshold


class InteractionConfig(BaseModel):
    """Interaction handling settings"""
    dwell_time_ms: int = 800  # Time to trigger selection
    scroll_threshold: float = 0.2  # Gaze offset to trigger scroll
    scroll_speed: float = 5.0
    hover_radius: int = 50  # Pixels around gaze point for hover detection


class CalibrationConfig(BaseModel):
    """Calibration system settings"""
    num_points: int = 9  # 5 or 9 point calibration
    samples_per_point: int = 30
    point_display_time_ms: int = 2000


class ServerConfig(BaseModel):
    """Backend server settings"""
    host: str = "0.0.0.0"
    port: int = 8000
    websocket_path: str = "/ws/gaze"
    max_connections: int = 10
    frame_buffer_size: int = 5


class SystemConfig(BaseModel):
    """Main system configuration"""
    camera: CameraConfig = CameraConfig()
    gaze: GazeConfig = GazeConfig()
    interaction: InteractionConfig = InteractionConfig()
    calibration: CalibrationConfig = CalibrationConfig()
    server: ServerConfig = ServerConfig()
    
    # Performance settings
    target_fps: int = 30
    max_latency_ms: int = 50
    enable_gpu: bool = False
    
    # Privacy settings
    store_frames: bool = False
    encrypt_transport: bool = True
    
    # Screen dimensions (to be set by client)
    screen_width: int = 1080
    screen_height: int = 1920


# Global config instance
config = SystemConfig()


def load_config_from_env():
    """Load configuration from environment variables"""
    global config
    
    if os.getenv("GAZE_SERVER_HOST"):
        config.server.host = os.getenv("GAZE_SERVER_HOST")
    
    if os.getenv("GAZE_SERVER_PORT"):
        config.server.port = int(os.getenv("GAZE_SERVER_PORT"))
    
    if os.getenv("GAZE_ENABLE_GPU"):
        config.enable_gpu = os.getenv("GAZE_ENABLE_GPU").lower() == "true"
    
    if os.getenv("GAZE_TARGET_FPS"):
        config.target_fps = int(os.getenv("GAZE_TARGET_FPS"))
    
    return config
