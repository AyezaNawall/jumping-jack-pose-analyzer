import cv2
import math
from pathlib import Path
from math import degrees, acos

try:
    import mediapipe as mp
except ImportError as exc:
    raise ImportError(
        "MediaPipe is not installed. Run: python -m pip install mediapipe"
    ) from exc

try:
    mpDraw = mp.solutions.drawing_utils
    mpPose = mp.solutions.pose
except AttributeError:
    mpDraw = None
    mpPose = None

try:
    from mediapipe.tasks.python import vision
    from mediapipe.tasks.python.core.base_options import BaseOptions
except ImportError:
    vision = None
    BaseOptions = None

MODEL_PATH = Path(__file__).with_name("pose_landmarker_lite.task")

class PoseDetector:
    def __init__(self, mode=False, smooth=True, detectionCon=0.5, trackCon=0.5):
        self.mode = mode
        self.smooth = smooth
        self.detectionCon = detectionCon
        self.trackCon = trackCon
        self.results = None

        if mpPose is not None:
            self.api = "solutions"
            self.mpDraw = mpDraw
            self.mpPose = mpPose
            self.pose = self.mpPose.Pose(static_image_mode=self.mode,
                                         smooth_landmarks=self.smooth,
                                         min_detection_confidence=self.detectionCon,
                                         min_tracking_confidence=self.trackCon)
        elif vision is not None and BaseOptions is not None:
            self.api = "tasks"
            if not MODEL_PATH.exists():
                raise FileNotFoundError(
                    f"Missing MediaPipe pose model: {MODEL_PATH.name}. "
                    "Download pose_landmarker_lite.task into this project folder."
                )
            options = vision.PoseLandmarkerOptions(
                base_options=BaseOptions(model_asset_path=str(MODEL_PATH)),
                running_mode=vision.RunningMode.IMAGE,
                num_poses=1,
                min_pose_detection_confidence=self.detectionCon,
                min_tracking_confidence=self.trackCon,
            )
            self.landmarker = vision.PoseLandmarker.create_from_options(options)
        else:
            raise ImportError(
                "This MediaPipe install has neither the old solutions API nor "
                "the new tasks vision API."
            )

    def findPose(self, img, draw=True):
        imgRGB = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        if self.api == "solutions":
            self.results = self.pose.process(imgRGB)
            if self.results.pose_landmarks and draw:
                self.mpDraw.draw_landmarks(img, self.results.pose_landmarks, self.mpPose.POSE_CONNECTIONS)
            return img

        mp_image = mp.Image(image_format=mp.ImageFormat.SRGB, data=imgRGB)
        self.results = self.landmarker.detect(mp_image)
        if self.results.pose_landmarks and draw:
            self._draw_task_landmarks(img, self.results.pose_landmarks[0])
        return img

    def findPosition(self, img, draw=True, bboxWithHands=False):
        self.lmList = []
        if self.results is None:
            return self.lmList

        if self.api == "solutions" and self.results.pose_landmarks:
            for id, lm in enumerate(self.results.pose_landmarks.landmark):
                h, w, c = img.shape
                cx, cy, cz = int(lm.x * w), int(lm.y * h), int(lm.z * w)
                self.lmList.append([id, cx, cy, cz])
        elif self.api == "tasks" and self.results.pose_landmarks:
            h, w, c = img.shape
            for id, lm in enumerate(self.results.pose_landmarks[0]):
                cx, cy, cz = int(lm.x * w), int(lm.y * h), int(lm.z * w)
                self.lmList.append([id, cx, cy, cz])
        return self.lmList

    def _draw_task_landmarks(self, img, landmarks):
        h, w, c = img.shape
        for connection in vision.PoseLandmarksConnections.POSE_LANDMARKS:
            start = landmarks[connection.start]
            end = landmarks[connection.end]
            start_point = (int(start.x * w), int(start.y * h))
            end_point = (int(end.x * w), int(end.y * h))
            cv2.line(img, start_point, end_point, (255, 255, 255), 2)

        for lm in landmarks:
            cx, cy = int(lm.x * w), int(lm.y * h)
            cv2.circle(img, (cx, cy), 4, (0, 255, 255), cv2.FILLED)
    
    def calculateDistance(self, x1, y1, x2, y2):
        distance = math.sqrt((x1 - x2)**2 + (y1 - y2)**2)
        return distance

    def calculateAngle(self, a, b, c):
        # Calculates angle using Law of Cosines based on 3 side lengths
        try:
            ABC_numerator = a**2 + b**2 - c**2
            ABC_denominator = 2 * a * b
            ABC_cosine_angle = degrees(acos(max(-1.0, min(1.0, ABC_numerator / ABC_denominator))))
            return ABC_cosine_angle
        except ZeroDivisionError:
            return 0
