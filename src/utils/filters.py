"""
Kalman Filter for Gaze Smoothing
Provides temporal smoothing for stable gaze points.
"""
import numpy as np
from typing import Tuple, Optional


class KalmanFilter2D:
    """
    2D Kalman filter for smoothing gaze coordinates.
    Tracks position and velocity for both x and y.
    """
    
    def __init__(
        self,
        process_noise: float = 0.01,
        measurement_noise: float = 0.1,
        initial_x: float = 0.0,
        initial_y: float = 0.0
    ):
        """
        Initialize 2D Kalman filter.
        
        Args:
            process_noise: Process noise variance (higher = more responsive)
            measurement_noise: Measurement noise variance (higher = more smoothing)
            initial_x: Initial x position
            initial_y: Initial y position
        """
        # State: [x, y, vx, vy] (position and velocity)
        self.state = np.array([initial_x, initial_y, 0.0, 0.0])
        
        # State covariance matrix
        self.P = np.eye(4) * 1000  # High initial uncertainty
        
        # State transition matrix (assumes constant velocity)
        self.F = np.array([
            [1, 0, 1, 0],  # x = x + vx
            [0, 1, 0, 1],  # y = y + vy
            [0, 0, 1, 0],  # vx = vx
            [0, 0, 0, 1]   # vy = vy
        ], dtype=float)
        
        # Measurement matrix (we only measure position)
        self.H = np.array([
            [1, 0, 0, 0],
            [0, 1, 0, 0]
        ], dtype=float)
        
        # Process noise covariance
        self.Q = np.eye(4) * process_noise
        self.Q[2, 2] *= 2  # Higher noise for velocity
        self.Q[3, 3] *= 2
        
        # Measurement noise covariance
        self.R = np.eye(2) * measurement_noise
        
        self.initialized = False
        
    def predict(self) -> Tuple[float, float]:
        """
        Predict next state.
        
        Returns:
            Predicted (x, y) position
        """
        # Predict state
        self.state = self.F @ self.state
        
        # Predict covariance
        self.P = self.F @ self.P @ self.F.T + self.Q
        
        return self.state[0], self.state[1]
    
    def update(self, x: float, y: float) -> Tuple[float, float]:
        """
        Update filter with new measurement.
        
        Args:
            x: Measured x position
            y: Measured y position
            
        Returns:
            Filtered (x, y) position
        """
        if not self.initialized:
            self.state[0] = x
            self.state[1] = y
            self.initialized = True
            return x, y
        
        # Measurement vector
        z = np.array([x, y])
        
        # Prediction step
        self.predict()
        
        # Innovation (measurement residual)
        y_residual = z - self.H @ self.state
        
        # Innovation covariance
        S = self.H @ self.P @ self.H.T + self.R
        
        # Kalman gain
        K = self.P @ self.H.T @ np.linalg.inv(S)
        
        # Update state
        self.state = self.state + K @ y_residual
        
        # Update covariance
        I = np.eye(4)
        self.P = (I - K @ self.H) @ self.P
        
        return self.state[0], self.state[1]
    
    def get_velocity(self) -> Tuple[float, float]:
        """Get estimated velocity"""
        return self.state[2], self.state[3]
    
    def reset(self, x: float = 0.0, y: float = 0.0):
        """Reset filter state"""
        self.state = np.array([x, y, 0.0, 0.0])
        self.P = np.eye(4) * 1000
        self.initialized = False
    
    def set_noise_parameters(
        self,
        process_noise: Optional[float] = None,
        measurement_noise: Optional[float] = None
    ):
        """Adjust noise parameters for different smoothing behavior"""
        if process_noise is not None:
            self.Q = np.eye(4) * process_noise
            self.Q[2, 2] *= 2
            self.Q[3, 3] *= 2
        
        if measurement_noise is not None:
            self.R = np.eye(2) * measurement_noise


class OneEuroFilter:
    """
    1€ Filter for adaptive low-pass filtering.
    Better for gaze smoothing as it adapts to movement speed.
    """
    
    def __init__(
        self,
        min_cutoff: float = 1.0,
        beta: float = 0.007,
        d_cutoff: float = 1.0
    ):
        """
        Initialize 1€ filter.
        
        Args:
            min_cutoff: Minimum cutoff frequency (lower = more smoothing)
            beta: Speed coefficient (higher = more responsive to fast movement)
            d_cutoff: Derivative cutoff frequency
        """
        self.min_cutoff = min_cutoff
        self.beta = beta
        self.d_cutoff = d_cutoff
        
        self.x_prev = None
        self.y_prev = None
        self.dx_prev = 0.0
        self.dy_prev = 0.0
        self.t_prev = None
        
    def _smoothing_factor(self, cutoff: float, dt: float) -> float:
        """Calculate exponential smoothing factor"""
        tau = 1.0 / (2 * np.pi * cutoff)
        return 1.0 / (1.0 + tau / dt)
    
    def _exponential_smoothing(
        self,
        current: float,
        previous: float,
        alpha: float
    ) -> float:
        """Apply exponential smoothing"""
        return alpha * current + (1 - alpha) * previous
    
    def update(
        self,
        x: float,
        y: float,
        timestamp: float
    ) -> Tuple[float, float]:
        """
        Update filter with new measurement.
        
        Args:
            x: Measured x position
            y: Measured y position
            timestamp: Current timestamp in seconds
            
        Returns:
            Filtered (x, y) position
        """
        if self.t_prev is None:
            self.x_prev = x
            self.y_prev = y
            self.t_prev = timestamp
            return x, y
        
        # Calculate time delta
        dt = timestamp - self.t_prev
        if dt <= 0:
            dt = 1e-6
        
        # Calculate derivative
        dx = (x - self.x_prev) / dt
        dy = (y - self.y_prev) / dt
        
        # Smooth derivative
        alpha_d = self._smoothing_factor(self.d_cutoff, dt)
        dx_hat = self._exponential_smoothing(dx, self.dx_prev, alpha_d)
        dy_hat = self._exponential_smoothing(dy, self.dy_prev, alpha_d)
        
        # Calculate adaptive cutoff
        speed = np.sqrt(dx_hat**2 + dy_hat**2)
        cutoff = self.min_cutoff + self.beta * speed
        
        # Smooth position
        alpha = self._smoothing_factor(cutoff, dt)
        x_hat = self._exponential_smoothing(x, self.x_prev, alpha)
        y_hat = self._exponential_smoothing(y, self.y_prev, alpha)
        
        # Update state
        self.x_prev = x_hat
        self.y_prev = y_hat
        self.dx_prev = dx_hat
        self.dy_prev = dy_hat
        self.t_prev = timestamp
        
        return x_hat, y_hat
    
    def reset(self):
        """Reset filter state"""
        self.x_prev = None
        self.y_prev = None
        self.dx_prev = 0.0
        self.dy_prev = 0.0
        self.t_prev = None


class GazeSmoother:
    """
    High-level gaze smoothing that combines multiple techniques.
    """
    
    def __init__(
        self,
        method: str = "one_euro",
        **kwargs
    ):
        """
        Initialize gaze smoother.
        
        Args:
            method: "kalman" or "one_euro"
            **kwargs: Parameters for the chosen filter
        """
        self.method = method
        
        if method == "kalman":
            self.filter = KalmanFilter2D(
                process_noise=kwargs.get("process_noise", 0.01),
                measurement_noise=kwargs.get("measurement_noise", 0.1)
            )
        else:
            self.filter = OneEuroFilter(
                min_cutoff=kwargs.get("min_cutoff", 1.0),
                beta=kwargs.get("beta", 0.007)
            )
        
        self.last_timestamp = 0
        
    def smooth(
        self,
        x: float,
        y: float,
        timestamp: Optional[float] = None
    ) -> Tuple[float, float]:
        """
        Apply smoothing to gaze point.
        
        Args:
            x: Raw x coordinate
            y: Raw y coordinate
            timestamp: Optional timestamp (seconds for 1€, ignored for Kalman)
            
        Returns:
            Smoothed (x, y) coordinates
        """
        if self.method == "kalman":
            return self.filter.update(x, y)
        else:
            if timestamp is None:
                timestamp = self.last_timestamp + 0.033  # Assume 30 FPS
            self.last_timestamp = timestamp
            return self.filter.update(x, y, timestamp)
    
    def reset(self):
        """Reset smoother state"""
        self.filter.reset()
        self.last_timestamp = 0
