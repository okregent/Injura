import math

import pytest

from engine.pose.types import Landmark
from engine.squat.quality import is_usable_landmark, valid_frame_ratio


def make_landmark(
    visibility: float = 1.0,
    x: float = 0.5,
) -> Landmark:
    return Landmark(x=x, y=0.5, z=0.0, visibility=visibility)


def test_is_usable_landmark_accepts_visible_finite_landmark():
    assert is_usable_landmark(make_landmark(), visibility_threshold=0.5)


def test_is_usable_landmark_rejects_low_visibility():
    assert not is_usable_landmark(
        make_landmark(visibility=0.49),
        visibility_threshold=0.5,
    )


def test_is_usable_landmark_rejects_non_finite_coordinate():
    assert not is_usable_landmark(make_landmark(x=math.nan))


@pytest.mark.parametrize("threshold", [-0.1, 1.1])
def test_is_usable_landmark_rejects_invalid_threshold(threshold):
    with pytest.raises(ValueError, match="between 0 and 1"):
        is_usable_landmark(make_landmark(), threshold)


def test_valid_frame_ratio():
    assert valid_frame_ratio([True, False, True, True]) == pytest.approx(0.75)


def test_valid_frame_ratio_returns_zero_for_empty_mask():
    assert valid_frame_ratio([]) == 0.0
