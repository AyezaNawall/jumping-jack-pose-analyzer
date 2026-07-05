import tkinter as tk
from tkinter import filedialog
from PIL import Image, ImageTk
import cv2
from oop import PoseDetector  # Ensure oop.py is in the same folder

class ExerciseApp:
    def __init__(self, window):
        self.window = window
        self.window.title("Project 22: Jumping Jack Analyzer")
        self.window.geometry("1280x720")
        
        # --- 1. Variables ---
        self.running = False
        self.cap = None
        self.detector = PoseDetector()
        self.is_live = False  # Track if source is camera or video file
        
        # Logic Variables
        self.count = 0
        self.status = "down" 
        
        # --- 2. GUI Layout ---
        # Sidebar (Right)
        self.sidebar = tk.Frame(window, width=300, bg="#2c3e50")
        self.sidebar.pack(side=tk.RIGHT, fill=tk.Y)
        self.sidebar.pack_propagate(False) 

        # Title
        tk.Label(self.sidebar, text="CONTROLS", font=("Arial", 20, "bold"), 
                 bg="#2c3e50", fg="white").pack(pady=20)

        # Buttons
        tk.Button(self.sidebar, text="START LIVE CAMERA", font=("Arial", 12), 
                  bg="#27ae60", fg="white", command=self.start_live).pack(pady=10, fill=tk.X, padx=20)
        
        tk.Button(self.sidebar, text="UPLOAD VIDEO", font=("Arial", 12), 
                  bg="#2980b9", fg="white", command=self.upload_video).pack(pady=10, fill=tk.X, padx=20)

        tk.Button(self.sidebar, text="RESET", font=("Arial", 12), 
                  bg="#c0392b", fg="white", command=self.reset_app).pack(pady=10, fill=tk.X, padx=20)

        # Stats
        tk.Label(self.sidebar, text="STATS", font=("Arial", 20, "bold"), 
                 bg="#2c3e50", fg="white").pack(pady=(40, 20))

        self.lbl_count = tk.Label(self.sidebar, text="Count: 0", font=("Arial", 16), 
                                 bg="#2c3e50", fg="#f1c40f")
        self.lbl_count.pack(pady=5)

        self.lbl_status = tk.Label(self.sidebar, text="Status: IDLE", font=("Arial", 16), 
                                  bg="#2c3e50", fg="white")
        self.lbl_status.pack(pady=5)
        self.lbl_angle = tk.Label(self.sidebar, text="Angle: nil", font=("Arial", 16), 
                                  bg="#2c3e50", fg="white")
        self.lbl_angle.pack(pady=5)


        # Video Placeholder (Centered)
        self.video_frame = tk.Label(window, text="Video Feed", bg="black", fg="white")
        self.video_frame.pack(side=tk.LEFT, expand=True, fill=tk.BOTH)


    # --- 3. Functions ---

    def start_live(self):
        self.reset_app()
        self.cap = cv2.VideoCapture(0)
        self.cap.set(3, 1280)
        self.cap.set(4, 720)
        self.running = True
        self.is_live = True  # We are live
        self.update_frame()

    def upload_video(self):
        filename = filedialog.askopenfilename(title="Select Video", 
                                              filetypes=(("MP4 files", "*.mp4"), ("All files", "*.*")))
        if filename:
            self.reset_app()
            self.cap = cv2.VideoCapture(filename)
            self.running = True
            self.is_live = False  # We are watching a recording
            self.update_frame()

    def reset_app(self):
        self.running = False
        if self.cap:
            self.cap.release()
        
        self.count = 0
        self.status = "down"
        self.is_live = False
        
        self.lbl_count.config(text="Count: 0")
        self.lbl_status.config(text="Status: IDLE")
        self.video_frame.config(image='') 

    def update_frame(self):
        if not self.running:
            return

        success, img = self.cap.read()
        if not success:
            # Video ended? Stop smoothly.
            self.running = False
            return

        # 1. Flip ONLY if Live (Don't mirror uploaded videos)
        if self.is_live:
            img = cv2.flip(img, 1) 

        # 2. Smart Resize (Fit within the GUI Box)
        # This prevents vertical videos from going off-screen
        img_display = self.resize_aspect_fit(img, max_width=900, max_height=650)
        
        # AI Detection
        self.detector.findPose(img_display)
        lmlist = self.detector.findPosition(img_display, draw=False)
        
        color = (0, 0, 255) 
        
        if len(lmlist) != 0:
            # --- JUMPING JACK LOGIC ---
            
            # 1. Get Distances
            hip_shoulder_dist_l = self.detector.calculateDistance(lmlist[11][1],lmlist[11][2],lmlist[23][1],lmlist[23][2])
            hip_shoulder_dist_r = self.detector.calculateDistance(lmlist[12][1],lmlist[12][2],lmlist[24][1],lmlist[24][2])
            
            wrist_shoulder_dist_r = self.detector.calculateDistance(lmlist[16][1],lmlist[16][2],lmlist[12][1],lmlist[12][2])
            wrist_shoulder_dist_l = self.detector.calculateDistance(lmlist[15][1],lmlist[15][2],lmlist[11][1],lmlist[11][2])
            
            hip_wrist_dist_r = self.detector.calculateDistance(lmlist[16][1],lmlist[16][2],lmlist[24][1],lmlist[24][2])
            hip_wrist_dist_l = self.detector.calculateDistance(lmlist[15][1],lmlist[15][2],lmlist[23][1],lmlist[23][2])
            
            # 2. Get Angles
            shoulder_angle_l = self.detector.calculateAngle(hip_shoulder_dist_l,wrist_shoulder_dist_l,hip_wrist_dist_l)
            shoulder_angle_r = self.detector.calculateAngle(hip_shoulder_dist_r,wrist_shoulder_dist_r,hip_wrist_dist_r)
            
            shoulder_angle = (shoulder_angle_l + shoulder_angle_r) / 2
            
            # 3. Heuristics
            shoulder_dist = abs(lmlist[12][1] - lmlist[11][1])
            ankle_dist = abs(lmlist[28][1] - lmlist[27][1])

            # 4. State Machine
            if shoulder_angle > 140 and ankle_dist > shoulder_dist * 0.5:
                self.status = "up"
            
            if shoulder_angle < 30 and ankle_dist < shoulder_dist * 0.5 and self.status == "up":
                self.status = "down"
                self.count += 1
                
            # 5. Visuals
            if self.status == "up":
                current_color = (0, 255, 0) # Green 
            else:
                current_color = (0, 0, 255) # Red

            joints = [11, 12, 13, 14, 15, 16, 23, 24, 27, 28]
            for point in joints:
                cx, cy = lmlist[point][1], lmlist[point][2]
                cv2.circle(img_display, (cx, cy), 10, current_color, cv2.FILLED)
            self.lbl_count.config(text=f"Count: {self.count}")
            self.lbl_status.config(text=f"Status: {self.status.upper()}")
            self.lbl_angle.config(text=f"Angle: {int(shoulder_angle)}")

        # Display Logic
        img_rgb = cv2.cvtColor(img_display, cv2.COLOR_BGR2RGB)
        img_pil = Image.fromarray(img_rgb)
        imgtk = ImageTk.PhotoImage(image=img_pil)
        
        self.video_frame.imgtk = imgtk 
        self.video_frame.configure(image=imgtk)

        self.window.after(30, self.update_frame)

    def resize_aspect_fit(self, img, max_width, max_height):
        """
        Resizes an image to fit within max_width and max_height 
        while maintaining aspect ratio.
        """
        h, w = img.shape[:2]
        
        # Calculate scaling factor
        scale_w = max_width / w
        scale_h = max_height / h
        scale = min(scale_w, scale_h) # Choose the smaller scale to fit in box
        
        new_w = int(w * scale)
        new_h = int(h * scale)
        
        return cv2.resize(img, (new_w, new_h))

# --- STARTUP BLOCK ---
if __name__ == "__main__":
    root = tk.Tk()
    app = ExerciseApp(root)
    root.mainloop()