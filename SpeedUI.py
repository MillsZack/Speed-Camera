import tkinter as tk
from tkinter import ttk, messagebox
import json
import os

class SpeedCameraUI:
    def __init__(self, master):
        self.master = master
        master.title("Speed Camera Settings")
        master.geometry("400x250")  # Adjusted window size
        
        # Use default styling that ensures readable text
        style = ttk.Style()
        style.configure('TButton', font=('Helvetica', 10), padding=5)
        
        # Main frame
        main_frame = ttk.Frame(master, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Title
        ttk.Label(main_frame, text="Speed Camera Configuration", 
                font=('Helvetica', 12, 'bold')).grid(row=0, column=0, columnspan=2, pady=(0, 15))
        
        # Default values
        self.speed_limit = 30
        self.threshold = 5
        
        # Load existing settings
        self.load_settings()
        
        # Speed Limit
        ttk.Label(main_frame, text="Speed Limit (mph):").grid(row=1, column=0, sticky=tk.W, pady=5)
        self.speed_entry = ttk.Entry(main_frame)
        self.speed_entry.grid(row=1, column=1, pady=5, sticky=tk.EW)
        self.speed_entry.insert(0, str(self.speed_limit))
        
        # Threshold
        ttk.Label(main_frame, text="Threshold (mph):").grid(row=2, column=0, sticky=tk.W, pady=5)
        self.thresh_entry = ttk.Entry(main_frame)
        self.thresh_entry.grid(row=2, column=1, pady=5, sticky=tk.EW)
        self.thresh_entry.insert(0, str(self.threshold))
        
        # Explanation
        ttk.Label(main_frame, 
                 text="Threshold is added to speed limit to\navoid minor speeding violations.",
                 font=('Helvetica', 8),
                 foreground="#666666").grid(row=3, column=0, columnspan=2, pady=10)
        
        # Button frame
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=4, column=0, columnspan=2, pady=10)
        
        # Save Settings Button - Now with visible text
        self.save_button = ttk.Button(
            button_frame, 
            text="Save Settings", 
            command=self.save_settings
        )
        self.save_button.pack(side=tk.LEFT, padx=5)
        
        # Start Camera Button
        self.start_button = ttk.Button(
            button_frame, 
            text="Start Speed Camera", 
            command=self.start_camera
        )
        self.start_button.pack(side=tk.LEFT, padx=5)
        
        # Configure grid weights
        main_frame.columnconfigure(1, weight=1)
    
    def load_settings(self):
        """Load settings from JSON file if it exists"""
        if os.path.exists("camera_settings.json"):
            with open("camera_settings.json", "r") as f:
                settings = json.load(f)
                self.speed_limit = settings.get("speed_limit", 30)
                self.threshold = settings.get("threshold", 5)
    
    def save_settings(self):
        """Save the current settings to file"""
        try:
            self.speed_limit = int(self.speed_entry.get())
            self.threshold = int(self.thresh_entry.get())
            
            settings = {
                "speed_limit": self.speed_limit,
                "threshold": self.threshold
            }
            
            with open("camera_settings.json", "w") as f:
                json.dump(settings, f)
            
            messagebox.showinfo("Saved", "Settings have been saved successfully!")
        except ValueError:
            messagebox.showerror("Error", "Please enter valid numbers")
    
    def start_camera(self):
        """Close the UI and start the camera with current settings"""
        try:
            # Validate inputs
            speed = int(self.speed_entry.get())
            threshold = int(self.thresh_entry.get())
            
            if speed <= 0 or threshold <= 0:
                raise ValueError("Values must be positive")
            
            # Save before starting
            self.save_settings()
            self.master.destroy()
        except ValueError as e:
            messagebox.showerror("Error", f"Invalid settings: {str(e)}")

def run_ui():
    root = tk.Tk()
    app = SpeedCameraUI(root)
    root.mainloop()
    
    # Return the settings after window closes
    try:
        with open("camera_settings.json", "r") as f:
            settings = json.load(f)
            return settings["speed_limit"], settings["threshold"]
    except:
        return 30, 5  # Default values

if __name__ == "__main__":
    speed_limit, threshold = run_ui()
    print(f"Starting camera with: Speed Limit={speed_limit}, Threshold={threshold}")
