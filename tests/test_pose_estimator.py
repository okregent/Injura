from engine.pose.mediapipe_estimator import MediaPipePoseEstimator
import cv2




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




def test_visualize_pose_estimation():
    video_path = r"C:\Users\okreg\projects\Injura\sample_video.mp4"

    estimator = MediaPipePoseEstimator()
    cap = cv2.VideoCapture(video_path)

    while cap.isOpened():
        success, frame = cap.read()

        if not success:
            break

        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = estimator.pose.process(rgb_frame)

        if results.pose_landmarks is not None:
            estimator.visualize(frame, results.pose_landmarks)

        if cv2.waitKey(30) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()
    estimator.close()


if __name__ == "__main__":
    test_visualize_pose_estimation()
    test_extract_pose_sequence()