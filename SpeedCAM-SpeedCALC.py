#!/usr/bin/env python3
import cv2
import time
import json
import numpy as np
import os
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
from multiprocessing import Process, Value, Lock, Array
from picamera2 import Picamera2
from libcamera import Transform


class SpeedCameraSystem:
    def __init__(self):
        self.config = self._load_config()
        self.running = Value('b', True)
        self.current_speed = Value('d', 0.0)
        self.lock = Lock()
        self.prev_frame = None
        self.last_detection_time = None
        self.last_speed = 0.0
        
        # Calibration data (2022.5 px/m at 0.6096 m / 2 ft)
        self.calibration_distance = 0.6096  # 2 ft in meters
        self.calibration_px_per_m = 2022.5  # Your measured px/m at 2 ft
        self.px_per_meter = self.calibration_px_per_m  # Initialize with baseline
        
        # Real-world car dimensions (avg width: ~1.8m, height: ~1.5m)
        self.car_width_m = 1.8
        self.car_height_m = 1.5
        
        self.detection_zone = [0, 0, self.config['frame_width'], self.config['frame_height']]
        self.overlay = SpeedOverlay()
        
        # Detection parameters
        self.min_contour_area = 1200
        self.max_contour_area = 8000
        self.bg_subtractor = cv2.createBackgroundSubtractorMOG2(
            history=300,
            varThreshold=24,
            detectShadows=False
        )
        
        # UI Settings
        self.speed_limit = 35.0
        self.warn_thresh = 5.0
        self.danger_thresh = 10.0
        
        # Display settings
        self.window_name = "Speed Camera System"
        self.border_color = (0, 255, 0)
        self.border_thickness = int(min(self.config['frame_width'], self.config['frame_height']) * 0.02)

    def _load_config(self):
        try:
            with open('config.json') as f:
                return json.load(f)
        except FileNotFoundError:
            return {
                "px_per_meter": 85,
                "frame_width": 1280,
                "frame_height": 720,
                "speed_limit_mph": 35.0,
                "calibration_factor": 1.0,
                "distance_compensation": 1.18,
                "min_speed_threshold": 10.0
            }

    def _estimate_distance(self, pixel_width):
        """
        Estimates distance to object using pixel width and known real-world size.
        Returns distance in meters.
        """
        if pixel_width == 0:
            return float('inf')
        # Inverse scaling: distance = (calib_distance * calib_px_per_m) / observed_px_per_m
        observed_px_per_m = pixel_width / self.car_width_m
        distance_m = (self.calibration_distance * self.calibration_px_per_m) / observed_px_per_m
        return distance_m

    def _process_frame(self, frame, frame_time):
        # Exact same tracking as your reference program
        x1, y1, x2, y2 = self.detection_zone
        roi = frame[y1:y2, x1:x2]
        
        # Background subtraction
        fg_mask = self.bg_subtractor.apply(roi)
        fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_OPEN, np.ones((3,3), np.uint8))
        
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (15, 15), 0)
        
        if self.prev_frame is None:
            self.prev_frame = gray
            return None
            
        # Motion detection
        frame_diff = cv2.absdiff(self.prev_frame, gray)
        frame_diff = cv2.bitwise_and(frame_diff, frame_diff, mask=fg_mask)
        
        _, thresh = cv2.threshold(frame_diff, 30, 255, cv2.THRESH_BINARY)
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        valid_contours = [
            c for c in contours 
            if self.min_contour_area < cv2.contourArea(c) < self.max_contour_area
        ]
        
        if valid_contours:
            contour = max(valid_contours, key=cv2.contourArea)
            x, y, w, h = cv2.boundingRect(contour)
            
            # Estimate distance and adjust px_per_meter dynamically
            distance = self._estimate_distance(w)
            if distance < 50:  # Ignore unrealistic distances
                self.px_per_meter = self.calibration_px_per_m * (self.calibration_distance / distance)
            
            if self.last_detection_time is not None:
                speed_mph = self._calculate_speed(y, y+h, frame_time)
                if speed_mph > self.config.get('min_speed_threshold', 10.0):
                    self.last_detection_time = time.time()
                    return {
                        'speed_mph': speed_mph * self.config['calibration_factor'],
                        'speed_kmh': speed_mph * 1.60934,
                        'bounding_box': (x1+x, y1+y, w, h),
                        'speed_limit': self.speed_limit
                    }
            self.last_detection_time = time.time()
        
        self.prev_frame = gray
        return None

    def _calculate_speed(self, entry_y, exit_y, frame_time):
        # Same calculation as your reference
        pixels = abs(exit_y - entry_y)
        meters = pixels / self.px_per_meter  # Now uses distance-adjusted px_per_meter
        speed_mph = (meters / frame_time) * 2.23694  # Convert m/s to mph
        
        # Smoothing filter
        if hasattr(self, 'last_speed'):
            speed_mph = 0.7 * speed_mph + 0.3 * self.last_speed
        self.last_speed = speed_mph
        
        return speed_mph

    def _update_display(self, frame, speed_data):
        # Same display logic with added UI thresholds
        cv2.rectangle(frame, 
                     (0, 0), 
                     (frame.shape[1]-1, frame.shape[0]-1),
                     self.border_color, 
                     self.border_thickness)
        
        if speed_data and 'bounding_box' in speed_data:
            x, y, w, h = speed_data['bounding_box']
            cv2.rectangle(frame, (x,y), (x+w,y+h), (0,0,255), 2)
        
        frame = self.overlay.draw_overlay(frame, speed_data, self.warn_thresh, self.danger_thresh)
        return frame

    def process_video_file(self, video_path):
        cap = cv2.VideoCapture(video_path)
        prev_time = time.time()
        
        cv2.namedWindow(self.window_name, cv2.WND_PROP_FULLSCREEN)
        cv2.setWindowProperty(self.window_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
        
        while cap.isOpened() and self.running.value:
            ret, frame = cap.read()
            if not ret:
                break
            
            current_time = time.time()
            frame_time = current_time - prev_time
            prev_time = current_time
            
            speed_data = self._process_frame(frame, frame_time)
            display_frame = self._update_display(frame, speed_data)
            
            cv2.imshow(self.window_name, display_frame)
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        
        cap.release()
        cv2.destroyAllWindows()

    def run_live_camera(self):
        self.picam2 = Picamera2()
        config = self.picam2.create_preview_configuration(
            main={"size": (self.config['frame_width'], self.config['frame_height'])},
            transform=Transform(vflip=True),
            controls={"FrameDurationLimits": (33333, 33333)}
        )
        self.picam2.configure(config)
        self.picam2.start()
        time.sleep(2)
        prev_time = time.time()
        
        cv2.namedWindow(self.window_name, cv2.WND_PROP_FULLSCREEN)
        cv2.setWindowProperty(self.window_name, cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)
        
        try:
            while self.running.value:
                current_time = time.time()
                frame_time = current_time - prev_time
                prev_time = current_time
                
                frame = self.picam2.capture_array()
                frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                speed_data = self._process_frame(frame_bgr, frame_time)
                display_frame = self._update_display(frame_bgr, speed_data)
                
                cv2.imshow(self.window_name, display_frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    self.running.value = False
                    
        finally:
            self.picam2.stop()
            cv2.destroyAllWindows()

    def show_config_ui(self):
        root = tk.Tk()
        ui = SpeedCameraUI(root)
        root.mainloop()
        
        if hasattr(root, 'speed_limit'):
            self.speed_limit = root.speed_limit
            self.warn_thresh = root.warn_thresh
            self.danger_thresh = root.danger_thresh

if __name__ == "__main__":
    system = SpeedCameraSystem()
    
    print("Select mode:")
    print("1. Live Camera Detection")
    print("2. Process Video Files from Videos directory")
    choice = input("Enter choice (1 or 2): ")
    
    system.show_config_ui()
    
    if choice == "1":
        system.run_live_camera()
    elif choice == "2":
        video_dir = "Videos"
        if not os.path.exists(video_dir):
            print(f"Error: Directory '{video_dir}' not found!")
            exit()
            
        video_files = [f for f in os.listdir(video_dir) if f.endswith('.mp4')]
        if not video_files:
            print(f"No .mp4 files found in '{video_dir}'")
            exit()
            
        print(f"Found {len(video_files)} video files:")
        for i, f in enumerate(video_files, 1):
            print(f"{i}. {f}")
            
        vid_choice = int(input("Select video file (number): ")) - 1
        selected_video = os.path.join(video_dir, video_files[vid_choice])
        system.process_video_file(selected_video)
    else:
        print("Invalid choice!")