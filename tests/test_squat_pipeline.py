from engine.pose.mediapipe_estimator import MediaPipePoseEstimator
from engine.squat.phases import (
    extract_hip_y_values,
    detect_squat_phases,
)
from engine.squat.reps import detect_squat_reps
from engine.squat.smoothing import smooth_squat_phases
from engine.squat.windowing import detect_squat_analysis_window
from engine.squat.analyzer import SquatAnalyzer
from engine.pose.side import BodySide
from engine.pose.orientation import FacingDirection


def test_real_video_squat_pipeline():
    estimator = MediaPipePoseEstimator()

    try:
        extraction = estimator.extract_with_metadata("sample_video2.mp4")
        pose_sequence = extraction.pose_sequence

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
        assert extraction.fps is not None and extraction.fps > 0
        assert extraction.image_size is not None
        analysis = SquatAnalyzer().analyze(
            extraction, side=BodySide.LEFT, facing_direction=FacingDirection.RIGHT,
        )
        assert analysis.features.frame_count == len(pose_sequence)
        assert len(analysis.phases) == len(pose_sequence)
        assert len(analysis.repetitions) >= 1
        assert all(rep.metrics["depth"].value is not None for rep in analysis.repetitions)
        assert all(rep.metrics["normalized_knee_travel"].value is None for rep in analysis.repetitions)

    finally:
        estimator.close()
