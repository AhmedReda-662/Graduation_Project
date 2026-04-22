"""
Calibration System Module
Handles multi-point calibration with visual feedback.
"""
import cv2
import numpy as np
import time
from typing import List, Tuple, Optional, Callable
from dataclasses import dataclass
from enum import Enum


class CalibrationState(Enum):
    IDLE = "idle"
    COUNTDOWN = "countdown"
    COLLECTING = "collecting"
    TRANSITIONING = "transitioning"
    COMPLETE = "complete"
    FAILED = "failed"


@dataclass
class CalibrationProgress:
    """Current calibration progress"""
    state: CalibrationState
    current_point: int
    total_points: int
    samples_collected: int
    samples_needed: int
    countdown_remaining: float
    message: str


class CalibrationSystem:
    """
    Interactive calibration system for gaze tracking.
    Displays calibration points and collects gaze samples.
    """
    
    def __init__(
        self,
        screen_width: int,
        screen_height: int,
        num_points: int = 9,
        samples_per_point: int = 30,
        countdown_seconds: float = 1.5,
        point_display_ms: int = 2000,
        on_sample: Optional[Callable] = None,
        on_complete: Optional[Callable] = None
    ):
        """
        Initialize calibration system.
        
        Args:
            screen_width: Screen width in pixels
            screen_height: Screen height in pixels
            num_points: Number of calibration points (5 or 9)
            samples_per_point: Samples to collect per point
            countdown_seconds: Countdown before collecting at each point
            point_display_ms: Time to show each point
            on_sample: Callback when sample collected
            on_complete: Callback when calibration complete
        """
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.num_points = num_points
        self.samples_per_point = samples_per_point
        self.countdown_seconds = countdown_seconds
        self.point_display_ms = point_display_ms
        
        self.on_sample = on_sample
        self.on_complete = on_complete
        
        # Generate calibration points
        self.calibration_points = self._generate_points()
        
        # State
        self.state = CalibrationState.IDLE
        self.current_point_index = 0
        self.samples_collected = 0
        self.countdown_start = 0
        self.point_start_time = 0
        
        # Visual settings
        self.point_radius = 20
        self.point_color = (0, 255, 0)  # Green
        self.countdown_color = (255, 255, 0)  # Yellow
        self.pulse_speed = 3.0
        
    def _generate_points(self) -> List[Tuple[int, int]]:
        """Generate calibration point positions"""
        w = self.screen_width
        h = self.screen_height
        margin_x = w // 8
        margin_y = h // 8
        
        if self.num_points == 5:
            return [
                (w // 2, h // 2),  # Center
                (margin_x, margin_y),
                (w - margin_x, margin_y),
                (margin_x, h - margin_y),
                (w - margin_x, h - margin_y),
            ]
        else:  # 9 points
            points = []
            for row in range(3):
                for col in range(3):
                    x = margin_x + col * (w - 2 * margin_x) // 2
                    y = margin_y + row * (h - 2 * margin_y) // 2
                    points.append((x, y))
            return points
    
    def start(self) -> List[Tuple[int, int]]:
        """
        Start calibration process.
        
        Returns:
            List of calibration point coordinates
        """
        self.state = CalibrationState.COUNTDOWN
        self.current_point_index = 0
        self.samples_collected = 0
        self.countdown_start = time.time()
        
        return self.calibration_points
    
    def update(self, timestamp: float = None) -> CalibrationProgress:
        """
        Update calibration state.
        
        Args:
            timestamp: Current timestamp (uses time.time() if None)
            
        Returns:
            Current progress information
        """
        timestamp = timestamp or time.time()
        
        if self.state == CalibrationState.IDLE:
            return self._create_progress("Calibration not started")
        
        if self.state == CalibrationState.COMPLETE:
            return self._create_progress("Calibration complete!")
        
        if self.state == CalibrationState.COUNTDOWN:
            elapsed = timestamp - self.countdown_start
            remaining = self.countdown_seconds - elapsed
            
            if remaining <= 0:
                self.state = CalibrationState.COLLECTING
                self.point_start_time = timestamp
                return self._create_progress("Look at the point!")
            
            return CalibrationProgress(
                state=self.state,
                current_point=self.current_point_index + 1,
                total_points=self.num_points,
                samples_collected=self.samples_collected,
                samples_needed=self.samples_per_point,
                countdown_remaining=remaining,
                message=f"Get ready... {remaining:.1f}s"
            )
        
        if self.state == CalibrationState.COLLECTING:
            return self._create_progress(
                f"Collecting samples: {self.samples_collected}/{self.samples_per_point}"
            )
        
        if self.state == CalibrationState.TRANSITIONING:
            return self._create_progress("Moving to next point...")
        
        return self._create_progress("Unknown state")
    
    def add_sample(self, gaze_sample: Tuple[float, float]) -> bool:
        """
        Add a gaze sample for current calibration point.
        
        Args:
            gaze_sample: (h_ratio, v_ratio) from eye tracker
            
        Returns:
            True if sample was accepted
        """
        if self.state != CalibrationState.COLLECTING:
            return False
        
        current_point = self.calibration_points[self.current_point_index]
        
        # Call sample callback
        if self.on_sample:
            self.on_sample(current_point[0], current_point[1], gaze_sample)
        
        self.samples_collected += 1
        
        # Check if we have enough samples
        if self.samples_collected >= self.samples_per_point:
            self._advance_to_next_point()
        
        return True
    
    def _advance_to_next_point(self):
        """Move to the next calibration point"""
        self.current_point_index += 1
        self.samples_collected = 0
        
        if self.current_point_index >= self.num_points:
            # Calibration complete
            self.state = CalibrationState.COMPLETE
            if self.on_complete:
                self.on_complete()
        else:
            # Start countdown for next point
            self.state = CalibrationState.COUNTDOWN
            self.countdown_start = time.time()
    
    def get_current_point(self) -> Optional[Tuple[int, int]]:
        """Get current calibration point coordinates"""
        if self.state in [CalibrationState.IDLE, CalibrationState.COMPLETE]:
            return None
        
        if self.current_point_index < len(self.calibration_points):
            return self.calibration_points[self.current_point_index]
        return None
    
    def draw_overlay(self, frame: np.ndarray) -> np.ndarray:
        """
        Draw calibration overlay on frame.
        
        Args:
            frame: Input frame
            
        Returns:
            Frame with calibration overlay
        """
        if self.state == CalibrationState.IDLE:
            return frame
        
        output = frame.copy()
        h, w = output.shape[:2]
        
        # Scale factor from screen to frame
        scale_x = w / self.screen_width
        scale_y = h / self.screen_height
        
        current_point = self.get_current_point()
        
        if current_point and self.state != CalibrationState.COMPLETE:
            px = int(current_point[0] * scale_x)
            py = int(current_point[1] * scale_y)
            
            # Pulse effect
            t = time.time() * self.pulse_speed
            pulse = int(5 * np.sin(t) + self.point_radius)
            
            if self.state == CalibrationState.COUNTDOWN:
                # Yellow during countdown
                cv2.circle(output, (px, py), pulse + 10, self.countdown_color, 3)
                cv2.circle(output, (px, py), pulse, self.point_color, -1)
            else:
                # Green during collection
                cv2.circle(output, (px, py), pulse, self.point_color, -1)
            
            # Draw small center dot
            cv2.circle(output, (px, py), 3, (255, 255, 255), -1)
        
        # Draw progress bar
        progress = self.samples_collected / self.samples_per_point
        bar_width = 200
        bar_height = 10
        bar_x = (w - bar_width) // 2
        bar_y = h - 40
        
        cv2.rectangle(output, (bar_x, bar_y), (bar_x + bar_width, bar_y + bar_height), (100, 100, 100), -1)
        cv2.rectangle(output, (bar_x, bar_y), (bar_x + int(bar_width * progress), bar_y + bar_height), self.point_color, -1)
        
        # Draw text
        text = f"Point {self.current_point_index + 1}/{self.num_points}"
        cv2.putText(output, text, (bar_x, bar_y - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
        
        return output
    
    def _create_progress(self, message: str) -> CalibrationProgress:
        """Create progress object"""
        return CalibrationProgress(
            state=self.state,
            current_point=self.current_point_index + 1,
            total_points=self.num_points,
            samples_collected=self.samples_collected,
            samples_needed=self.samples_per_point,
            countdown_remaining=0,
            message=message
        )
    
    def reset(self):
        """Reset calibration state"""
        self.state = CalibrationState.IDLE
        self.current_point_index = 0
        self.samples_collected = 0
    
    def is_complete(self) -> bool:
        """Check if calibration is complete"""
        return self.state == CalibrationState.COMPLETE
    
    def is_active(self) -> bool:
        """Check if calibration is in progress"""
        return self.state not in [CalibrationState.IDLE, CalibrationState.COMPLETE]
