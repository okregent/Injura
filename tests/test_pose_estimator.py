from engine.pose.mediapipe_estimator import MediaPipePoseEstimator


def test_extract_pose_sequence():
    print("Test started")

    video_path = r"C:\Users\okreg\projects\Injura\sample_video.mp4"
    print("Video path:", video_path)

    estimator = MediaPipePoseEstimator()
    print("Estimator created")

    pose_sequence = estimator.extract(video_path)
    print("Extraction finished")

    print("Number of frames:", len(pose_sequence))

    if len(pose_sequence) > 0:
        print("Landmarks in first frame:", len(pose_sequence[0]))
        print("First landmark:", pose_sequence[0][0])


if __name__ == "__main__":
    test_extract_pose_sequence()