"""
Blink Detector Module
Detects eye blinks for interaction (click/select).
"""
import numpy as np
from collections import deque
from typing import Optional, Tuple
from dataclasses import dataclass
from .eye_tracker import EyeTrackingResult


@dataclass
class BlinkEvent:
    """Represents a detected blink event"""
    timestamp: float
    duration_ms: float
    eye: str  # "left", "right", or "both"
    is_intentional: bool  # True if likely intentional (longer than threshold)


class BlinkDetector:
    """
    Detects eye blinks using Eye Aspect Ratio (EAR).
    Differentiates between natural and intentional blinks.
    """
    
    def __init__(
        self,
        ear_threshold: float = 0.25,
        min_blink_frames: int = 2,
        max_blink_frames: int = 15,
        intentional_threshold_ms: float = 150,
        history_size: int = 30
    ):
        """
        Initialize blink detector.
        
        Args:
            ear_threshold: Eye aspect ratio below which eye is considered closed
            min_blink_frames: Minimum frames for valid blink
            max_blink_frames: Maximum frames before considered closed (not blink)
            intentional_threshold_ms: Duration threshold for intentional blink
            history_size: Number of frames to keep in history
        """
        self.ear_threshold = ear_threshold
        self.min_blink_frames = min_blink_frames
        self.max_blink_frames = max_blink_frames
        self.intentional_threshold_ms = intentional_threshold_ms
        
        # State tracking
        self.left_eye_closed = False
        self.right_eye_closed = False
        self.left_closed_start = 0
        self.right_closed_start = 0
        self.left_closed_frames = 0
        self.right_closed_frames = 0
        
        # History for smoothing
        self.left_ear_history = deque(maxlen=history_size)
        self.right_ear_history = deque(maxlen=history_size)
        
        # Blink cooldown (prevent double detection)
        self.last_blink_time = 0
        self.blink_cooldown_ms = 200
        
        # Frame timing
        self.frame_time_ms = 33.33  # ~30 FPS default
        
    def update(
        self,
        eye_result: EyeTrackingResult,
        timestamp: float
    ) -> Optional[BlinkEvent]:
        """
        Update blink detection with new eye tracking data.
        
        Args:
            eye_result: Eye tracking result with aspect ratios
            timestamp: Current timestamp in milliseconds
            
        Returns:
            BlinkEvent if a blink was detected, None otherwise
        """
        if not eye_result.success:
            return None
        
        left_ear = eye_result.left_eye_aspect_ratio
        right_ear = eye_result.right_eye_aspect_ratio
        
        # Add to history
        self.left_ear_history.append(left_ear)
        self.right_ear_history.append(right_ear)
        
        # Smooth EAR values
        smooth_left = np.mean(list(self.left_ear_history)[-3:]) if len(self.left_ear_history) >= 3 else left_ear
        smooth_right = np.mean(list(self.right_ear_history)[-3:]) if len(self.right_ear_history) >= 3 else right_ear
        
        # Check for blink cooldown
        if timestamp - self.last_blink_time < self.blink_cooldown_ms:
            self._update_state(smooth_left, smooth_right, timestamp)
            return None
        
        # Detect blinks
        blink_event = None
        
        # Check both eyes (most common natural blink)
        both_closed = smooth_left < self.ear_threshold and smooth_right < self.ear_threshold
        
        if both_closed and not (self.left_eye_closed and self.right_eye_closed):
            # Eyes just closed
            self.left_eye_closed = True
            self.right_eye_closed = True
            self.left_closed_start = timestamp
            self.right_closed_start = timestamp
            self.left_closed_frames = 1
            self.right_closed_frames = 1
            
        elif not both_closed and (self.left_eye_closed and self.right_eye_closed):
            # Eyes just opened - blink complete
            duration = timestamp - self.left_closed_start
            
            if self.min_blink_frames <= self.left_closed_frames <= self.max_blink_frames:
                is_intentional = duration >= self.intentional_threshold_ms
                blink_event = BlinkEvent(
                    timestamp=timestamp,
                    duration_ms=duration,
                    eye="both",
                    is_intentional=is_intentional
                )
                self.last_blink_time = timestamp
            
            self.left_eye_closed = False
            self.right_eye_closed = False
            self.left_closed_frames = 0
            self.right_closed_frames = 0
            
        elif self.left_eye_closed and self.right_eye_closed:
            # Eyes still closed
            self.left_closed_frames += 1
            self.right_closed_frames += 1
        
        # Update individual eye states (for wink detection)
        self._update_single_eye_state(smooth_left, "left", timestamp)
        self._update_single_eye_state(smooth_right, "right", timestamp)
        
        return blink_event
    
    def _update_state(self, left_ear: float, right_ear: float, timestamp: float):
        """Update internal state without detecting blinks"""
        if left_ear < self.ear_threshold:
            self.left_closed_frames += 1
        else:
            self.left_eye_closed = False
            self.left_closed_frames = 0
            
        if right_ear < self.ear_threshold:
            self.right_closed_frames += 1
        else:
            self.right_eye_closed = False
            self.right_closed_frames = 0
    
    def _update_single_eye_state(self, ear: float, eye: str, timestamp: float):
        """Update state for individual eye (wink detection)"""
        if eye == "left":
            closed = self.left_eye_closed
            other_closed = self.right_eye_closed
        else:
            closed = self.right_eye_closed
            other_closed = self.left_eye_closed
        
        # Wink = one eye closed while other is open
        # Not implementing full wink detection here, but tracking state
        pass
    
    def is_eyes_closed(self) -> Tuple[bool, bool]:
        """
        Check if eyes are currently closed.
        
        Returns:
            (left_closed, right_closed) tuple
        """
        return self.left_eye_closed, self.right_eye_closed
    
    def get_average_ear(self) -> float:
        """Get average Eye Aspect Ratio across both eyes"""
        if not self.left_ear_history or not self.right_ear_history:
            return 0.3  # Default open eye value
        
        left_avg = np.mean(list(self.left_ear_history))
        right_avg = np.mean(list(self.right_ear_history))
        return (left_avg + right_avg) / 2
    
    def set_frame_rate(self, fps: float):
        """Update frame timing based on actual FPS"""
        self.frame_time_ms = 1000.0 / fps
    
    def set_threshold(self, threshold: float):
        """Adjust blink detection sensitivity"""
        self.ear_threshold = threshold
    
    def reset(self):
        """Reset detector state"""
        self.left_eye_closed = False
        self.right_eye_closed = False
        self.left_closed_start = 0
        self.right_closed_start = 0
        self.left_closed_frames = 0
        self.right_closed_frames = 0
        self.left_ear_history.clear()
        self.right_ear_history.clear()
        self.last_blink_time = 0
