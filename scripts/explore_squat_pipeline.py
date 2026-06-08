


from engine.pose.mediapipe_estimator import MediaPipePoseEstimator
from engine.squat.phases import (
    calculate_squat_phase_thresholds,
    extract_hip_y_values,
    detect_squat_phases,
)
from engine.squat.reps import detect_squat_reps
from engine.squat.smoothing import smooth_squat_phases
from engine.squat.windowing import (
    detect_rough_movement_window,
    detect_squat_analysis_window,
    detect_refined_analysis_window,
)

def print_phase_segments(phases):
    if not phases:
        return

    start = 0
    current = phases[0]

    for i in range(1, len(phases)):
        if phases[i] != current:
            print(
                f"{start:4d}-{i - 1:4d}",
                current.name,
                f"len={i - start}",
            )
            start = i
            current = phases[i]

    print(
        f"{start:4d}-{len(phases) - 1:4d}",
        current.name,
        f"len={len(phases) - start}",
    )

def main():
    video_path = "sample_video_not_edited.mp4"

    estimator = MediaPipePoseEstimator()

    pose_sequence = estimator.extract(video_path)
    hip_y_values = extract_hip_y_values(pose_sequence)

    thresholds = calculate_squat_phase_thresholds(hip_y_values)

    raw_phases = detect_squat_phases(hip_y_values)

    smoothed_phases = smooth_squat_phases(
        raw_phases,
        min_duration=2,
    )

    raw_reps = detect_squat_reps(raw_phases)
    smoothed_reps = detect_squat_reps(smoothed_phases)

    window = detect_rough_movement_window(smoothed_phases)

    print(f"Rough window: {window}")

    if window is not None:
        start, end = window

        cropped_hip_y = hip_y_values[start:end + 1]

        cropped_thresholds = calculate_squat_phase_thresholds(cropped_hip_y)

        cropped_phases = detect_squat_phases(cropped_hip_y)

        cropped_smoothed_phases = smooth_squat_phases(cropped_phases,min_duration=2,)

        cropped_reps = detect_squat_reps(cropped_smoothed_phases)

        print("Cropped thresholds:", cropped_thresholds)
        print(f"Cropped reps: {len(cropped_reps)}")

        print("\nCROPPED PHASE SEGMENTS")
        print_phase_segments(cropped_smoothed_phases)
    else:
        print("No rough movement window found.")

    analysis_window = detect_squat_analysis_window(smoothed_reps)
    print(f"Analysis window: {analysis_window}")
    if analysis_window is not None:
        start, end = analysis_window
        print(f"Analysis start: {start}")
        print(f"Analysis end: {end}")
        print(f"Analysis length: {end - start + 1}")
    else:
        print("No analysis window found.")

    print(f"Pose frames: {len(pose_sequence)}")
    print(f"Hip y values: {len(hip_y_values)}")
    print(f"Raw phases: {len(raw_phases)}")
    print(f"Smoothed phases: {len(smoothed_phases)}")

    print(f"Raw reps: {len(raw_reps)}")
    print(f"Smoothed reps: {len(smoothed_reps)}")

    print("Thresholds:", thresholds)
    print("Min hip_y:", min(hip_y_values))
    print("Max hip_y:", max(hip_y_values))

    changes = [
        (i, raw.name, smooth.name)
        for i, (raw, smooth) in enumerate(zip(raw_phases, smoothed_phases))
        if raw != smooth
    ]

    print(f"Changed frames: {len(changes)}")
    print("First 30 changes:", changes[:30])

    print("\nFrame | hip_y | raw_phase | smoothed_phase")
    for i in range(850, min(903, len(hip_y_values))):
        print(
            i,
            round(hip_y_values[i], 4),
            raw_phases[i].name,
            smoothed_phases[i].name,
        )

    print("\nRAW PHASE SEGMENTS")
    print_phase_segments(raw_phases)

    print("\nSMOOTHED PHASE SEGMENTS")
    print_phase_segments(smoothed_phases)

    window = detect_refined_analysis_window(
    hip_y_values)
    print(f"Refined analysis window: {window}")

    estimator.close()

    




if __name__ == "__main__":
    main()