import pytest

from engine.squat.metrics.torso_lean import (
    calculate_torso_lean,
)
from engine.squat.reps import SquatRep


def make_rep(
    start_index: int = 1,
    bottom_index: int = 3,
    end_index: int = 5,
) -> SquatRep:
    return SquatRep(
        start_index=start_index,
        bottom_index=bottom_index,
        end_index=end_index,
    )


def test_calculate_torso_lean_returns_expected_result():
    torso_angles = [
        5,
        10,
        18,
        32,
        25,
        12,
    ]

    result = calculate_torso_lean(
        torso_angles,
        make_rep(),
    )

    assert result.max_lean_angle == pytest.approx(32)
    assert result.max_lean_index == 3
    assert result.standing_angle == pytest.approx(10)
    assert result.lean_change == pytest.approx(22)


def test_calculate_torso_lean_only_searches_inside_rep():
    torso_angles = [
        60,
        10,
        18,
        32,
        25,
        12,
        70,
    ]

    result = calculate_torso_lean(
        torso_angles,
        make_rep(start_index=1, end_index=5),
    )

    assert result.max_lean_index == 3
    assert result.max_lean_angle == pytest.approx(32)


def test_calculate_torso_lean_uses_first_maximum():
    torso_angles = [
        5,
        10,
        30,
        30,
        25,
        12,
    ]

    result = calculate_torso_lean(
        torso_angles,
        make_rep(),
    )

    assert result.max_lean_index == 2


def test_calculate_torso_lean_returns_zero_change():
    torso_angles = [
        5,
        20,
        18,
        15,
        12,
        10,
    ]

    result = calculate_torso_lean(
        torso_angles,
        make_rep(),
    )

    assert result.max_lean_angle == 20
    assert result.lean_change == 0


def test_calculate_torso_lean_raises_for_empty_input():
    with pytest.raises(
        ValueError,
        match="torso_angles list cannot be empty",
    ):
        calculate_torso_lean([], make_rep())


def test_calculate_torso_lean_raises_for_negative_start():
    with pytest.raises(
        ValueError,
        match="rep.start_index cannot be negative",
    ):
        calculate_torso_lean(
            [1, 2, 3],
            make_rep(start_index=-1, end_index=2),
        )


def test_calculate_torso_lean_raises_when_start_after_end():
    with pytest.raises(
        ValueError,
        match="rep.start_index must not be greater than rep.end_index",
    ):
        calculate_torso_lean(
            [1, 2, 3],
            make_rep(start_index=2, end_index=1),
        )


def test_calculate_torso_lean_raises_when_end_out_of_range():
    with pytest.raises(
        ValueError,
        match="rep.end_index is outside torso_angles range",
    ):
        calculate_torso_lean(
            [1, 2, 3],
            make_rep(start_index=0, end_index=3),
        )