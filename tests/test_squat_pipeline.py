from engine.pose.mediapipe_estimator import MediaPipePoseEstimator
from engine.squat.phases import (
    calculate_squat_phase_thresholds,
    extract_hip_y_values,
    detect_squat_phases,
)
from engine.squat.reps import detect_squat_reps
from engine.squat.smoothing import smooth_squat_phases

def test_real_video_squat_pipeline():
    video_path = "sample_video2.mp4"

    estimator = MediaPipePoseEstimator()

    pose_sequence = estimator.extract(video_path)
    hip_y_values = extract_hip_y_values(pose_sequence)
    phases = detect_squat_phases(hip_y_values)
    reps = detect_squat_reps(phases)

    assert len(pose_sequence) > 0
    assert len(hip_y_values) == len(pose_sequence)
    assert len(phases) == len(pose_sequence)
    assert isinstance(reps, list)

    estimator.close()

