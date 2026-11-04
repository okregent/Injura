import cv2
import mediapipe as mp
import math

from .base_estimator import BasePoseEstimator
from .types import Landmark, PoseExtractionResult, PoseSequence

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
        return self.extract_with_metadata(video_path).pose_sequence

    def extract_with_metadata(self, video_path: str) -> PoseExtractionResult:
        pose_sequence : PoseSequence = []
        source_frame_indices = []
        source_frame_count = 0
        image_size = None

        cap = cv2.VideoCapture(video_path)
        source_fps = cap.get(cv2.CAP_PROP_FPS)
        fps = source_fps if math.isfinite(source_fps) and source_fps > 0 else None
        

        while cap.isOpened():
            success, frame = cap.read()

            if not success:
                break

            if image_size is None:
                height, width = frame.shape[:2]
                image_size = (width, height)

            source_frame_index = source_frame_count
            source_frame_count += 1
            
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
            source_frame_indices.append(source_frame_index)

        cap.release()
        cv2.destroyAllWindows()

        return PoseExtractionResult(
            pose_sequence=pose_sequence,
            source_frame_indices=source_frame_indices,
            source_frame_count=source_frame_count,
            image_size=image_size,
            fps=fps,
        )
    
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
