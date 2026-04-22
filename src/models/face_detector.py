"""
Face Detector Module
Uses MediaPipe Face Mesh for robust face and landmark detection.
Supports both legacy solutions API and new Tasks API for Python 3.13+
"""
import cv2
import numpy as np
import mediapipe as mp
from typing import Optional, Tuple, List, NamedTuple
from dataclasses import dataclass
import os
import urllib.request


@dataclass
class FaceDetectionResult:
    """Container for face detection results"""
    success: bool
    face_landmarks: Optional[np.ndarray] = None
    face_bbox: Optional[Tuple[int, int, int, int]] = None  # x, y, w, h
    confidence: float = 0.0
    
    # Key landmark indices for eyes
    left_eye_landmarks: Optional[np.ndarray] = None
    right_eye_landmarks: Optional[np.ndarray] = None
    left_iris_landmarks: Optional[np.ndarray] = None
    right_iris_landmarks: Optional[np.ndarray] = None


class FaceDetector:
    """
    Real-time face detection using MediaPipe Face Mesh.
    Extracts facial landmarks including detailed eye regions.
    Automatically uses Tasks API for Python 3.13+ compatibility.
    """
    
    # MediaPipe Face Mesh landmark indices
    # Left eye contour
    LEFT_EYE_INDICES = [362, 382, 381, 380, 374, 373, 390, 249, 263, 466, 388, 387, 386, 385, 384, 398]
    # Right eye contour
    RIGHT_EYE_INDICES = [33, 7, 163, 144, 145, 153, 154, 155, 133, 173, 157, 158, 159, 160, 161, 246]
    # Left iris
    LEFT_IRIS_INDICES = [474, 475, 476, 477]
    # Right iris
    RIGHT_IRIS_INDICES = [469, 470, 471, 472]
    # Eye corners for gaze reference
    LEFT_EYE_INNER = 362
    LEFT_EYE_OUTER = 263
    RIGHT_EYE_INNER = 133
    RIGHT_EYE_OUTER = 33
    
    # Model URL for Tasks API
    MODEL_URL = "https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task"
    
    def __init__(
        self,
        max_faces: int = 1,
        min_detection_confidence: float = 0.5,
        min_tracking_confidence: float = 0.5,
        refine_landmarks: bool = True
    ):
        """
        Initialize the face detector.
        
        Args:
            max_faces: Maximum number of faces to detect
            min_detection_confidence: Minimum confidence for face detection
            min_tracking_confidence: Minimum confidence for landmark tracking
            refine_landmarks: Whether to refine iris landmarks (requires more compute)
        """
        self.max_faces = max_faces
        self.min_detection_confidence = min_detection_confidence
        self.min_tracking_confidence = min_tracking_confidence
        self.refine_landmarks = refine_landmarks
        self._use_tasks_api = not hasattr(mp, 'solutions')
        
        if self._use_tasks_api:
            self._init_tasks_api()
        else:
            self._init_solutions_api()
    
    def _init_solutions_api(self):
        """Initialize using legacy solutions API"""
        self.mp_face_mesh = mp.solutions.face_mesh
        self.face_mesh = self.mp_face_mesh.FaceMesh(
            max_num_faces=self.max_faces,
            refine_landmarks=self.refine_landmarks,
            min_detection_confidence=self.min_detection_confidence,
            min_tracking_confidence=self.min_tracking_confidence
        )
        self.mp_drawing = mp.solutions.drawing_utils
        self.mp_drawing_styles = mp.solutions.drawing_styles
    
    def _init_tasks_api(self):
        """Initialize using new Tasks API (Python 3.13+)"""
        from mediapipe.tasks import python
        from mediapipe.tasks.python import vision
        
        # Download model if not exists
        model_path = self._get_model_path()
        
        # Create face landmarker options
        base_options = python.BaseOptions(model_asset_path=model_path)
        options = vision.FaceLandmarkerOptions(
            base_options=base_options,
            running_mode=vision.RunningMode.IMAGE,
            num_faces=self.max_faces,
            min_face_detection_confidence=self.min_detection_confidence,
            min_face_presence_confidence=self.min_tracking_confidence,
            min_tracking_confidence=self.min_tracking_confidence,
            output_face_blendshapes=False,
            output_facial_transformation_matrixes=False
        )
        
        self.face_landmarker = vision.FaceLandmarker.create_from_options(options)
    
    def _get_model_path(self) -> str:
        """Download and return path to face landmarker model"""
        # Store in user's home directory
        model_dir = os.path.join(os.path.expanduser("~"), ".mediapipe", "models")
        os.makedirs(model_dir, exist_ok=True)
        model_path = os.path.join(model_dir, "face_landmarker.task")
        
        if not os.path.exists(model_path):
            print(f"Downloading MediaPipe face landmarker model...")
            urllib.request.urlretrieve(self.MODEL_URL, model_path)
            print(f"Model downloaded to {model_path}")
        
        return model_path
        
    def detect(self, frame: np.ndarray) -> FaceDetectionResult:
        """
        Detect face and extract landmarks from a frame.
        
        Args:
            frame: BGR image from camera
            
        Returns:
            FaceDetectionResult with landmarks and bounding box
        """
        if self._use_tasks_api:
            return self._detect_tasks_api(frame)
        else:
            return self._detect_solutions_api(frame)
    
    def _detect_solutions_api(self, frame: np.ndarray) -> FaceDetectionResult:
        """Detect using legacy solutions API"""
        # Convert BGR to RGB for MediaPipe
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        rgb_frame.flags.writeable = False
        
        # Process the frame
        results = self.face_mesh.process(rgb_frame)
        
        if not results.multi_face_landmarks:
            return FaceDetectionResult(success=False)
        
        # Get first face landmarks
        face_landmarks = results.multi_face_landmarks[0]
        h, w, _ = frame.shape
        
        # Convert landmarks to numpy array with pixel coordinates
        landmarks_np = np.array([
            [lm.x * w, lm.y * h, lm.z * w]
            for lm in face_landmarks.landmark
        ])
        
        return self._build_result(landmarks_np, frame.shape)
    
    def _detect_tasks_api(self, frame: np.ndarray) -> FaceDetectionResult:
        """Detect using new Tasks API (Python 3.13+)"""
        # Convert BGR to RGB for MediaPipe
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        
        # Create MediaPipe Image
        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb_frame)
        
        # Detect face landmarks
        result = self.face_landmarker.detect(mp_image)
        
        if not result.face_landmarks:
            return FaceDetectionResult(success=False)
        
        # Get first face landmarks
        face_landmarks = result.face_landmarks[0]
        h, w, _ = frame.shape
        
        # Convert landmarks to numpy array with pixel coordinates
        landmarks_np = np.array([
            [lm.x * w, lm.y * h, lm.z * w]
            for lm in face_landmarks
        ])
        
        return self._build_result(landmarks_np, frame.shape)
    
    def _build_result(self, landmarks_np: np.ndarray, frame_shape: tuple) -> FaceDetectionResult:
        """Build detection result from landmarks array"""
        # Calculate face bounding box
        x_coords = landmarks_np[:, 0]
        y_coords = landmarks_np[:, 1]
        bbox = (
            int(x_coords.min()),
            int(y_coords.min()),
            int(x_coords.max() - x_coords.min()),
            int(y_coords.max() - y_coords.min())
        )
        
        # Extract eye landmarks
        left_eye = landmarks_np[self.LEFT_EYE_INDICES]
        right_eye = landmarks_np[self.RIGHT_EYE_INDICES]
        
        # Extract iris landmarks - Tasks API has 478 landmarks (no iris refinement by default)
        # Check if we have enough landmarks for iris
        if len(landmarks_np) >= 478:
            left_iris = landmarks_np[self.LEFT_IRIS_INDICES]
            right_iris = landmarks_np[self.RIGHT_IRIS_INDICES]
        else:
            # Estimate iris position from eye center
            left_iris = np.array([left_eye.mean(axis=0)] * 4)
            right_iris = np.array([right_eye.mean(axis=0)] * 4)
        
        return FaceDetectionResult(
            success=True,
            face_landmarks=landmarks_np,
            face_bbox=bbox,
            confidence=1.0,  # MediaPipe doesn't expose confidence directly
            left_eye_landmarks=left_eye,
            right_eye_landmarks=right_eye,
            left_iris_landmarks=left_iris,
            right_iris_landmarks=right_iris
        )
    
    def draw_landmarks(
        self,
        frame: np.ndarray,
        result: FaceDetectionResult,
        draw_face: bool = True,
        draw_eyes: bool = True,
        draw_iris: bool = True
    ) -> np.ndarray:
        """
        Draw detected landmarks on frame for visualization.
        
        Args:
            frame: Input frame to draw on
            result: Detection result with landmarks
            draw_face: Whether to draw face mesh
            draw_eyes: Whether to draw eye contours
            draw_iris: Whether to draw iris points
            
        Returns:
            Frame with landmarks drawn
        """
        if not result.success:
            return frame
        
        output = frame.copy()
        
        if draw_eyes and result.left_eye_landmarks is not None:
            # Draw eye contours
            left_eye_pts = result.left_eye_landmarks[:, :2].astype(np.int32)
            right_eye_pts = result.right_eye_landmarks[:, :2].astype(np.int32)
            
            cv2.polylines(output, [left_eye_pts], True, (0, 255, 0), 1)
            cv2.polylines(output, [right_eye_pts], True, (0, 255, 0), 1)
        
        if draw_iris and result.left_iris_landmarks is not None:
            # Draw iris centers
            left_iris_center = result.left_iris_landmarks[:, :2].mean(axis=0).astype(int)
            right_iris_center = result.right_iris_landmarks[:, :2].mean(axis=0).astype(int)
            
            cv2.circle(output, tuple(left_iris_center), 3, (0, 0, 255), -1)
            cv2.circle(output, tuple(right_iris_center), 3, (0, 0, 255), -1)
        
        if draw_face and result.face_bbox is not None:
            x, y, w, h = result.face_bbox
            cv2.rectangle(output, (x, y), (x + w, y + h), (255, 0, 0), 2)
        
        return output
    
    def get_eye_centers(self, result: FaceDetectionResult) -> Tuple[Optional[np.ndarray], Optional[np.ndarray]]:
        """
        Get the center points of both eyes.
        
        Args:
            result: Face detection result
            
        Returns:
            Tuple of (left_eye_center, right_eye_center) as numpy arrays
        """
        if not result.success:
            return None, None
        
        left_center = result.left_eye_landmarks[:, :2].mean(axis=0)
        right_center = result.right_eye_landmarks[:, :2].mean(axis=0)
        
        return left_center, right_center
    
    def get_iris_centers(self, result: FaceDetectionResult) -> Tuple[Optional[np.ndarray], Optional[np.ndarray]]:
        """
        Get the center points of both irises.
        
        Args:
            result: Face detection result
            
        Returns:
            Tuple of (left_iris_center, right_iris_center) as numpy arrays
        """
        if not result.success or result.left_iris_landmarks is None:
            return None, None
        
        left_center = result.left_iris_landmarks[:, :2].mean(axis=0)
        right_center = result.right_iris_landmarks[:, :2].mean(axis=0)
        
        return left_center, right_center
    
    def close(self):
        """Release resources"""
        if self._use_tasks_api:
            if hasattr(self, 'face_landmarker'):
                self.face_landmarker.close()
        else:
            if hasattr(self, 'face_mesh'):
                self.face_mesh.close()
