import cv2
import numpy as np
from datetime import datetime
from multiprocessing import Process, Value, Array
import time
import picamera
from picamera.array import PiRGBArray


class SpeedOverlay:
    def __init__(self):
        # Shared memory for inter-process communication
        self.shared_speed = Value('d', 0.0)  # Double precision float
        self.shared_data = Array('d', [0.0, 0.0, 0.0])  # [speed, confidence, direction]

        # cam configuration
        self.camera_config = {
            'resolution': (640, 480),
            'framerate': 30,
            'rotation': 180,  # Adjust if camera is mounted upside down
            'sensor_mode': 2  # Optimized for 640x480
        }

        # overlay settings
        self.overlay_settings = {
            'bg_color': (0, 0, 0),
            'bg_alpha': 0.6,
            'normal_color': (0, 255, 0),
            'warning_color': (0, 255, 255),
            'danger_color': (0, 0, 255),
            'font_scale': 0.8,
            'thickness': 2
        }

    def get_speed_color(self, speed):
        """Determine text color based on speed thresholds"""
        if speed >= 42:
            return self.overlay_settings['danger_color']  # red
        elif 35 <= speed < 42:
            return self.overlay_settings['warning_color']  # yellow
        return self.overlay_settings['normal_color']  # green

    def draw_overlay(self, frame, timestamp):
        """Draw the overlay with current speed data"""
        height, width = frame.shape[:2]

        # create background
        overlay = frame.copy()
        cv2.rectangle(overlay, (0, 0), (width, 100), self.overlay_settings['bg_color'], -1)
        cv2.addWeighted(overlay, self.overlay_settings['bg_alpha'], frame,
                        1 - self.overlay_settings['bg_alpha'], 0, frame)

        # current values from shared memory
        current_speed = self.shared_speed.value
        # current_confidence = self.shared_data[1]  # Example of additional data

        # timestamp
        timestamp_str = timestamp.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]
        cv2.putText(frame, timestamp_str, (10, 25),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)

        # speed display
        speed_text = f"Speed: {current_speed:.1f} km/h"
        cv2.putText(frame, speed_text, (10, 60),
                    cv2.FONT_HERSHEY_SIMPLEX, self.overlay_settings['font_scale'],
                    self.get_speed_color(current_speed),
                    self.overlay_settings['thickness'] + 1)

        return frame

    def run_overlay(self):
        """Main overlay display process"""
        with picamera.PiCamera() as camera:
            # Configure camera
            camera.resolution = self.camera_config['resolution']
            camera.framerate = self.camera_config['framerate']
            camera.rotation = self.camera_config['rotation']

            # Use RGB array for OpenCV
            raw_capture = PiRGBArray(camera, size=self.camera_config['resolution'])

            # Camera warm-up
            time.sleep(2)

            try:
                for frame in camera.capture_continuous(raw_capture,
                                                       format="bgr",
                                                       use_video_port=True):
                    # Process frame
                    processed_frame = self.draw_overlay(frame.array, datetime.now())

                    # Display
                    cv2.imshow("Speed Overlay", processed_frame)

                    # Clear stream
                    raw_capture.truncate(0)

                    # Exit on 'q' key
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        break
            finally:
                cv2.destroyAllWindows()

    def get_shared_memory(self):
        """Return references to shared memory for external code"""
        return {
            'speed': self.shared_speed,
            'data_array': self.shared_data
        }


if __name__ == "__main__":
    overlay = SpeedOverlay()

    # Start overlay in a separate process
    overlay_process = Process(target=overlay.run_overlay)
    overlay_process.start()

    # Example of how external code would interface
    try:
        shared = overlay.get_shared_memory()
        while True:
            # External code would update these values
            shared['speed'].value = 30.5  # Example speed update
            time.sleep(0.1)
    except KeyboardInterrupt:
        pass
    finally:
        overlay_process.terminate()