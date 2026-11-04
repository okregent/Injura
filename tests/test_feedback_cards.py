from dataclasses import replace

from engine.squat.feedback import build_feedback_cards
from tests.test_measurement_rules import APPROVED
from tests.test_squat_remaining_metrics import analyze


def test_unknown_capture_requests_review_without_assuming_retake():
    cards = build_feedback_cards(analyze())
    assert cards and all(card.status == 'capture_review' for card in cards)
    assert all(card.observation is None for card in cards)


def test_rejected_capture_requests_retake_and_withholds_values():
    cards = build_feedback_cards(analyze(), recording_review=replace(APPROVED, side_view=False))
    assert all(card.status == 'retake' and card.observation is None for card in cards)


def test_reviewed_measurement_is_observation_never_correction():
    result = analyze()
    before = result.repetitions[0].metrics['knee_flexion'].value
    cards = build_feedback_cards(result, recording_review=APPROVED)
    knee = next(card for card in cards if card.metric == 'knee_flexion')
    assert knee.status == 'observation' and knee.observation == before
    assert all(card.coaching_status == 'pending_validation' for card in cards)
    assert result.repetitions[0].metrics['knee_flexion'].value == before


def test_invalid_measurement_never_shown_as_usable():
    result = analyze()
    result.repetitions[0].metrics['knee_flexion'].value = float('nan')
    knee = next(card for card in build_feedback_cards(result, recording_review=APPROVED) if card.metric == 'knee_flexion')
    assert knee.status == 'measurement_review' and knee.observation is None


def test_empty_cycles_produce_no_measurement_cards():
    result = analyze()
    result.repetitions.clear()
    assert build_feedback_cards(result) == []
