from engine.squat.phases import SquatPhase
from engine.squat.reps import detect_squat_reps
from engine.squat.smoothing import smooth_squat_phases


def test_phase_smoothing_preserves_rep_count():
    phases = [
        SquatPhase.STANDING,

        SquatPhase.DESCENDING,
        SquatPhase.DESCENDING,
        SquatPhase.BOTTOM,
        SquatPhase.ASCENDING,
        SquatPhase.STANDING,

        SquatPhase.DESCENDING,
        SquatPhase.ASCENDING,  # spike
        SquatPhase.DESCENDING,
        SquatPhase.BOTTOM,
        SquatPhase.ASCENDING,
        SquatPhase.STANDING,

        SquatPhase.DESCENDING,
        SquatPhase.BOTTOM,
        SquatPhase.ASCENDING,
        SquatPhase.STANDING,
    ]

    raw_reps = detect_squat_reps(phases)

    smoothed_phases = smooth_squat_phases(
        phases,
        min_duration=2,
    )

    smoothed_reps = detect_squat_reps(smoothed_phases)

    assert len(raw_reps) == 3
    assert len(smoothed_reps) == 3

def test_smoothing_removes_single_frame_phase_spike():
    phases = [
        SquatPhase.DESCENDING,
        SquatPhase.ASCENDING,
        SquatPhase.DESCENDING,
    ]

    smoothed = smooth_squat_phases(
        phases,
        min_duration=2,
    )

    assert smoothed == [
        SquatPhase.DESCENDING,
        SquatPhase.DESCENDING,
        SquatPhase.DESCENDING,
    ]