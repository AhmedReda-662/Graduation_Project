"""
Eye Gaze Tracking System - Main Entry Point
Run this file to start the server or test locally.
"""
import argparse
import cv2
import time
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.pipeline import GazeTrackingPipeline
from src.config import config


def run_demo():
    """Run local demo using webcam"""
    print("=" * 50)
    print("Eye Gaze Tracking System - Local Demo")
    print("=" * 50)
    print("\nControls:")
    print("  'q' - Quit")
    print("  'c' - Start calibration")
    print("  'r' - Reset calibration")
    print("  's' - Toggle smoothing")
    print("=" * 50)
    
    # Initialize pipeline
    pipeline = GazeTrackingPipeline(
        screen_width=1920,
        screen_height=1080,
        enable_smoothing=True
    )
    
    # Open webcam
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Error: Could not open webcam")
        return
    
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    cap.set(cv2.CAP_PROP_FPS, 30)
    
    print("\nWebcam opened successfully. Starting tracking...")
    
    # Calibration state
    calibrating = False
    calibration_points = []
    current_cal_point = 0
    cal_samples = 0
    cal_samples_per_point = 30
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        # Flip horizontally for mirror effect
        frame = cv2.flip(frame, 1)
        
        timestamp = time.time() * 1000
        
        if calibrating and calibration_points:
            # Calibration mode
            cal_x, cal_y = calibration_points[current_cal_point]
            
            # Draw calibration point (scaled to frame)
            h, w = frame.shape[:2]
            point_x = int(cal_x * w / pipeline.screen_width)
            point_y = int(cal_y * h / pipeline.screen_height)
            
            cv2.circle(frame, (point_x, point_y), 20, (0, 255, 0), -1)
            cv2.circle(frame, (point_x, point_y), 25, (255, 255, 255), 2)
            
            # Add calibration sample
            success = pipeline.add_calibration_sample(frame, cal_x, cal_y)
            if success:
                cal_samples += 1
            
            # Progress text
            cv2.putText(
                frame, 
                f"Calibrating: Point {current_cal_point + 1}/{len(calibration_points)} | Sample {cal_samples}/{cal_samples_per_point}",
                (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2
            )
            
            # Move to next point
            if cal_samples >= cal_samples_per_point:
                cal_samples = 0
                current_cal_point += 1
                
                if current_cal_point >= len(calibration_points):
                    # Finish calibration
                    success = pipeline.finish_calibration()
                    print(f"\nCalibration {'completed!' if success else 'failed!'}")
                    calibrating = False
        else:
            # Normal tracking mode
            result = pipeline.process_frame(frame, timestamp)
            
            # Draw debug overlay
            frame = pipeline.draw_debug_overlay(frame, result)
            
            # Draw gaze point
            if result.gaze_point:
                # Scale to frame coordinates
                h, w = frame.shape[:2]
                gaze_x = int(result.gaze_point.x * w / pipeline.screen_width)
                gaze_y = int(result.gaze_point.y * h / pipeline.screen_height)
                
                cv2.circle(frame, (gaze_x, gaze_y), 15, (0, 0, 255), -1)
                cv2.circle(frame, (gaze_x, gaze_y), 17, (255, 255, 0), 2)
        
        # Display frame
        cv2.imshow("Eye Gaze Tracking", frame)
        
        # Handle key presses
        key = cv2.waitKey(1) & 0xFF
        
        if key == ord('q'):
            break
        elif key == ord('c') and not calibrating:
            # Start calibration
            print("\nStarting calibration...")
            calibration_points = pipeline.start_calibration(9)
            calibrating = True
            current_cal_point = 0
            cal_samples = 0
        elif key == ord('r'):
            # Reset calibration
            pipeline.gaze_estimator.reset_calibration()
            print("\nCalibration reset")
        elif key == ord('s'):
            # Toggle smoothing
            pipeline.enable_smoothing = not pipeline.enable_smoothing
            print(f"\nSmoothing: {'ON' if pipeline.enable_smoothing else 'OFF'}")
    
    # Cleanup
    cap.release()
    cv2.destroyAllWindows()
    pipeline.close()
    print("\nDemo ended.")


def run_server():
    """Run the WebSocket server"""
    from src.server import run_server as start_server
    print("Starting Eye Gaze Tracking Server...")
    start_server()


def main():
    parser = argparse.ArgumentParser(description="Eye Gaze Tracking System")
    parser.add_argument(
        "mode",
        choices=["demo", "server"],
        nargs="?",
        default="server",
        help="Run mode: 'demo' for local webcam demo, 'server' for WebSocket server"
    )
    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="Server host address"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Server port"
    )
    
    args = parser.parse_args()
    
    if args.mode == "demo":
        run_demo()
    else:
        config.server.host = args.host
        config.server.port = args.port
        run_server()


if __name__ == "__main__":
    main()
