from engine.pose.mediapipe_estimator import MediaPipePoseEstimator
from engine.squat.phases import (
    extract_hip_y_values,
    detect_squat_phases,
)
from engine.squat.reps import detect_squat_reps
from engine.squat.smoothing import smooth_squat_phases
from engine.squat.windowing import detect_squat_analysis_window


def test_real_video_squat_pipeline():
    estimator = MediaPipePoseEstimator()

    try:
        pose_sequence = estimator.extract("sample_video2.mp4")

        hip_y_values = extract_hip_y_values(pose_sequence)

        raw_phases = detect_squat_phases(hip_y_values)

        smoothed_phases = smooth_squat_phases(
            raw_phases,
            min_duration=2,
        )

        reps = detect_squat_reps(smoothed_phases)

        analysis_window = detect_squat_analysis_window(reps)

        assert len(pose_sequence) > 0
        assert len(hip_y_values) == len(pose_sequence)
        assert len(raw_phases) == len(pose_sequence)
        assert len(smoothed_phases) == len(pose_sequence)
        assert len(reps) == 3
        assert analysis_window is not None

    finally:
        estimator.close()