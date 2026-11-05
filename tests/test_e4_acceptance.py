"""Synthetic cross-module acceptance; these fixtures are not accuracy evidence."""

from engine.pose.side import BodySide
from engine.pose.orientation import FacingDirection
from engine.squat.analyzer import SquatAnalyzer
from engine.squat.feedback import build_feedback_cards
from engine.squat.overview import build_session_overview
from engine.squat.personal import compare_baseline, load_baseline
from engine.squat.recording import load_recording_reviews
from engine.validation.dataset import read_json
from tests.test_e3_workflow import three_cycle_extraction
from tests.test_personal_setup import bundle, complete
from tools import personal_setup


def session(root, context):
    manifest = read_json(root / 'manifest.json')
    analysis = SquatAnalyzer().analyze(three_cycle_extraction(), side=BodySide.LEFT,
                                     facing_direction=FacingDirection.LEFT)
    review = load_recording_reviews(root / 'recording-review.json', manifest['preparation_video'])[0]
    cards = build_feedback_cards(analysis, recording_review=review)
    output = personal_setup.build(root, extractor=lambda _: three_cycle_extraction())
    baseline = load_baseline(output / 'baseline.json')
    actual_context = context or read_json(output / 'context.json')
    comparisons = compare_baseline(cards, baseline, context=actual_context)
    return analysis, cards, comparisons


def test_reviewed_personal_setup_flows_to_descriptive_feedback_without_coaching(bundle):
    complete(bundle)
    analysis, cards, comparisons = session(bundle, None)
    overview = build_session_overview(analysis, cards, comparisons=comparisons, baseline_requested=True)
    compared = [item for item in comparisons if item['status'] == 'descriptive_comparison']
    assert compared and all(item['difference_from_preparation_median'] == 0 for item in compared)
    assert overview['personal_comparison_state'] in ('partial_comparison', 'descriptive_comparison')
    assert overview['accuracy_status'] == 'not_validated'
    assert overview['coaching_status'] == 'pending_validation'


def test_new_profile_context_cannot_silently_reuse_old_baseline(bundle):
    complete(bundle)
    context = dict(profile_sha256='d' * 64, pipeline_sha256='b' * 64,
                   side='left', facing='left', setup_id='fixture')
    analysis, cards, comparisons = session(bundle, context)
    overview = build_session_overview(analysis, cards, comparisons=comparisons, baseline_requested=True)
    assert overview['personal_comparison_state'] == 'context_mismatch'
    assert all(item['difference_from_preparation_median'] is None for item in comparisons)


def test_target_capture_review_is_required_even_with_reviewed_baseline(bundle):
    complete(bundle)
    output = personal_setup.build(bundle, extractor=lambda _: three_cycle_extraction())
    baseline = load_baseline(output / 'baseline.json')
    analysis = SquatAnalyzer().analyze(three_cycle_extraction(), side=BodySide.LEFT,
                                     facing_direction=FacingDirection.LEFT)
    cards = build_feedback_cards(analysis)  # Current recording has no review.
    comparisons = compare_baseline(cards, baseline, context=baseline['context'])
    overview = build_session_overview(analysis, cards, comparisons=comparisons, baseline_requested=True)
    assert overview['state'] == 'capture_review'
    assert overview['personal_comparison_state'] == 'comparison_unavailable'
    assert all(item['difference_from_preparation_median'] is None for item in comparisons)
