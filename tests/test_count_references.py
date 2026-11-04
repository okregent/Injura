import pytest

from tools.evaluate_counts import reference_range


def test_uncertain_reported_count_remains_a_range():
    assert reference_range({"actual_reps": "", "reported_min_reps": "6", "reported_max_reps": "7"}) == (6, 7)


def test_explicit_count_is_not_replaced_by_candidate_count():
    assert reference_range({"actual_reps": "3"}) == (3, 3)


def test_unfilled_reference_is_not_invented():
    assert reference_range({"actual_reps": ""}) is None


@pytest.mark.parametrize("row", [{"actual_reps": "-1"}, {"reported_min_reps": "7", "reported_max_reps": "6"}])
def test_invalid_reference_is_rejected(row):
    with pytest.raises(ValueError, match="nonnegative ordered range"):
        reference_range(row)
