import tkinter as tk
from tkinter import ttk, messagebox
import json
import os

class EnhancedSpeedCameraUI:
    def __init__(self, master):
        self.master = master
        master.title("Speed Camera Configuration")
        master.geometry("400x300")  # Larger window size
        master.resizable(False, False)  # Fixed size
        
        # Style configuration
        self.style = ttk.Style()
        self.style.configure('TLabel', font=('Helvetica', 10))
        self.style.configure('TButton', font=('Helvetica', 10), padding=5)
        self.style.configure('TEntry', font=('Helvetica', 10), padding=5)
        
        # Configure colors
        master.configure(bg='#f0f0f0')
        self.frame_bg = '#ffffff'
        
        # Main container frame
        self.main_frame = ttk.Frame(master, padding="20", style='Card.TFrame')
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Header
        self.header = ttk.Label(
            self.main_frame, 
            text="Speed Camera Settings", 
            font=('Helvetica', 14, 'bold')
        )
        self.header.grid(row=0, column=0, columnspan=2, pady=(0, 20))
        
        # Default values
        self.speed_limit = 30
        self.threshold = 5
        
        # Try to load previous settings
        self.load_settings()
        
        # Speed Limit
        ttk.Label(
            self.main_frame, 
            text="Speed Limit (mph):"
        ).grid(row=1, column=0, sticky=tk.W, pady=5)
        
        self.speed_entry = ttk.Entry(self.main_frame)
        self.speed_entry.grid(row=1, column=1, pady=5, padx=10, sticky=tk.EW)
        self.speed_entry.insert(0, str(self.speed_limit))
        
        # Threshold
        ttk.Label(
            self.main_frame, 
            text="Threshold (mph):",
            justify=tk.LEFT
        ).grid(row=2, column=0, sticky=tk.W, pady=5)
        
        self.thresh_entry = ttk.Entry(self.main_frame)
        self.thresh_entry.grid(row=2, column=1, pady=5, padx=10, sticky=tk.EW)
        self.thresh_entry.insert(0, str(self.threshold))
        
        # Explanation label
        ttk.Label(
            self.main_frame, 
            text="Threshold is added to speed limit to determine\nwhen to trigger the camera.",
            font=('Helvetica', 8),
            foreground="#666666"
        ).grid(row=3, column=0, columnspan=2, pady=(10, 20))
        
        # Button frame
        self.button_frame = ttk.Frame(self.main_frame)
        self.button_frame.grid(row=4, column=0, columnspan=2, pady=(10, 0))
        
        # Save Button
        self.save_button = ttk.Button(
            self.button_frame, 
            text="Save Settings", 
            command=self.save_settings,
            
        )
        self.save_button.pack(side=tk.LEFT, padx=5)
        
        # Start Camera Button
        self.start_button = ttk.Button(
            self.button_frame, 
            text="Start Speed Camera", 
            command=self.start_camera
        )
        self.start_button.pack(side=tk.LEFT, padx=5)
        
        # Configure grid weights
        self.main_frame.columnconfigure(1, weight=1)
        
        # Custom styling
        self.create_styles()
    
    def create_styles(self):
        """Create custom styles for a more modern look"""
        self.style.configure('Card.TFrame', background=self.frame_bg, borderwidth=1, relief='solid')
        
        # Accent button style
        self.style.configure('Accent.TButton', 
                            foreground='white', 
                            background='#2c7be5', 
                            bordercolor='#2c7be5', 
                            focuscolor='#2c7be5')
        self.style.map('Accent.TButton',
                      foreground=[('pressed', 'white'), ('active', 'white')],
                      background=[('pressed', '#1a68d1'), ('active', '#3d8af2')])
    
    def load_settings(self):
        """Load settings from JSON file if it exists"""
        if os.path.exists("camera_settings.json"):
            with open("camera_settings.json", "r") as f:
                settings = json.load(f)
                self.speed_limit = settings.get("speed_limit", 30)
                self.threshold = settings.get("threshold", 5)
    
    def save_settings(self):
        """Save settings to JSON file"""
        try:
            self.speed_limit = int(self.speed_entry.get())
            self.threshold = int(self.thresh_entry.get())
            
            if self.speed_limit <= 0 or self.threshold <= 0:
                raise ValueError("Values must be positive")
            
            settings = {
                "speed_limit": self.speed_limit,
                "threshold": self.threshold
            }
            
            with open("camera_settings.json", "w") as f:
                json.dump(settings, f)
            
            messagebox.showinfo("Success", "Settings saved successfully!")
        except ValueError as e:
            messagebox.showerror("Error", f"Invalid input: {str(e)}\nPlease enter positive numbers")
    
    def start_camera(self):
        """Close UI and start camera with current settings"""
        try:
            # Validate before closing
            speed = int(self.speed_entry.get())
            threshold = int(self.thresh_entry.get())
            if speed <= 0 or threshold <= 0:
                raise ValueError("Values must be positive")
            
            self.save_settings()  # Save current values
            self.master.destroy()  # Close the UI window
        except ValueError as e:
            messagebox.showerror("Error", f"Invalid settings: {str(e)}\nCannot start camera")

def run_ui():
    root = tk.Tk()
    
    # Set theme (requires tcl/tk 8.6+ - works on Raspberry Pi OS)
    try:
        root.tk.call('source', 'azure.tcl')
        root.tk.call('set_theme', 'light')
    except:
        pass  # Use default theme if custom theme not available
    
    app = EnhancedSpeedCameraUI(root)
    root.mainloop()
    
    # After UI closes, return the settings
    try:
        with open("camera_settings.json", "r") as f:
            settings = json.load(f)
            return settings["speed_limit"], settings["threshold"]
    except:
        return 30, 5  # Default values if something goes wrong

if __name__ == "__main__":
    speed_limit, threshold = run_ui()
    print(f"Starting camera with: Speed Limit={speed_limit}, Threshold={threshold}")
