from engine.squat.phases import SquatPhase, detect_squat_reps


def test_detect_multiple_squat_reps():
    phases = [
        SquatPhase.STANDING,
        SquatPhase.DESCENDING,
        SquatPhase.BOTTOM,
        SquatPhase.ASCENDING,
        SquatPhase.STANDING,

        SquatPhase.DESCENDING,
        SquatPhase.BOTTOM,
        SquatPhase.ASCENDING,
        SquatPhase.STANDING,
    ]

    reps = detect_squat_reps(phases)

    assert len(reps) == 2

    assert reps[0].start_index == 1
    assert reps[0].bottom_index == 2
    assert reps[0].end_index == 4

    assert reps[1].start_index == 5
    assert reps[1].bottom_index == 6
    assert reps[1].end_index == 8

def test_incomplete_rep_is_not_counted():
    phases = [
        SquatPhase.STANDING,
        SquatPhase.DESCENDING,
        SquatPhase.BOTTOM,
        SquatPhase.ASCENDING,
    ]

    reps = detect_squat_reps(phases)

    assert len(reps) == 0

def test_empty_phase_list_returns_no_reps():
    reps = detect_squat_reps([])

    assert reps == []

def test_no_bottom_rep_is_not_counted():
    phases = [
        SquatPhase.STANDING,
        SquatPhase.DESCENDING,
        SquatPhase.ASCENDING,
        SquatPhase.STANDING,
    ]

    reps = detect_squat_reps(phases)

    assert len(reps) == 0