from engine.squat.phases import SquatPhase
from engine.squat.smoothing import smooth_squat_phases

def test_smooth_squat_phases_removes_single_frame_spike():
    phases = [
        SquatPhase.DESCENDING,
        SquatPhase.DESCENDING,
        SquatPhase.BOTTOM,
        SquatPhase.DESCENDING,
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
        SquatPhase.DESCENDING,
        SquatPhase.DESCENDING,
    ]

def test_smooth_squat_phases_empty_input():
    assert smooth_squat_phases([]) == []

def test_smooth_squat_phases_returns_copy_when_min_duration_is_one():
    phases = [
        SquatPhase.STANDING,
        SquatPhase.DESCENDING,
        SquatPhase.BOTTOM,
    ]

    smoothed = smooth_squat_phases(
        phases,
        min_duration=1,
    )

    assert smoothed == phases
    assert smoothed is not phases

def test_smooth_squat_phases_preserves_first_segment():
    phases = [
        SquatPhase.BOTTOM,
        SquatPhase.DESCENDING,
        SquatPhase.DESCENDING,
        SquatPhase.DESCENDING,
    ]

    smoothed = smooth_squat_phases(
        phases,
        min_duration=2,
    )

    assert smoothed == phases

def test_smooth_squat_phases_preserves_last_segment():
    phases = [
        SquatPhase.DESCENDING,
        SquatPhase.DESCENDING,
        SquatPhase.DESCENDING,
        SquatPhase.BOTTOM,
    ]

    smoothed = smooth_squat_phases(
        phases,
        min_duration=2,
    )

    assert smoothed == phases