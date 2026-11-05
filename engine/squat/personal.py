"""Descriptive personal baselines, never ideal-posture references."""

import math
import json
from pathlib import Path
from statistics import median

from engine.squat.rules import TARGETS


def _finite(value):
    return type(value) in (int, float) and math.isfinite(value)


def validate_context(context):
    required = {'profile_sha256', 'setup_id', 'side', 'facing', 'pipeline_sha256'}
    if not isinstance(context, dict) or set(context) != required:
        raise ValueError('explicit profile, camera/setup, side, facing and pipeline context required')
    if any(not isinstance(value, str) or not value.strip() for value in context.values()):
        raise ValueError('nonempty personal context fields required')
    if context['side'] not in ('left', 'right') or context['facing'] not in ('left', 'right'):
        raise ValueError('explicit side/facing required')
    for name in ('profile_sha256', 'pipeline_sha256'):
        if len(context[name]) != 64 or any(char not in '0123456789abcdef' for char in context[name]):
            raise ValueError('SHA-256 context fingerprints required')


def build_baseline(cards, *, context, source_sha256, reviewer=None):
    """Capture median/range of at least three usable cycles per item.

    Caller supplies source-bound reviewed cards and a reviewed profile context.
    Unknown/missing observations stay in the denominator; only complete coverage
    forms a baseline. The reviewer confirms provenance, not clinical correctness.
    """
    validate_context(context)
    cards = list(cards)
    all_repetitions = {card.repetition for card in cards}
    if not isinstance(source_sha256, str) or len(source_sha256) != 64 or any(c not in '0123456789abcdef' for c in source_sha256):
        raise ValueError('baseline source SHA-256 required')
    if reviewer is not None and (not isinstance(reviewer, str) or not reviewer.strip()):
        raise ValueError('reviewer must be nonempty or null')
    items = []
    for (metric, field), unit in TARGETS.items():
        entries = [card for card in cards if card.metric == metric and card.field == field]
        repetitions = [card.repetition for card in entries]
        if len(repetitions) != len(set(repetitions)):
            raise ValueError('duplicate baseline repetition for metric')
        values = [card.observation for card in entries if card.status == 'observation' and _finite(card.observation)]
        ready = (reviewer is not None and len(values) >= 3 and len(values) == len(entries)
                 and set(repetitions) == all_repetitions)
        items.append(dict(metric=metric, field=field, unit=unit, status='descriptive' if ready else 'review_required',
                          expected=len(all_repetitions), usable=len(values), repetitions=repetitions,
                          median=median(values) if ready else None, minimum=min(values) if ready else None,
                          maximum=max(values) if ready else None))
    return dict(schema_version=1, context=dict(context), source_sha256=source_sha256,
                reviewer=reviewer, items=items, scope='observed preparation cycles, not ideal posture',
                coaching_status='pending_validation')


def compare_baseline(cards, baseline, *, context):
    validate_context(context)
    if baseline.get('schema_version') != 1:
        raise ValueError('unsupported baseline schema')
    validate_context(baseline.get('context'))
    compatible = context == baseline['context']
    items = baseline.get('items', [])
    keys = [(item['metric'], item['field']) for item in items]
    if len(keys) != len(set(keys)):
        raise ValueError('duplicate baseline item')
    if set(keys) != set(TARGETS):
        raise ValueError('baseline must explicitly retain every supported item')
    for item in items:
        if item.get('status') not in ('descriptive', 'review_required'):
            raise ValueError('unsupported baseline item state')
        if item['status'] == 'descriptive':
            values = [item.get(name) for name in ('minimum', 'median', 'maximum')]
            repetitions = item.get('repetitions', [])
            if (not isinstance(baseline.get('reviewer'), str) or not baseline['reviewer'].strip()
                    or not all(_finite(value) for value in values) or not values[0] <= values[1] <= values[2]
                    or item.get('unit') != TARGETS[(item['metric'], item['field'])]
                    or type(item.get('usable')) is not int or item['usable'] < 3
                    or type(item.get('expected')) is not int or item['expected'] != item['usable']
                    or len(repetitions) != item['usable'] or len(set(repetitions)) != len(repetitions)
                    or any(type(number) is not int or number < 1 for number in repetitions)):
                raise ValueError('invalid descriptive baseline evidence')
    comparisons = []
    for card in cards:
        item = next((item for item in items if (item['metric'], item['field']) == (card.metric, card.field)), None)
        status, delta = 'baseline_unavailable', None
        if not compatible:
            status = 'context_mismatch'
        elif card.status != 'observation' or not _finite(card.observation):
            status = 'observation_unavailable'
        elif item and baseline.get('reviewer') and item.get('status') == 'descriptive':
            if item.get('unit') != card.unit:
                raise ValueError('invalid descriptive baseline evidence')
            status, delta = 'descriptive_comparison', card.observation - item['median']
        comparisons.append(dict(repetition=card.repetition, metric=card.metric, field=card.field,
                                status=status, difference_from_preparation_median=delta, unit=card.unit,
                                interpretation='Difference is not a posture error or improvement.'))
    return comparisons


def save_baseline(baseline, path):
    """Persist an explicit draft/reviewed snapshot without overwriting history."""
    compare_baseline([], baseline, context=baseline['context'])
    with Path(path).open('x', encoding='utf-8') as handle:
        json.dump(baseline, handle, indent=2, allow_nan=False)


def load_baseline(path):
    data = json.loads(Path(path).read_text(encoding='utf-8-sig'))
    compare_baseline([], data, context=data['context'])
    return data


def summarize_session(cards):
    """Deduplicate next actions, retain repetition/metric evidence and priority."""
    priorities = {'retake': 0, 'capture_review': 1, 'measurement_review': 2, 'observation': 3}
    groups = {}
    for card in cards:
        key = (card.status, card.action)
        item = groups.setdefault(key, dict(status=card.status, action=card.action, repetitions=set(), evidence=[]))
        item['repetitions'].add(card.repetition)
        item['evidence'].append(dict(repetition=card.repetition, metric=card.metric, field=card.field, reason=card.reason))
    return [
        {**item, 'repetitions': sorted(item['repetitions'])}
        for item in sorted(groups.values(), key=lambda item: priorities[item['status']])]
