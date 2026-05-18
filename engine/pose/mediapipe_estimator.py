import cv2
import mediapipe as mp

from .base_estimator import BasePoseEstimator
from .types import Landmark, PoseSequence

class MediaPipePoseEstimator(BasePoseEstimator):
    def __init__(self):
        self.mp_pose = mp.solutions.pose

        self.pose = self.mp_pose.Pose(
            #video tracking mode
            static_image_mode=False,
            #accuracy vs speed tradeoff
            model_complexity=1,
            #smoothing landmarks across frames to reduce jitter
            smmooth_landmarks=True,
            #minimum confidence for detecting landmarks in a frame
            min_detection_confidence=0.5,
            #minimum confidence for tracking landmarks across frames
            min_tracking_confidence=0.5
        )

    def extract(self, video_path: str) -> PoseSequence:
        pose_sequence : PoseSequence = []

        cap = cv2.VideoCapture(video_path)

        while cap.isOpened():
            success, frame = cap.read()

            if not success:
                break
            
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            results = self.pose.process(rgb_frame)  
            
            if results.pose_landmarks is None:
                continue

            frame_landmarks = []

            for Landmark in results.pose_landmarks.landmark:
                frame_landmarks.append(
                    Landmark(
                        x=Landmark.x,
                        y=Landmark.y,
                        z=Landmark.z,
                        visibility=Landmark.visibility
                    )
                )
            pose_sequence.append(frame_landmarks)
            cap.release()

        return pose_sequence