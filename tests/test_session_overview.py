from dataclasses import replace

import pytest

from engine.squat.feedback import build_feedback_cards
from engine.squat.overview import build_session_overview
from tests.test_squat_remaining_metrics import analyze
from tests.test_measurement_rules import APPROVED


def test_unknown_capture_summary_never_claims_accuracy_or_coaching_ready():
    analysis = analyze()
    result = build_session_overview(analysis, build_feedback_cards(analysis))
    assert result['state'] == 'capture_review'
    assert result['accuracy_status'] == 'not_validated'
    assert result['coaching_status'] == 'pending_validation'
    assert result['personal_comparison_state'] == 'not_requested'


def test_no_cycles_no_cards_and_candidates_remain_separate():
    analysis = analyze()
    analysis.repetitions.clear()
    analysis.candidates.append(object())
    result = build_session_overview(analysis, [], baseline_requested=True)
    assert result['state'] == 'no_complete_cycles'
    assert result['detected_cycles'] == 0 and result['excluded_candidates'] == 1
    assert result['personal_comparison_state'] == 'no_observations'


def test_missing_cards_request_review():
    result = build_session_overview(analyze(), [])
    assert result['state'] == 'measurement_review'


def test_retake_prioritized_without_removing_other_evidence():
    analysis = analyze()
    cards = build_feedback_cards(analysis)
    cards[0] = replace(cards[0], status='retake', action='Record again.')
    result = build_session_overview(analysis, cards)
    assert result['state'] == 'retake' and result['primary_action'] == 'Record again.'
    assert sum(result['measurement_card_counts'].values()) == len(cards)


def comparison(card, status):
    return dict(repetition=card.repetition, metric=card.metric, field=card.field, status=status)


@pytest.mark.parametrize('mode,expected', [('all', 'descriptive_comparison'), ('partial', 'partial_comparison'),
                                         ('mismatch', 'context_mismatch'), ('missing', 'comparison_unavailable')])
def test_personal_summary_requires_actual_comparison_coverage(mode, expected):
    analysis = analyze()
    cards = [card for card in build_feedback_cards(analysis, recording_review=APPROVED) if card.status == 'observation']
    comparisons = [comparison(card, 'descriptive_comparison') for card in cards]
    if mode == 'partial':
        comparisons = comparisons[:1]
    elif mode == 'mismatch':
        comparisons[0]['status'] = 'context_mismatch'
    elif mode == 'missing':
        comparisons = []
    result = build_session_overview(analysis, cards, comparisons=comparisons, baseline_requested=True)
    assert result['personal_comparison_state'] == expected


def test_unrequested_or_duplicate_or_withheld_comparisons_rejected():
    analysis = analyze()
    cards = build_feedback_cards(analysis)
    value = comparison(cards[0], 'descriptive_comparison')
    with pytest.raises(ValueError):
        build_session_overview(analysis, cards, comparisons=[value], baseline_requested=True)
    value['status'] = 'observation_unavailable'
    with pytest.raises(ValueError):
        build_session_overview(analysis, cards, comparisons=[value])
    with pytest.raises(ValueError):
        build_session_overview(analysis, cards, comparisons=[value, value], baseline_requested=True)


def test_duplicate_or_out_of_range_cards_rejected():
    analysis = analyze()
    cards = build_feedback_cards(analysis)
    with pytest.raises(ValueError):
        build_session_overview(analysis, cards + [cards[0]])
    with pytest.raises(ValueError):
        build_session_overview(analysis, [replace(cards[0], repetition=99)])
