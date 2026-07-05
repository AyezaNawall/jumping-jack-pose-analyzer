import tkinter as tk
from tkinter import filedialog, messagebox

import cv2
from PIL import Image, ImageTk

from oop import PoseDetector


class ExerciseApp:
    WINDOW_SIZE = "1280x720"
    SIDEBAR_WIDTH = 320
    PANEL_BG = "#111827"
    APP_BG = "#0b1120"
    CARD_BG = "#172033"
    BORDER = "#263348"
    TEXT = "#f8fafc"
    MUTED = "#94a3b8"
    ACCENT = "#38bdf8"
    SUCCESS = "#22c55e"
    DANGER = "#ef4444"
    WARNING = "#f59e0b"

    def __init__(self, window):
        self.window = window
        self.running = False
        self.cap = None
        self.is_live = False
        self.count = 0
        self.status = "down"
        self.current_angle = None

        self.detector = PoseDetector()

        self.configure_window()
        self.build_layout()
        self.update_stats()

    def configure_window(self):
        self.window.title("Jumping Jack Pose Analyzer")
        self.window.geometry(self.WINDOW_SIZE)
        self.window.minsize(1050, 640)
        self.window.configure(bg=self.APP_BG)
        self.window.protocol("WM_DELETE_WINDOW", self.close_app)

    def build_layout(self):
        self.main = tk.Frame(self.window, bg=self.APP_BG)
        self.main.pack(fill=tk.BOTH, expand=True)

        self.video_area = tk.Frame(self.main, bg=self.APP_BG, padx=28, pady=24)
        self.video_area.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.sidebar = tk.Frame(self.main, width=self.SIDEBAR_WIDTH, bg=self.PANEL_BG, padx=22, pady=24)
        self.sidebar.pack(side=tk.RIGHT, fill=tk.Y)
        self.sidebar.pack_propagate(False)

        self.build_video_panel()
        self.build_sidebar()

    def build_video_panel(self):
        header = tk.Frame(self.video_area, bg=self.APP_BG)
        header.pack(fill=tk.X)

        tk.Label(
            header,
            text="Jumping Jack Analyzer",
            font=("Segoe UI", 24, "bold"),
            bg=self.APP_BG,
            fg=self.TEXT,
        ).pack(anchor="w")

        tk.Label(
            header,
            text="Live pose tracking for reps, arm angle, and movement state",
            font=("Segoe UI", 11),
            bg=self.APP_BG,
            fg=self.MUTED,
        ).pack(anchor="w", pady=(4, 18))

        self.video_shell = tk.Frame(
            self.video_area,
            bg="#020617",
            highlightbackground=self.BORDER,
            highlightthickness=1,
            padx=10,
            pady=10,
        )
        self.video_shell.pack(fill=tk.BOTH, expand=True)

        self.video_frame = tk.Label(
            self.video_shell,
            text="Choose live camera or upload a video",
            font=("Segoe UI", 16, "bold"),
            bg="#020617",
            fg=self.MUTED,
            compound=tk.CENTER,
        )
        self.video_frame.pack(fill=tk.BOTH, expand=True)

        self.footer_status = tk.Label(
            self.video_area,
            text="Ready",
            font=("Segoe UI", 10),
            bg=self.APP_BG,
            fg=self.MUTED,
        )
        self.footer_status.pack(anchor="w", pady=(12, 0))

    def build_sidebar(self):
        tk.Label(
            self.sidebar,
            text="Controls",
            font=("Segoe UI", 20, "bold"),
            bg=self.PANEL_BG,
            fg=self.TEXT,
        ).pack(anchor="w")

        tk.Label(
            self.sidebar,
            text="Select a source and monitor the analysis in real time.",
            font=("Segoe UI", 10),
            bg=self.PANEL_BG,
            fg=self.MUTED,
            wraplength=260,
            justify=tk.LEFT,
        ).pack(anchor="w", pady=(4, 22))

        self.create_button("Start Live Camera", self.SUCCESS, self.start_live).pack(fill=tk.X, pady=(0, 10))
        self.create_button("Upload Video", self.ACCENT, self.upload_video).pack(fill=tk.X, pady=(0, 10))
        self.create_button("Reset Session", self.DANGER, self.reset_app).pack(fill=tk.X, pady=(0, 28))

        self.metric_count = self.create_metric_card("Repetitions", "0", self.WARNING)
        self.metric_status = self.create_metric_card("Movement State", "IDLE", self.ACCENT)
        self.metric_angle = self.create_metric_card("Shoulder Angle", "--", self.SUCCESS)

        self.source_label = tk.Label(
            self.sidebar,
            text="Source: none",
            font=("Segoe UI", 10),
            bg=self.PANEL_BG,
            fg=self.MUTED,
        )
        self.source_label.pack(anchor="w", pady=(22, 0))

    def create_button(self, text, color, command):
        button = tk.Button(
            self.sidebar,
            text=text,
            command=command,
            font=("Segoe UI", 11, "bold"),
            bg=color,
            fg="#ffffff",
            activebackground=color,
            activeforeground="#ffffff",
            bd=0,
            cursor="hand2",
            padx=14,
            pady=12,
        )
        return button

    def create_metric_card(self, label, value, accent):
        card = tk.Frame(
            self.sidebar,
            bg=self.CARD_BG,
            highlightbackground=self.BORDER,
            highlightthickness=1,
            padx=16,
            pady=14,
        )
        card.pack(fill=tk.X, pady=(0, 12))

        tk.Label(
            card,
            text=label.upper(),
            font=("Segoe UI", 9, "bold"),
            bg=self.CARD_BG,
            fg=self.MUTED,
        ).pack(anchor="w")

        value_label = tk.Label(
            card,
            text=value,
            font=("Segoe UI", 24, "bold"),
            bg=self.CARD_BG,
            fg=accent,
        )
        value_label.pack(anchor="w", pady=(4, 0))
        return value_label

    def start_live(self):
        self.reset_app()
        self.cap = cv2.VideoCapture(0)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

        if not self.cap.isOpened():
            self.cap.release()
            self.cap = None
            messagebox.showerror("Camera Error", "Unable to open the camera.")
            self.footer_status.config(text="Camera unavailable")
            return

        self.running = True
        self.is_live = True
        self.source_label.config(text="Source: live camera")
        self.footer_status.config(text="Live camera running")
        self.update_frame()

    def upload_video(self):
        filename = filedialog.askopenfilename(
            title="Select Video",
            filetypes=(("Video files", "*.mp4 *.avi *.mov *.mkv"), ("All files", "*.*")),
        )
        if not filename:
            return

        self.reset_app()
        self.cap = cv2.VideoCapture(filename)
        if not self.cap.isOpened():
            self.cap.release()
            self.cap = None
            messagebox.showerror("Video Error", "Unable to open the selected video.")
            self.footer_status.config(text="Video could not be opened")
            return

        self.running = True
        self.is_live = False
        self.source_label.config(text=f"Source: {filename.split('/')[-1].split(chr(92))[-1]}")
        self.footer_status.config(text="Video analysis running")
        self.update_frame()

    def reset_app(self):
        self.running = False
        if self.cap:
            self.cap.release()
            self.cap = None

        self.count = 0
        self.status = "down"
        self.current_angle = None
        self.is_live = False
        self.update_stats()
        self.source_label.config(text="Source: none")
        self.footer_status.config(text="Ready")
        self.video_frame.config(image="", text="Choose live camera or upload a video")
        self.video_frame.imgtk = None

    def update_frame(self):
        if not self.running or not self.cap:
            return

        success, img = self.cap.read()
        if not success:
            self.running = False
            self.footer_status.config(text="Video finished")
            return

        if self.is_live:
            img = cv2.flip(img, 1)

        img_display = self.resize_aspect_fit(img, max_width=self.video_width(), max_height=self.video_height())
        self.detector.findPose(img_display)
        landmarks = self.detector.findPosition(img_display, draw=False)

        if len(landmarks) >= 29:
            self.analyze_jumping_jack(img_display, landmarks)
            self.update_stats()

        self.show_frame(img_display)
        self.window.after(30, self.update_frame)

    def analyze_jumping_jack(self, img, landmarks):
        hip_shoulder_dist_l = self.detector.calculateDistance(
            landmarks[11][1], landmarks[11][2], landmarks[23][1], landmarks[23][2]
        )
        hip_shoulder_dist_r = self.detector.calculateDistance(
            landmarks[12][1], landmarks[12][2], landmarks[24][1], landmarks[24][2]
        )
        wrist_shoulder_dist_l = self.detector.calculateDistance(
            landmarks[15][1], landmarks[15][2], landmarks[11][1], landmarks[11][2]
        )
        wrist_shoulder_dist_r = self.detector.calculateDistance(
            landmarks[16][1], landmarks[16][2], landmarks[12][1], landmarks[12][2]
        )
        hip_wrist_dist_l = self.detector.calculateDistance(
            landmarks[15][1], landmarks[15][2], landmarks[23][1], landmarks[23][2]
        )
        hip_wrist_dist_r = self.detector.calculateDistance(
            landmarks[16][1], landmarks[16][2], landmarks[24][1], landmarks[24][2]
        )

        shoulder_angle_l = self.detector.calculateAngle(
            hip_shoulder_dist_l, wrist_shoulder_dist_l, hip_wrist_dist_l
        )
        shoulder_angle_r = self.detector.calculateAngle(
            hip_shoulder_dist_r, wrist_shoulder_dist_r, hip_wrist_dist_r
        )
        self.current_angle = (shoulder_angle_l + shoulder_angle_r) / 2

        shoulder_dist = abs(landmarks[12][1] - landmarks[11][1])
        ankle_dist = abs(landmarks[28][1] - landmarks[27][1])

        if self.current_angle > 140 and ankle_dist > shoulder_dist * 0.5:
            self.status = "up"

        if self.current_angle < 30 and ankle_dist < shoulder_dist * 0.5 and self.status == "up":
            self.status = "down"
            self.count += 1

        joint_color = (34, 197, 94) if self.status == "up" else (239, 68, 68)
        for point in [11, 12, 13, 14, 15, 16, 23, 24, 27, 28]:
            cx, cy = landmarks[point][1], landmarks[point][2]
            cv2.circle(img, (cx, cy), 10, joint_color, cv2.FILLED)

    def update_stats(self):
        status_text = "IDLE" if not self.running else self.status.upper()
        angle_text = "--" if self.current_angle is None else f"{int(self.current_angle)} deg"
        self.metric_count.config(text=str(self.count))
        self.metric_status.config(text=status_text)
        self.metric_angle.config(text=angle_text)

    def show_frame(self, img):
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        img_pil = Image.fromarray(img_rgb)
        imgtk = ImageTk.PhotoImage(image=img_pil)

        self.video_frame.imgtk = imgtk
        self.video_frame.configure(image=imgtk, text="")

    def video_width(self):
        width = self.video_shell.winfo_width() - 24
        return max(width, 640)

    def video_height(self):
        height = self.video_shell.winfo_height() - 24
        return max(height, 420)

    def resize_aspect_fit(self, img, max_width, max_height):
        h, w = img.shape[:2]
        scale = min(max_width / w, max_height / h)
        new_w = max(1, int(w * scale))
        new_h = max(1, int(h * scale))
        return cv2.resize(img, (new_w, new_h))

    def close_app(self):
        self.running = False
        if self.cap:
            self.cap.release()
        self.window.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    app = ExerciseApp(root)
    root.mainloop()
