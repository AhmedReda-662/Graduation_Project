"""
Eye Gaze Tracking System - Model Accuracy Test
Tests face detection, eye tracking, gaze estimation, and blink detection
using a live webcam feed with visual metrics and quantitative results.
"""
import cv2
import numpy as np
import time
import sys
import os
from collections import deque
from dataclasses import dataclass, field
from typing import List, Tuple

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.models.face_detector import FaceDetector
from src.models.eye_tracker import EyeTracker
from src.models.gaze_estimator import GazeEstimator
from src.models.blink_detector import BlinkDetector
from src.pipeline import GazeTrackingPipeline


# ── Metrics Tracking ──────────────────────────────────────────────────────────

@dataclass
class AccuracyMetrics:
    """Tracks accuracy metrics across frames"""
    total_frames: int = 0
    face_detected_frames: int = 0
    eyes_detected_frames: int = 0
    gaze_estimated_frames: int = 0
    blinks_detected: int = 0

    # Timing
    face_detect_times: List[float] = field(default_factory=list)
    eye_track_times: List[float] = field(default_factory=list)
    gaze_estimate_times: List[float] = field(default_factory=list)
    pipeline_times: List[float] = field(default_factory=list)

    # Stability (gaze jitter measurement)
    gaze_positions: List[Tuple[float, float]] = field(default_factory=list)

    # Confidence scores
    gaze_confidences: List[float] = field(default_factory=list)

    # Eye aspect ratios
    left_ears: List[float] = field(default_factory=list)
    right_ears: List[float] = field(default_factory=list)

    @property
    def face_detection_rate(self) -> float:
        return (self.face_detected_frames / max(1, self.total_frames)) * 100

    @property
    def eye_detection_rate(self) -> float:
        return (self.eyes_detected_frames / max(1, self.total_frames)) * 100

    @property
    def gaze_estimation_rate(self) -> float:
        return (self.gaze_estimated_frames / max(1, self.total_frames)) * 100

    @property
    def avg_face_detect_ms(self) -> float:
        return np.mean(self.face_detect_times) if self.face_detect_times else 0

    @property
    def avg_eye_track_ms(self) -> float:
        return np.mean(self.eye_track_times) if self.eye_track_times else 0

    @property
    def avg_gaze_estimate_ms(self) -> float:
        return np.mean(self.gaze_estimate_times) if self.gaze_estimate_times else 0

    @property
    def avg_pipeline_ms(self) -> float:
        return np.mean(self.pipeline_times) if self.pipeline_times else 0

    @property
    def avg_confidence(self) -> float:
        return np.mean(self.gaze_confidences) if self.gaze_confidences else 0

    @property
    def gaze_stability(self) -> float:
        """Lower is better. Measures standard deviation of gaze position (jitter)."""
        if len(self.gaze_positions) < 10:
            return 0
        recent = self.gaze_positions[-60:]  # Last ~2 seconds at 30fps
        xs = [p[0] for p in recent]
        ys = [p[1] for p in recent]
        return float(np.sqrt(np.std(xs)**2 + np.std(ys)**2))


# ── Target Test ───────────────────────────────────────────────────────────────

class GazeTargetTest:
    """
    Displays targets on screen and measures how closely the gaze tracks them.
    Tests gaze accuracy by showing dots the user should look at.
    """

    def __init__(self, frame_w: int, frame_h: int):
        self.frame_w = frame_w
        self.frame_h = frame_h
        self.targets = self._generate_targets()
        self.current_target_idx = 0
        self.target_start_time = 0
        self.dwell_time_ms = 3000  # 3s per target
        self.collecting = False
        self.samples: List[Tuple[float, float]] = []
        self.results: List[dict] = []
        self.active = False

    def _generate_targets(self) -> List[Tuple[int, int]]:
        """Generate 5 target positions (center + 4 quadrants)"""
        cx, cy = self.frame_w // 2, self.frame_h // 2
        mx, my = self.frame_w // 5, self.frame_h // 5
        return [
            (cx, cy),                         # Center
            (mx, my),                         # Top-left
            (self.frame_w - mx, my),          # Top-right
            (mx, self.frame_h - my),          # Bottom-left
            (self.frame_w - mx, self.frame_h - my),  # Bottom-right
        ]

    def start(self):
        self.active = True
        self.current_target_idx = 0
        self.target_start_time = time.time() * 1000
        self.collecting = True
        self.samples = []
        self.results = []

    def update(self, gaze_x: float, gaze_y: float, timestamp_ms: float) -> bool:
        """Update with gaze position. Returns False when test is complete."""
        if not self.active:
            return True

        # Collect sample
        if self.collecting:
            self.samples.append((gaze_x, gaze_y))

        # Check if dwell time elapsed
        elapsed = timestamp_ms - self.target_start_time
        if elapsed >= self.dwell_time_ms:
            # Save results for this target
            target = self.targets[self.current_target_idx]
            if self.samples:
                avg_x = np.mean([s[0] for s in self.samples])
                avg_y = np.mean([s[1] for s in self.samples])
                error = np.sqrt((avg_x - target[0])**2 + (avg_y - target[1])**2)
                spread = np.sqrt(
                    np.std([s[0] for s in self.samples])**2 +
                    np.std([s[1] for s in self.samples])**2
                )
                self.results.append({
                    "target": target,
                    "avg_gaze": (avg_x, avg_y),
                    "error_px": error,
                    "spread_px": spread,
                    "num_samples": len(self.samples),
                })

            # Next target
            self.current_target_idx += 1
            self.samples = []
            self.target_start_time = timestamp_ms

            if self.current_target_idx >= len(self.targets):
                self.active = False
                return False

        return True

    def draw(self, frame: np.ndarray, timestamp_ms: float) -> np.ndarray:
        """Draw current target and progress"""
        if not self.active:
            return frame

        target = self.targets[self.current_target_idx]
        elapsed = timestamp_ms - self.target_start_time
        progress = min(1.0, elapsed / self.dwell_time_ms)

        # Draw target circle
        cv2.circle(frame, target, 25, (0, 255, 0), 2)
        cv2.circle(frame, target, int(25 * (1 - progress)), (0, 255, 0), -1)
        cv2.circle(frame, target, 5, (255, 255, 255), -1)

        # Draw instruction
        cv2.putText(
            frame,
            f"Look at the GREEN DOT  [{self.current_target_idx + 1}/{len(self.targets)}]",
            (10, frame.shape[0] - 20),
            cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2,
        )
        return frame

    def get_summary(self) -> dict:
        if not self.results:
            return {}
        errors = [r["error_px"] for r in self.results]
        spreads = [r["spread_px"] for r in self.results]
        return {
            "avg_error_px": np.mean(errors),
            "max_error_px": np.max(errors),
            "avg_spread_px": np.mean(spreads),
            "per_target": self.results,
        }


# ── Main Test Runner ──────────────────────────────────────────────────────────

def draw_metrics_panel(frame: np.ndarray, metrics: AccuracyMetrics, fps: float) -> np.ndarray:
    """Draw a translucent panel with live metrics on the frame"""
    h, w = frame.shape[:2]
    panel_w = 340
    overlay = frame.copy()
    cv2.rectangle(overlay, (w - panel_w, 0), (w, 280), (0, 0, 0), -1)
    cv2.addWeighted(overlay, 0.7, frame, 0.3, 0, frame)

    x0 = w - panel_w + 10
    y = 22
    gap = 22
    color_title = (0, 200, 255)
    color_val = (255, 255, 255)
    color_good = (0, 255, 0)
    color_warn = (0, 200, 255)
    color_bad = (0, 0, 255)

    def rate_color(rate: float):
        if rate >= 90:
            return color_good
        elif rate >= 70:
            return color_warn
        return color_bad

    cv2.putText(frame, "=== Accuracy Metrics ===", (x0, y), cv2.FONT_HERSHEY_SIMPLEX, 0.55, color_title, 1)
    y += gap + 4

    lines = [
        (f"Frames: {metrics.total_frames}", color_val),
        (f"FPS: {fps:.1f}", color_val),
        (f"Face Detection:  {metrics.face_detection_rate:.1f}%", rate_color(metrics.face_detection_rate)),
        (f"Eye  Detection:  {metrics.eye_detection_rate:.1f}%", rate_color(metrics.eye_detection_rate)),
        (f"Gaze Estimation: {metrics.gaze_estimation_rate:.1f}%", rate_color(metrics.gaze_estimation_rate)),
        (f"Avg Confidence:  {metrics.avg_confidence:.2f}", color_val),
        (f"Gaze Jitter:     {metrics.gaze_stability:.1f}px", color_val),
        (f"Blinks Detected: {metrics.blinks_detected}", color_val),
        (f"Avg Pipeline:    {metrics.avg_pipeline_ms:.1f}ms", color_val),
    ]

    for text, col in lines:
        cv2.putText(frame, text, (x0, y), cv2.FONT_HERSHEY_SIMPLEX, 0.48, col, 1)
        y += gap

    return frame


def print_final_report(metrics: AccuracyMetrics, target_summary: dict, elapsed_s: float):
    """Print comprehensive final report to console"""
    print("\n" + "=" * 60)
    print("        EYE GAZE TRACKING - ACCURACY TEST REPORT")
    print("=" * 60)
    print(f"\n  Test Duration:        {elapsed_s:.1f} seconds")
    print(f"  Total Frames:         {metrics.total_frames}")
    print(f"  Avg FPS:              {metrics.total_frames / max(0.1, elapsed_s):.1f}")

    print("\n--- Detection Rates ---")
    print(f"  Face Detection:       {metrics.face_detection_rate:.1f}%")
    print(f"  Eye  Detection:       {metrics.eye_detection_rate:.1f}%")
    print(f"  Gaze Estimation:      {metrics.gaze_estimation_rate:.1f}%")

    print("\n--- Performance (per frame) ---")
    print(f"  Face Detection:       {metrics.avg_face_detect_ms:.2f} ms")
    print(f"  Eye Tracking:         {metrics.avg_eye_track_ms:.2f} ms")
    print(f"  Gaze Estimation:      {metrics.avg_gaze_estimate_ms:.2f} ms")
    print(f"  Full Pipeline:        {metrics.avg_pipeline_ms:.2f} ms")

    print("\n--- Gaze Quality ---")
    print(f"  Avg Confidence:       {metrics.avg_confidence:.3f}")
    print(f"  Gaze Stability (σ):   {metrics.gaze_stability:.1f} px  (lower = smoother)")
    print(f"  Blinks Detected:      {metrics.blinks_detected}")

    if metrics.left_ears:
        print(f"  Avg Left  EAR:        {np.mean(metrics.left_ears):.3f}")
        print(f"  Avg Right EAR:        {np.mean(metrics.right_ears):.3f}")

    if target_summary:
        print("\n--- Gaze Target Accuracy ---")
        print(f"  Avg Error:            {target_summary['avg_error_px']:.1f} px")
        print(f"  Max Error:            {target_summary['max_error_px']:.1f} px")
        print(f"  Avg Spread (σ):       {target_summary['avg_spread_px']:.1f} px")
        for i, t in enumerate(target_summary["per_target"]):
            print(f"    Target {i+1} ({t['target'][0]:4d},{t['target'][1]:4d}):  "
                  f"error={t['error_px']:.1f}px  spread={t['spread_px']:.1f}px  "
                  f"samples={t['num_samples']}")

    print("\n" + "=" * 60)

    # Overall verdict
    score = 0
    if metrics.face_detection_rate >= 90:
        score += 1
    if metrics.eye_detection_rate >= 85:
        score += 1
    if metrics.gaze_estimation_rate >= 80:
        score += 1
    if metrics.avg_confidence >= 0.6:
        score += 1
    if metrics.avg_pipeline_ms < 50:
        score += 1

    verdicts = {5: "EXCELLENT", 4: "GOOD", 3: "FAIR", 2: "NEEDS IMPROVEMENT", 1: "POOR", 0: "POOR"}
    print(f"\n  Overall Rating: {verdicts.get(score, 'N/A')}  ({score}/5 criteria met)")
    print("=" * 60 + "\n")


def run_accuracy_test():
    """Main accuracy test loop"""
    print("=" * 60)
    print("  Eye Gaze Tracking - Model Accuracy Test")
    print("=" * 60)
    print("\nControls:")
    print("  'q'  - Quit and show final report")
    print("  't'  - Start gaze target accuracy test")
    print("  'r'  - Reset metrics")
    print("=" * 60)

    # Initialize pipeline
    pipeline = GazeTrackingPipeline(
        screen_width=1920,
        screen_height=1080,
        enable_smoothing=True,
    )

    # Open webcam
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Error: Could not open webcam")
        return

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    cap.set(cv2.CAP_PROP_FPS, 30)

    print("\nWebcam opened. Running accuracy test...\n")

    metrics = AccuracyMetrics()
    frame_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    frame_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    target_test = GazeTargetTest(frame_w, frame_h)

    fps_counter = deque(maxlen=60)
    test_start = time.time()

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        frame = cv2.flip(frame, 1)
        timestamp = time.time() * 1000
        metrics.total_frames += 1

        # ── Step-by-step timing ───────────────────────────────────
        # Face detection
        t0 = time.time()
        face_result = pipeline.face_detector.detect(frame)
        face_ms = (time.time() - t0) * 1000
        metrics.face_detect_times.append(face_ms)

        if face_result.success:
            metrics.face_detected_frames += 1

            # Eye tracking
            t0 = time.time()
            eye_result = pipeline.eye_tracker.track(face_result)
            eye_ms = (time.time() - t0) * 1000
            metrics.eye_track_times.append(eye_ms)

            if eye_result.success:
                metrics.eyes_detected_frames += 1
                metrics.left_ears.append(eye_result.left_eye_aspect_ratio)
                metrics.right_ears.append(eye_result.right_eye_aspect_ratio)

                # Gaze estimation
                t0 = time.time()
                gaze_point = pipeline.gaze_estimator.estimate(eye_result, timestamp)
                gaze_ms = (time.time() - t0) * 1000
                metrics.gaze_estimate_times.append(gaze_ms)

                if gaze_point:
                    metrics.gaze_estimated_frames += 1
                    metrics.gaze_confidences.append(gaze_point.confidence)

                    # Scale gaze to frame coords for visualization
                    scale_x = frame_w / pipeline.screen_width
                    scale_y = frame_h / pipeline.screen_height
                    gaze_fx = gaze_point.x * scale_x
                    gaze_fy = gaze_point.y * scale_y
                    metrics.gaze_positions.append((gaze_fx, gaze_fy))

                    # Draw gaze crosshair
                    gx, gy = int(gaze_fx), int(gaze_fy)
                    cv2.circle(frame, (gx, gy), 12, (0, 0, 255), -1)
                    cv2.circle(frame, (gx, gy), 14, (255, 255, 0), 2)
                    cv2.line(frame, (gx - 20, gy), (gx + 20, gy), (255, 255, 0), 1)
                    cv2.line(frame, (gx, gy - 20), (gx, gy + 20), (255, 255, 0), 1)

                    # Target test
                    if target_test.active:
                        still_running = target_test.update(gaze_fx, gaze_fy, timestamp)
                        if not still_running:
                            print("\nTarget test complete!")

                # Blink detection
                blink = pipeline.blink_detector.update(eye_result, timestamp)
                if blink:
                    metrics.blinks_detected += 1
                    cv2.putText(frame, "BLINK!", (frame_w // 2 - 50, 40),
                                cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 255), 2)

        # Full pipeline timing
        metrics.pipeline_times.append(face_ms +
            (eye_ms if face_result.success else 0) +
            (gaze_ms if face_result.success and eye_result.success else 0))

        # Draw landmarks
        if face_result.success:
            frame = pipeline.face_detector.draw_landmarks(
                frame, face_result, draw_face=True, draw_eyes=True, draw_iris=True)

        # Draw target test overlay
        if target_test.active:
            frame = target_test.draw(frame, timestamp)

        # FPS
        fps_counter.append(time.time())
        if len(fps_counter) > 1:
            fps = (len(fps_counter) - 1) / (fps_counter[-1] - fps_counter[0])
        else:
            fps = 0

        # Draw metrics panel
        frame = draw_metrics_panel(frame, metrics, fps)

        # Show
        cv2.imshow("Accuracy Test", frame)

        key = cv2.waitKey(1) & 0xFF
        if key == ord('q'):
            break
        elif key == ord('t') and not target_test.active:
            print("\nStarting gaze target test — look at each green dot!")
            target_test.start()
        elif key == ord('r'):
            metrics = AccuracyMetrics()
            print("\nMetrics reset.")

    # Cleanup
    cap.release()
    cv2.destroyAllWindows()
    pipeline.close()

    # Final report
    elapsed = time.time() - test_start
    print_final_report(metrics, target_test.get_summary(), elapsed)


if __name__ == "__main__":
    run_accuracy_test()
