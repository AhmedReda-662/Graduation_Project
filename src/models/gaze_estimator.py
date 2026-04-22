"""
Gaze Estimator Module
Maps eye tracking data to screen coordinates using calibration.
"""
import numpy as np
from typing import Optional, Tuple, List
from dataclasses import dataclass
from scipy import interpolate
from .eye_tracker import EyeTrackingResult


@dataclass
class GazePoint:
    """Gaze estimation result"""
    x: int  # Screen x coordinate
    y: int  # Screen y coordinate
    confidence: float  # Confidence score 0-1
    raw_x: float  # Raw normalized x
    raw_y: float  # Raw normalized y
    timestamp: float = 0.0


@dataclass
class CalibrationPoint:
    """Single calibration point data"""
    screen_x: int
    screen_y: int
    gaze_samples: List[Tuple[float, float]]  # List of (h_ratio, v_ratio) samples


class GazeEstimator:
    """
    Maps eye gaze direction to screen coordinates.
    Uses calibration data to create a personalized mapping.
    """
    
    def __init__(
        self,
        screen_width: int = 1080,
        screen_height: int = 1920,
        calibration_method: str = "polynomial"
    ):
        """
        Initialize gaze estimator.
        
        Args:
            screen_width: Target screen width in pixels
            screen_height: Target screen height in pixels
            calibration_method: "polynomial" or "rbf" interpolation
        """
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.calibration_method = calibration_method
        
        # Calibration data
        self.calibration_points: List[CalibrationPoint] = []
        self.is_calibrated = False
        
        # Mapping functions (set after calibration)
        self._map_x = None
        self._map_y = None
        
        # Polynomial coefficients (for polynomial method)
        self._poly_coeffs_x = None
        self._poly_coeffs_y = None
        
        # Default linear mapping (before calibration)
        self._use_default_mapping = True
        
    def estimate(
        self,
        eye_result: EyeTrackingResult,
        timestamp: float = 0.0
    ) -> Optional[GazePoint]:
        """
        Estimate screen gaze point from eye tracking data.
        
        Args:
            eye_result: Eye tracking result
            timestamp: Frame timestamp
            
        Returns:
            GazePoint with screen coordinates
        """
        if not eye_result.success:
            return None
        
        # Get average gaze direction
        gaze = eye_result.gaze_direction
        if gaze is None:
            return None
        
        # Normalize to 0-1 range
        norm_x = (gaze[0] + 1) / 2  # -1,1 -> 0,1
        norm_y = (gaze[1] + 1) / 2
        
        if self.is_calibrated and not self._use_default_mapping:
            # Use calibrated mapping
            screen_x, screen_y = self._apply_calibrated_mapping(norm_x, norm_y)
        else:
            # Default linear mapping
            screen_x = norm_x * self.screen_width
            screen_y = norm_y * self.screen_height
        
        # Clamp to screen bounds
        screen_x = max(0, min(self.screen_width - 1, int(screen_x)))
        screen_y = max(0, min(self.screen_height - 1, int(screen_y)))
        
        # Calculate confidence based on eye tracking quality
        confidence = self._calculate_confidence(eye_result)
        
        return GazePoint(
            x=screen_x,
            y=screen_y,
            confidence=confidence,
            raw_x=norm_x,
            raw_y=norm_y,
            timestamp=timestamp
        )
    
    def add_calibration_point(
        self,
        screen_x: int,
        screen_y: int,
        gaze_sample: Tuple[float, float]
    ):
        """
        Add a calibration sample.
        
        Args:
            screen_x: Target screen x coordinate
            screen_y: Target screen y coordinate
            gaze_sample: (horizontal_ratio, vertical_ratio) from eye tracking
        """
        # Find existing point or create new
        for point in self.calibration_points:
            if point.screen_x == screen_x and point.screen_y == screen_y:
                point.gaze_samples.append(gaze_sample)
                return
        
        # New calibration point
        self.calibration_points.append(CalibrationPoint(
            screen_x=screen_x,
            screen_y=screen_y,
            gaze_samples=[gaze_sample]
        ))
    
    def complete_calibration(self) -> bool:
        """
        Finalize calibration and compute mapping function.
        
        Returns:
            True if calibration was successful
        """
        if len(self.calibration_points) < 4:
            print("Warning: Need at least 4 calibration points")
            return False
        
        # Extract averaged calibration data
        screen_coords = []
        gaze_coords = []
        
        for point in self.calibration_points:
            if len(point.gaze_samples) == 0:
                continue
            
            # Average gaze samples for this point
            h_avg = np.mean([s[0] for s in point.gaze_samples])
            v_avg = np.mean([s[1] for s in point.gaze_samples])
            
            # Convert to normalized gaze direction (-1 to 1)
            gaze_x = (h_avg - 0.5) * 2
            gaze_y = (v_avg - 0.5) * 2
            
            # Normalize to 0-1
            norm_x = (gaze_x + 1) / 2
            norm_y = (gaze_y + 1) / 2
            
            screen_coords.append([point.screen_x, point.screen_y])
            gaze_coords.append([norm_x, norm_y])
        
        screen_coords = np.array(screen_coords)
        gaze_coords = np.array(gaze_coords)
        
        try:
            if self.calibration_method == "polynomial":
                self._fit_polynomial_mapping(gaze_coords, screen_coords)
            else:
                self._fit_rbf_mapping(gaze_coords, screen_coords)
            
            self.is_calibrated = True
            self._use_default_mapping = False
            return True
            
        except Exception as e:
            print(f"Calibration failed: {e}")
            return False
    
    def _fit_polynomial_mapping(
        self,
        gaze_coords: np.ndarray,
        screen_coords: np.ndarray
    ):
        """Fit 2nd degree polynomial mapping"""
        # Build design matrix for 2nd degree polynomial
        # [1, x, y, x^2, xy, y^2]
        X = gaze_coords[:, 0]
        Y = gaze_coords[:, 1]
        
        A = np.column_stack([
            np.ones_like(X),
            X, Y,
            X**2, X*Y, Y**2
        ])
        
        # Solve for coefficients using least squares
        self._poly_coeffs_x, _, _, _ = np.linalg.lstsq(A, screen_coords[:, 0], rcond=None)
        self._poly_coeffs_y, _, _, _ = np.linalg.lstsq(A, screen_coords[:, 1], rcond=None)
    
    def _fit_rbf_mapping(
        self,
        gaze_coords: np.ndarray,
        screen_coords: np.ndarray
    ):
        """Fit RBF (Radial Basis Function) interpolation"""
        self._map_x = interpolate.Rbf(
            gaze_coords[:, 0],
            gaze_coords[:, 1],
            screen_coords[:, 0],
            function='thin_plate'
        )
        self._map_y = interpolate.Rbf(
            gaze_coords[:, 0],
            gaze_coords[:, 1],
            screen_coords[:, 1],
            function='thin_plate'
        )
    
    def _apply_calibrated_mapping(
        self,
        norm_x: float,
        norm_y: float
    ) -> Tuple[float, float]:
        """Apply calibrated mapping to get screen coordinates"""
        if self.calibration_method == "polynomial":
            # Apply polynomial mapping
            features = np.array([
                1, norm_x, norm_y,
                norm_x**2, norm_x*norm_y, norm_y**2
            ])
            screen_x = np.dot(features, self._poly_coeffs_x)
            screen_y = np.dot(features, self._poly_coeffs_y)
        else:
            # Apply RBF mapping
            screen_x = self._map_x(norm_x, norm_y)
            screen_y = self._map_y(norm_x, norm_y)
        
        return screen_x, screen_y
    
    def _calculate_confidence(self, eye_result: EyeTrackingResult) -> float:
        """Calculate confidence score based on eye tracking quality"""
        confidence = 1.0
        
        # Reduce confidence if eyes are partially closed (possible blink)
        avg_ear = (eye_result.left_eye_aspect_ratio + eye_result.right_eye_aspect_ratio) / 2
        if avg_ear < 0.2:
            confidence *= 0.5
        elif avg_ear < 0.25:
            confidence *= 0.8
        
        # Check for extreme gaze positions (less reliable)
        if eye_result.gaze_direction is not None:
            gaze_magnitude = np.linalg.norm(eye_result.gaze_direction)
            if gaze_magnitude > 0.8:
                confidence *= 0.7
        
        return confidence
    
    def reset_calibration(self):
        """Clear calibration data"""
        self.calibration_points = []
        self.is_calibrated = False
        self._use_default_mapping = True
        self._map_x = None
        self._map_y = None
        self._poly_coeffs_x = None
        self._poly_coeffs_y = None
    
    def set_screen_size(self, width: int, height: int):
        """Update screen dimensions"""
        self.screen_width = width
        self.screen_height = height
    
    def get_calibration_points_grid(self, num_points: int = 9) -> List[Tuple[int, int]]:
        """
        Generate calibration point positions for the screen.
        
        Args:
            num_points: 5 or 9 point calibration
            
        Returns:
            List of (x, y) screen coordinates for calibration points
        """
        w = self.screen_width
        h = self.screen_height
        margin_x = w // 10
        margin_y = h // 10
        
        if num_points == 5:
            # Center and corners
            return [
                (w // 2, h // 2),  # Center
                (margin_x, margin_y),  # Top-left
                (w - margin_x, margin_y),  # Top-right
                (margin_x, h - margin_y),  # Bottom-left
                (w - margin_x, h - margin_y),  # Bottom-right
            ]
        else:
            # 9-point grid (3x3)
            points = []
            for row in range(3):
                for col in range(3):
                    x = margin_x + (col * (w - 2 * margin_x)) // 2
                    y = margin_y + (row * (h - 2 * margin_y)) // 2
                    points.append((x, y))
            return points
    
    def export_calibration(self) -> dict:
        """Export calibration data for saving"""
        return {
            "screen_width": self.screen_width,
            "screen_height": self.screen_height,
            "method": self.calibration_method,
            "is_calibrated": self.is_calibrated,
            "poly_coeffs_x": self._poly_coeffs_x.tolist() if self._poly_coeffs_x is not None else None,
            "poly_coeffs_y": self._poly_coeffs_y.tolist() if self._poly_coeffs_y is not None else None,
        }
    
    def import_calibration(self, data: dict) -> bool:
        """Import calibration data from saved profile"""
        try:
            self.screen_width = data["screen_width"]
            self.screen_height = data["screen_height"]
            self.calibration_method = data["method"]
            
            if data["is_calibrated"] and data["poly_coeffs_x"]:
                self._poly_coeffs_x = np.array(data["poly_coeffs_x"])
                self._poly_coeffs_y = np.array(data["poly_coeffs_y"])
                self.is_calibrated = True
                self._use_default_mapping = False
                return True
            
            return False
        except Exception as e:
            print(f"Failed to import calibration: {e}")
            return False
