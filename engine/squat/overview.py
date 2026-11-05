"""Conservative session presentation state, separate from posture judgment."""

from engine.squat.personal import summarize_session


def build_session_overview(analysis, cards, *, comparisons=(), baseline_requested=False):
    cards, comparisons = list(cards), list(comparisons)
    statuses = ('retake', 'capture_review', 'measurement_review', 'observation')
    counts = {status: 0 for status in statuses}
    keys = set()
    for card in cards:
        key = (card.repetition, card.metric, card.field)
        if key in keys or card.status not in counts or type(card.repetition) is not int or not 1 <= card.repetition <= len(analysis.repetitions):
            raise ValueError('invalid or duplicate session measurement card')
        keys.add(key)
        counts[card.status] += 1
    if not analysis.repetitions:
        state, action = 'no_complete_cycles', 'Review the source video and detected gaps before interpreting measurements.'
    elif not cards:
        state, action = 'measurement_review', 'No measurement cards are available; inspect the analysis evidence.'
    else:
        state = next(status for status in statuses if counts[status])
        action = summarize_session(cards)[0]['action']
    allowed = ('context_mismatch', 'observation_unavailable', 'baseline_unavailable', 'descriptive_comparison')
    comparison_counts = {status: 0 for status in allowed}
    compared_keys = set()
    by_key = {(card.repetition, card.metric, card.field): card for card in cards}
    for comparison in comparisons:
        key = (comparison['repetition'], comparison['metric'], comparison['field'])
        status = comparison['status']
        if key not in keys or key in compared_keys or status not in comparison_counts:
            raise ValueError('invalid personal comparison evidence')
        if status == 'descriptive_comparison' and by_key[key].status != 'observation':
            raise ValueError('withheld measurement cannot have a descriptive comparison')
        compared_keys.add(key)
        comparison_counts[status] += 1
    if not baseline_requested:
        if comparisons:
            raise ValueError('personal comparisons require an explicit baseline request')
        personal_state = 'not_requested'
    elif not cards:
        personal_state = 'no_observations'
    elif not comparisons:
        personal_state = 'comparison_unavailable'
    elif comparison_counts['context_mismatch']:
        personal_state = 'context_mismatch'
    elif comparison_counts['descriptive_comparison'] == len(cards):
        personal_state = 'descriptive_comparison'
    elif comparison_counts['descriptive_comparison']:
        personal_state = 'partial_comparison'
    else:
        personal_state = 'comparison_unavailable'
    return dict(schema_version=1, state=state, primary_action=action,
                detected_cycles=len(analysis.repetitions), excluded_candidates=len(analysis.candidates),
                measurement_card_counts=counts, personal_comparison_state=personal_state,
                personal_comparison_counts=comparison_counts,
                accuracy_status='not_validated', coaching_status='pending_validation',
                scope='Measurement availability and descriptive differences only; no posture score or injury-risk judgment.')
