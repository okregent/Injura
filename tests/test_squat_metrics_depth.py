import pytest

from engine.squat.metrics.depth import calculate_squat_depth
from engine.squat.phases import SquatPhaseThresholds
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


def make_thresholds(
    standing_y: float = 0.50,
    bottom_y: float = 0.70,
) -> SquatPhaseThresholds:
    return SquatPhaseThresholds(
        standing_y=standing_y,
        bottom_y=bottom_y,
        velocity_threshold=0.01,
    )


def test_calculate_squat_depth_returns_expected_result():
    hip_y_values = [
        0.50,
        0.52,
        0.60,
        0.68,
        0.64,
        0.53,
    ]

    result = calculate_squat_depth(
        hip_y_values=hip_y_values,
        rep=make_rep(),
        thresholds=make_thresholds(),
    )

    assert result.deepest_index == 3
    assert result.deepest_hip_y == pytest.approx(0.68)
    assert result.depth_ratio == pytest.approx(0.90)
    assert result.standing_y == pytest.approx(0.50)
    assert result.bottom_y == pytest.approx(0.70)


def test_calculate_squat_depth_only_searches_inside_rep_range():
    hip_y_values = [
        0.95,
        0.52,
        0.60,
        0.68,
        0.64,
        0.53,
        0.99,
    ]

    result = calculate_squat_depth(
        hip_y_values=hip_y_values,
        rep=make_rep(start_index=1, end_index=5),
        thresholds=make_thresholds(),
    )

    assert result.deepest_index == 3
    assert result.deepest_hip_y == pytest.approx(0.68)


def test_calculate_squat_depth_uses_first_index_when_maximum_is_tied():
    hip_y_values = [
        0.50,
        0.52,
        0.68,
        0.68,
        0.60,
        0.53,
    ]

    result = calculate_squat_depth(
        hip_y_values=hip_y_values,
        rep=make_rep(),
        thresholds=make_thresholds(),
    )

    assert result.deepest_index == 2


def test_calculate_squat_depth_can_return_ratio_above_one():
    hip_y_values = [
        0.50,
        0.52,
        0.60,
        0.75,
        0.64,
        0.53,
    ]

    result = calculate_squat_depth(
        hip_y_values=hip_y_values,
        rep=make_rep(),
        thresholds=make_thresholds(),
    )

    assert result.depth_ratio == pytest.approx(1.25)


def test_calculate_squat_depth_can_return_ratio_below_zero():
    hip_y_values = [
        0.50,
        0.48,
        0.47,
    ]

    result = calculate_squat_depth(
        hip_y_values=hip_y_values,
        rep=make_rep(
            start_index=1,
            bottom_index=1,
            end_index=2,
        ),
        thresholds=make_thresholds(),
    )

    assert result.depth_ratio == pytest.approx(-0.10)


def test_calculate_squat_depth_raises_for_empty_values():
    with pytest.raises(
        ValueError,
        match="hip_y_values list cannot be empty",
    ):
        calculate_squat_depth(
            hip_y_values=[],
            rep=make_rep(),
            thresholds=make_thresholds(),
        )


def test_calculate_squat_depth_raises_for_negative_start_index():
    with pytest.raises(
        ValueError,
        match="rep.start_index cannot be negative",
    ):
        calculate_squat_depth(
            hip_y_values=[0.50, 0.60, 0.70],
            rep=make_rep(start_index=-1, end_index=2),
            thresholds=make_thresholds(),
        )


def test_calculate_squat_depth_raises_when_start_is_after_end():
    with pytest.raises(
        ValueError,
        match="rep.start_index must not be greater than rep.end_index",
    ):
        calculate_squat_depth(
            hip_y_values=[0.50, 0.60, 0.70],
            rep=make_rep(start_index=2, end_index=1),
            thresholds=make_thresholds(),
        )


def test_calculate_squat_depth_raises_when_end_index_is_out_of_range():
    with pytest.raises(
        ValueError,
        match="rep.end_index is outside hip_y_values range",
    ):
        calculate_squat_depth(
            hip_y_values=[0.50, 0.60, 0.70],
            rep=make_rep(start_index=0, end_index=3),
            thresholds=make_thresholds(),
        )


@pytest.mark.parametrize(
    ("standing_y", "bottom_y"),
    [
        (0.50, 0.50),
        (0.70, 0.50),
    ],
)
def test_calculate_squat_depth_raises_for_invalid_movement_range(
    standing_y: float,
    bottom_y: float,
):
    with pytest.raises(
        ValueError,
        match="bottom_y must be greater than standing_y",
    ):
        calculate_squat_depth(
            hip_y_values=[0.50, 0.60, 0.70],
            rep=make_rep(start_index=0, end_index=2),
            thresholds=make_thresholds(
                standing_y=standing_y,
                bottom_y=bottom_y,
            ),
        )