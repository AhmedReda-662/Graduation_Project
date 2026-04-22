"""
Gaze Tracking Pipeline
Main pipeline that integrates all components for real-time gaze tracking.
"""
import cv2
import numpy as np
import time
from typing import Optional, Dict, Any
from dataclasses import dataclass, asdict

from .models import FaceDetector, EyeTracker, GazeEstimator, BlinkDetector
from .models.gaze_estimator import GazePoint
from .models.blink_detector import BlinkEvent
from .utils.filters import GazeSmoother
from .config import config


@dataclass
class GazeTrackingResult:
    """Complete result from gaze tracking pipeline"""
    success: bool
    gaze_point: Optional[GazePoint] = None
    blink_event: Optional[BlinkEvent] = None
    face_detected: bool = False
    eyes_visible: bool = False
    confidence: float = 0.0
    processing_time_ms: float = 0.0
    timestamp: float = 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        result = {
            "success": self.success,
            "face_detected": self.face_detected,
            "eyes_visible": self.eyes_visible,
            "confidence": self.confidence,
            "processing_time_ms": self.processing_time_ms,
            "timestamp": self.timestamp
        }
        
        if self.gaze_point:
            result["gaze"] = {
                "x": self.gaze_point.x,
                "y": self.gaze_point.y,
                "confidence": self.gaze_point.confidence,
                "raw_x": self.gaze_point.raw_x,
                "raw_y": self.gaze_point.raw_y
            }
        else:
            result["gaze"] = None
        
        if self.blink_event:
            result["blink"] = {
                "duration_ms": self.blink_event.duration_ms,
                "eye": self.blink_event.eye,
                "is_intentional": self.blink_event.is_intentional
            }
        else:
            result["blink"] = None
        
        return result
    
    def to_response(self) -> Dict[str, Any]:
        """Convert to simplified response format as per requirements"""
        return {
            "x": self.gaze_point.x if self.gaze_point else 0,
            "y": self.gaze_point.y if self.gaze_point else 0,
            "confidence": self.confidence,
            "blink": self.blink_event is not None
        }


class GazeTrackingPipeline:
    """
    Main pipeline for real-time eye gaze tracking.
    Integrates face detection, eye tracking, gaze estimation, and blink detection.
    """
    
    def __init__(
        self,
        screen_width: int = None,
        screen_height: int = None,
        enable_smoothing: bool = True,
        smoothing_method: str = "one_euro"
    ):
        """
        Initialize the gaze tracking pipeline.
        
        Args:
            screen_width: Target screen width
            screen_height: Target screen height
            enable_smoothing: Whether to apply gaze smoothing
            smoothing_method: "kalman" or "one_euro"
        """
        self.screen_width = screen_width or config.screen_width
        self.screen_height = screen_height or config.screen_height
        
        # Initialize components
        self.face_detector = FaceDetector(
            max_faces=1,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5,
            refine_landmarks=True  # Enable iris tracking
        )
        
        self.eye_tracker = EyeTracker(
            smoothing_factor=config.gaze.smoothing_factor
        )
        
        self.gaze_estimator = GazeEstimator(
            screen_width=self.screen_width,
            screen_height=self.screen_height
        )
        
        self.blink_detector = BlinkDetector(
            ear_threshold=config.gaze.blink_threshold
        )
        
        # Gaze smoothing
        self.enable_smoothing = enable_smoothing
        self.smoother = GazeSmoother(method=smoothing_method) if enable_smoothing else None
        
        # Performance tracking
        self.frame_count = 0
        self.total_processing_time = 0
        self.fps = 0
        self.last_fps_update = time.time()
        
        # State
        self.is_calibrating = False
        self.calibration_point_index = 0
        self.calibration_samples = 0
        
    def process_frame(
        self,
        frame: np.ndarray,
        timestamp: float = None
    ) -> GazeTrackingResult:
        """
        Process a single frame through the gaze tracking pipeline.
        
        Args:
            frame: BGR image from camera
            timestamp: Frame timestamp in milliseconds
            
        Returns:
            GazeTrackingResult with gaze point and events
        """
        start_time = time.time()
        timestamp = timestamp or (time.time() * 1000)
        
        # Step 1: Face Detection
        face_result = self.face_detector.detect(frame)
        
        if not face_result.success:
            return GazeTrackingResult(
                success=False,
                face_detected=False,
                processing_time_ms=(time.time() - start_time) * 1000,
                timestamp=timestamp
            )
        
        # Step 2: Eye Tracking
        eye_result = self.eye_tracker.track(face_result)
        
        if not eye_result.success:
            return GazeTrackingResult(
                success=False,
                face_detected=True,
                eyes_visible=False,
                processing_time_ms=(time.time() - start_time) * 1000,
                timestamp=timestamp
            )
        
        # Step 3: Gaze Estimation
        gaze_point = self.gaze_estimator.estimate(eye_result, timestamp)
        
        if gaze_point and self.enable_smoothing and self.smoother:
            # Apply smoothing
            smooth_x, smooth_y = self.smoother.smooth(
                gaze_point.x,
                gaze_point.y,
                timestamp / 1000  # Convert to seconds for 1€ filter
            )
            gaze_point.x = int(smooth_x)
            gaze_point.y = int(smooth_y)
        
        # Step 4: Blink Detection
        blink_event = self.blink_detector.update(eye_result, timestamp)
        
        # Update performance metrics
        processing_time = (time.time() - start_time) * 1000
        self._update_performance(processing_time)
        
        return GazeTrackingResult(
            success=True,
            gaze_point=gaze_point,
            blink_event=blink_event,
            face_detected=True,
            eyes_visible=True,
            confidence=gaze_point.confidence if gaze_point else 0,
            processing_time_ms=processing_time,
            timestamp=timestamp
        )
    
    def start_calibration(self, num_points: int = 9):
        """Start calibration process"""
        self.is_calibrating = True
        self.calibration_point_index = 0
        self.calibration_samples = 0
        self.gaze_estimator.reset_calibration()
        self.eye_tracker.reset_smoothing()
        return self.gaze_estimator.get_calibration_points_grid(num_points)
    
    def add_calibration_sample(
        self,
        frame: np.ndarray,
        screen_x: int,
        screen_y: int
    ) -> bool:
        """
        Add a calibration sample for the current point.
        
        Args:
            frame: Camera frame
            screen_x: Target screen x coordinate
            screen_y: Target screen y coordinate
            
        Returns:
            True if sample was added successfully
        """
        face_result = self.face_detector.detect(frame)
        if not face_result.success:
            return False
        
        eye_result = self.eye_tracker.track(face_result)
        if not eye_result.success:
            return False
        
        # Average iris ratios from both eyes
        h_ratio = (eye_result.left_iris_ratio[0] + eye_result.right_iris_ratio[0]) / 2
        v_ratio = (eye_result.left_iris_ratio[1] + eye_result.right_iris_ratio[1]) / 2
        
        self.gaze_estimator.add_calibration_point(screen_x, screen_y, (h_ratio, v_ratio))
        self.calibration_samples += 1
        
        return True
    
    def finish_calibration(self) -> bool:
        """Complete calibration and compute mapping"""
        self.is_calibrating = False
        success = self.gaze_estimator.complete_calibration()
        
        if success:
            # Reset smoother for fresh tracking
            if self.smoother:
                self.smoother.reset()
            self.eye_tracker.reset_smoothing()
        
        return success
    
    def set_screen_size(self, width: int, height: int):
        """Update screen dimensions"""
        self.screen_width = width
        self.screen_height = height
        self.gaze_estimator.set_screen_size(width, height)
    
    def _update_performance(self, processing_time: float):
        """Update FPS and performance metrics"""
        self.frame_count += 1
        self.total_processing_time += processing_time
        
        current_time = time.time()
        if current_time - self.last_fps_update >= 1.0:
            self.fps = self.frame_count
            self.frame_count = 0
            self.last_fps_update = current_time
    
    def get_performance_stats(self) -> Dict[str, float]:
        """Get current performance statistics"""
        avg_time = self.total_processing_time / max(1, self.frame_count)
        return {
            "fps": self.fps,
            "avg_processing_time_ms": avg_time,
            "is_calibrated": self.gaze_estimator.is_calibrated
        }
    
    def draw_debug_overlay(
        self,
        frame: np.ndarray,
        result: GazeTrackingResult
    ) -> np.ndarray:
        """
        Draw debug visualization on frame.
        
        Args:
            frame: Input frame
            result: Gaze tracking result
            
        Returns:
            Frame with debug overlay
        """
        output = frame.copy()
        h, w = output.shape[:2]
        
        # Draw face detection
        face_result = self.face_detector.detect(frame)
        if face_result.success:
            output = self.face_detector.draw_landmarks(
                output, face_result,
                draw_face=True,
                draw_eyes=True,
                draw_iris=True
            )
        
        # Draw gaze point (scaled to frame size)
        if result.gaze_point:
            # Scale screen coordinates to frame coordinates
            scale_x = w / self.screen_width
            scale_y = h / self.screen_height
            gaze_x = int(result.gaze_point.x * scale_x)
            gaze_y = int(result.gaze_point.y * scale_y)
            
            # Draw gaze point
            cv2.circle(output, (gaze_x, gaze_y), 10, (0, 255, 255), -1)
            cv2.circle(output, (gaze_x, gaze_y), 12, (255, 255, 0), 2)
        
        # Draw stats
        stats_text = [
            f"FPS: {self.fps}",
            f"Time: {result.processing_time_ms:.1f}ms",
            f"Conf: {result.confidence:.2f}",
            f"Cal: {'Yes' if self.gaze_estimator.is_calibrated else 'No'}"
        ]
        
        for i, text in enumerate(stats_text):
            cv2.putText(
                output, text,
                (10, 30 + i * 25),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6, (0, 255, 0), 2
            )
        
        # Draw blink indicator
        if result.blink_event:
            cv2.putText(
                output, "BLINK!",
                (w - 100, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8, (0, 0, 255), 2
            )
        
        return output
    
    def export_calibration(self) -> dict:
        """Export calibration data"""
        return self.gaze_estimator.export_calibration()
    
    def import_calibration(self, data: dict) -> bool:
        """Import calibration data"""
        return self.gaze_estimator.import_calibration(data)
    
    def close(self):
        """Release resources"""
        self.face_detector.close()
