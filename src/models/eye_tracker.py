"""
Eye Tracker Module
Extracts detailed eye features for gaze estimation.
"""
import cv2
import numpy as np
from typing import Optional, Tuple, Dict
from dataclasses import dataclass
from .face_detector import FaceDetectionResult


@dataclass
class EyeTrackingResult:
    """Container for eye tracking results"""
    success: bool
    
    # Iris positions relative to eye corners (0-1 normalized)
    left_iris_ratio: Optional[Tuple[float, float]] = None  # (horizontal, vertical)
    right_iris_ratio: Optional[Tuple[float, float]] = None
    
    # Eye openness (for blink detection)
    left_eye_aspect_ratio: float = 0.0
    right_eye_aspect_ratio: float = 0.0
    
    # Raw positions
    left_iris_center: Optional[np.ndarray] = None
    right_iris_center: Optional[np.ndarray] = None
    
    # Gaze direction vector
    gaze_direction: Optional[np.ndarray] = None  # Normalized (x, y) direction


class EyeTracker:
    """
    Eye tracking module that extracts gaze-relevant features from face landmarks.
    Computes iris position ratios and eye aspect ratios for gaze estimation.
    """
    
    # Landmark indices for eye aspect ratio calculation
    # These are the vertical and horizontal points of the eye
    LEFT_EYE_VERTICAL = [(386, 374), (387, 373)]  # Upper-lower pairs
    LEFT_EYE_HORIZONTAL = (362, 263)  # Inner-outer
    
    RIGHT_EYE_VERTICAL = [(159, 145), (158, 153)]
    RIGHT_EYE_HORIZONTAL = (133, 33)
    
    def __init__(self, smoothing_factor: float = 0.3):
        """
        Initialize eye tracker.
        
        Args:
            smoothing_factor: Factor for exponential smoothing (0-1)
        """
        self.smoothing_factor = smoothing_factor
        self.prev_left_ratio = None
        self.prev_right_ratio = None
        self.prev_gaze = None
        
    def track(self, face_result: FaceDetectionResult) -> EyeTrackingResult:
        """
        Track eyes from face detection result.
        
        Args:
            face_result: Result from FaceDetector
            
        Returns:
            EyeTrackingResult with iris ratios and eye metrics
        """
        if not face_result.success:
            return EyeTrackingResult(success=False)
        
        landmarks = face_result.face_landmarks
        
        # Calculate iris position ratios
        left_iris_ratio = self._calculate_iris_ratio(
            face_result.left_iris_landmarks,
            face_result.left_eye_landmarks
        )
        right_iris_ratio = self._calculate_iris_ratio(
            face_result.right_iris_landmarks,
            face_result.right_eye_landmarks
        )
        
        # Apply smoothing
        if self.smoothing_factor > 0:
            left_iris_ratio = self._smooth_ratio(left_iris_ratio, self.prev_left_ratio)
            right_iris_ratio = self._smooth_ratio(right_iris_ratio, self.prev_right_ratio)
            self.prev_left_ratio = left_iris_ratio
            self.prev_right_ratio = right_iris_ratio
        
        # Calculate eye aspect ratios (for blink detection)
        left_ear = self._calculate_eye_aspect_ratio(landmarks, "left")
        right_ear = self._calculate_eye_aspect_ratio(landmarks, "right")
        
        # Get iris centers
        left_iris_center = face_result.left_iris_landmarks[:, :2].mean(axis=0)
        right_iris_center = face_result.right_iris_landmarks[:, :2].mean(axis=0)
        
        # Calculate gaze direction from iris ratios
        gaze_direction = self._calculate_gaze_direction(left_iris_ratio, right_iris_ratio)
        
        return EyeTrackingResult(
            success=True,
            left_iris_ratio=left_iris_ratio,
            right_iris_ratio=right_iris_ratio,
            left_eye_aspect_ratio=left_ear,
            right_eye_aspect_ratio=right_ear,
            left_iris_center=left_iris_center,
            right_iris_center=right_iris_center,
            gaze_direction=gaze_direction
        )
    
    def _calculate_iris_ratio(
        self,
        iris_landmarks: np.ndarray,
        eye_landmarks: np.ndarray
    ) -> Tuple[float, float]:
        """
        Calculate the iris position ratio within the eye region.
        
        Returns:
            (horizontal_ratio, vertical_ratio) where:
            - horizontal: 0 = looking left, 0.5 = center, 1 = looking right
            - vertical: 0 = looking up, 0.5 = center, 1 = looking down
        """
        # Get eye bounding box
        eye_pts = eye_landmarks[:, :2]
        eye_x_min, eye_y_min = eye_pts.min(axis=0)
        eye_x_max, eye_y_max = eye_pts.max(axis=0)
        
        # Get iris center
        iris_center = iris_landmarks[:, :2].mean(axis=0)
        
        # Calculate ratios
        eye_width = eye_x_max - eye_x_min
        eye_height = eye_y_max - eye_y_min
        
        if eye_width == 0 or eye_height == 0:
            return (0.5, 0.5)
        
        h_ratio = (iris_center[0] - eye_x_min) / eye_width
        v_ratio = (iris_center[1] - eye_y_min) / eye_height
        
        # Clamp to valid range
        h_ratio = max(0.0, min(1.0, h_ratio))
        v_ratio = max(0.0, min(1.0, v_ratio))
        
        return (h_ratio, v_ratio)
    
    def _smooth_ratio(
        self,
        current: Tuple[float, float],
        previous: Optional[Tuple[float, float]]
    ) -> Tuple[float, float]:
        """Apply exponential smoothing to ratio values"""
        if previous is None:
            return current
        
        alpha = self.smoothing_factor
        h = alpha * current[0] + (1 - alpha) * previous[0]
        v = alpha * current[1] + (1 - alpha) * previous[1]
        return (h, v)
    
    def _calculate_eye_aspect_ratio(
        self,
        landmarks: np.ndarray,
        eye: str
    ) -> float:
        """
        Calculate Eye Aspect Ratio (EAR) for blink detection.
        EAR = (|p2-p6| + |p3-p5|) / (2 * |p1-p4|)
        """
        if eye == "left":
            vertical_pairs = self.LEFT_EYE_VERTICAL
            horizontal = self.LEFT_EYE_HORIZONTAL
        else:
            vertical_pairs = self.RIGHT_EYE_VERTICAL
            horizontal = self.RIGHT_EYE_HORIZONTAL
        
        # Calculate vertical distances
        v_dist = 0
        for upper_idx, lower_idx in vertical_pairs:
            upper = landmarks[upper_idx, :2]
            lower = landmarks[lower_idx, :2]
            v_dist += np.linalg.norm(upper - lower)
        
        # Calculate horizontal distance
        inner = landmarks[horizontal[0], :2]
        outer = landmarks[horizontal[1], :2]
        h_dist = np.linalg.norm(inner - outer)
        
        if h_dist == 0:
            return 0.0
        
        ear = v_dist / (2.0 * h_dist)
        return ear
    
    def _calculate_gaze_direction(
        self,
        left_ratio: Tuple[float, float],
        right_ratio: Tuple[float, float]
    ) -> np.ndarray:
        """
        Calculate normalized gaze direction from iris ratios.
        
        Returns:
            Normalized direction vector (x, y) where:
            - x: -1 = left, 0 = center, 1 = right
            - y: -1 = up, 0 = center, 1 = down
        """
        # Average both eyes
        h_avg = (left_ratio[0] + right_ratio[0]) / 2
        v_avg = (left_ratio[1] + right_ratio[1]) / 2
        
        # Convert from 0-1 range to -1 to 1 range
        gaze_x = (h_avg - 0.5) * 2
        gaze_y = (v_avg - 0.5) * 2
        
        direction = np.array([gaze_x, gaze_y])
        
        # Apply smoothing to direction
        if self.prev_gaze is not None and self.smoothing_factor > 0:
            alpha = self.smoothing_factor
            direction = alpha * direction + (1 - alpha) * self.prev_gaze
        
        self.prev_gaze = direction
        return direction
    
    def reset_smoothing(self):
        """Reset smoothing state (call after calibration)"""
        self.prev_left_ratio = None
        self.prev_right_ratio = None
        self.prev_gaze = None
