import cv2
import mediapipe as mp

from .base_estimator import BasePoseEstimator
from .types import Landmark, PoseSequence

class MediaPipePoseEstimator(BasePoseEstimator):
    def __init__(self):
        self.mp_pose = mp.solutions.pose
        self.mp_drawing = mp.solutions.drawing_utils
        self.pose = self.mp_pose.Pose(
            #video tracking mode
            static_image_mode=False,
            #accuracy vs speed tradeoff
            model_complexity=1,
            #smoothing landmarks across frames to reduce jitter
            smooth_landmarks=True,
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

            for lndmark in results.pose_landmarks.landmark:
                frame_landmarks.append(
                    Landmark(
                        x=lndmark.x,
                        y=lndmark.y,
                        z=lndmark.z,
                        visibility=lndmark.visibility
                    )
                )
            pose_sequence.append(frame_landmarks)

        cap.release()
        cv2.destroyAllWindows()

        return pose_sequence
    
    def close(self):
        self.pose.close()
    
    def visualize(self, frame, pose_landmarks):
        self.mp_drawing.draw_landmarks(
            frame,
            pose_landmarks,
            self.mp_pose.POSE_CONNECTIONS,
        )

        scale = 0.5

        resized_frame = cv2.resize(
            frame,
            None,
            fx=scale,
            fy=scale
        )

        cv2.imshow("Pose Estimation", resized_frame)

        return cv2.waitKey(30)
