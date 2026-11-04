"""Read-only evaluation triage and an explicitly unapproved E4 review packet."""

import html
import json
from datetime import datetime, timezone
from pathlib import Path

from engine.validation.dataset import METRICS, FRAME_METRICS, reference_positions, read_json, sha256, write_new
from engine.validation.scoring import decision


MEASURES = ('complete_repetitions', 'start_boundary', 'end_boundary',
            'deepest_observed_frame', 'total_duration', *METRICS, 'consistency',
            'phase_duration_arithmetic')
CASES = ('wrong_view', 'required_joint_occlusion', 'timing_discontinuity_or_unknown_cadence')


def scaffold_reference(reference_path, output_path):
    """Expand manually marked events into empty slots without inventing values."""
    reference_path, output_path = Path(reference_path), Path(output_path)
    reference = read_json(reference_path)
    if reference.get('schema_version') != 1 or not reference.get('source_sha256'):
        raise ValueError('source-bound schema version 1 reference required')
    reps = reference.get('repetitions', [])
    previous = -1
    for rep in reps:
        start, end = rep['start_source'], rep['end_source']
        low, high = rep['deepest_interval']
        if (any(type(value) is not int for value in (start, end, low, high))
                or not previous < start < low <= high < end or start < 1):
            raise ValueError('mark chronological, nonoverlapping source-frame events first')
        previous = end
        rep.setdefault('uncertainty_frames', None)
        metrics = rep.setdefault('metrics', {})
        for name in METRICS:
            metrics.setdefault(name, dict(value=None, uncertainty=None))
    if len(reps) < 3:
        raise ValueError('mark at least three complete repetitions first')
    positions = reference_positions(reps)
    if len(set(positions)) != 10:
        raise ValueError('events do not provide ten distinct reference positions')
    frames = reference.setdefault('frame_measurements', [])
    existing = {(item['metric'], item['source_frame']) for item in frames}
    for metric in FRAME_METRICS:
        for position in positions:
            if (metric, position) not in existing:
                frames.append(dict(metric=metric, source_frame=position, value=None, uncertainty=None))
    reference['confirmed'] = False
    reference['reviewer'] = None
    reference['origin'] = None
    write_new(output_path, reference)
    return output_path


def summarize(result):
    """Never infer acceptance from totals, a smoke run, or absent evidence."""
    if result.get('schema_version') != 1:
        raise ValueError('unsupported results schema')
    primary = result.get('kind') == 'frozen_primary_evaluation'
    clips = result.get('clips', [])
    if not isinstance(clips, list) or any(not isinstance(clip, dict) for clip in clips):
        raise ValueError('invalid result clips')
    ids = [clip['id'] for clip in clips]
    if len(ids) != len(set(ids)):
        raise ValueError('duplicate result clip ids')
    compliant = [clip for clip in clips if clip.get('case') == 'compliant']
    items, actions = {}, []
    for name in MEASURES:
        evidence = []
        for clip in compliant:
            item = clip.get('evaluation', {}).get('metrics', {}).get(name, {})
            status = item.get('status', 'not_evaluated')
            decision([status])  # Reject malformed decisions even in development data.
            evidence.append(dict(clip=clip['id'], status=status, details=item))
            if status != 'pass':
                actions.append(dict(clip=clip['id'], item=name, status=status,
                                    action='Review missing references, excluded observations and signed errors; investigate before changing limits.'))
        status = decision(item['status'] for item in evidence)
        if not primary or len(compliant) < 3:
            status = 'not_evaluated'
        items[name] = dict(status=status, evidence=evidence)
    violations = {}
    for case in CASES:
        entries = [dict(clip=clip['id'], evaluation=clip.get('evaluation', {}))
                   for clip in clips if clip.get('case') == case]
        status = decision(entry['evaluation'].get('status', 'not_evaluated') for entry in entries)
        violations[case] = dict(status=status if primary else 'not_evaluated', evidence=entries)
        if not entries or status != 'pass':
            actions.append(dict(clip=None, item=case, status='not_evaluated' if not entries else status,
                                action='Review the signed capture conditions and affected/unaffected item isolation.'))
    prerequisites = []
    if not primary:
        prerequisites.append('A development smoke run cannot establish measurement acceptance.')
    if result.get('dataset_check', {}).get('ready') is not True:
        prerequisites.append('Dataset eligibility is incomplete.')
    if len(compliant) < 3:
        prerequisites.append('At least three compliant clips are required; participant diversity is checked by dataset eligibility.')
    if result.get('status') != 'pass':
        prerequisites.append('The complete primary evaluation has not passed.')
    metric_status = decision(item['status'] for item in items.values())
    violation_status = decision(item['status'] for item in violations.values())
    eligible = not prerequisites and metric_status == 'pass' and violation_status == 'pass'
    return dict(schema_version=1, kind='e4_review_draft', measurement_items=items,
                capture_cases=violations, actions=actions, blockers=prerequisites,
                eligible_for_human_measurement_review=eligible,
                measurement_approval='pending', coaching_approval='pending',
                enabled_rules=[], reviewer=None,
                required_signoffs=[
                    'Verify the frozen bundle, source provenance, independent references and runtime hashes.',
                    'Review per-item failures, coverage, uncertainty and the limited participant/camera scope.',
                    'Specify each proposed feedback threshold, rationale, applicable population and wording separately.',
                    'Validate feedback behavior on independent cases before product activation.'],
                restrictions=['This packet is a review aid, not runtime authorization.',
                              'No clinical injury-prevention efficacy follows from measurement checks.',
                              'Physical phase duration and heel-rise duration remain unvalidated.',
                              'Phase arithmetic acceptance does not validate phase-event semantics.'])


def build_handoff(results_path):
    """Create a fresh immutable snapshot beside a run; never modify its evidence."""
    results_path = Path(results_path).resolve()
    before = sha256(results_path)
    packet = summarize(read_json(results_path))
    packet['source'] = dict(results_path=str(results_path), sha256=before)
    packet['created_utc'] = datetime.now(timezone.utc).isoformat()
    if sha256(results_path) != before:
        raise ValueError('results changed while preparing handoff')
    output = results_path.parent / ('handoff-' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'))
    output.mkdir(exist_ok=False)
    write_new(output / 'review.json', packet)
    rows = ''.join('<tr><td>' + html.escape(name) + '</td><td>' + item['status'] + '</td></tr>'
                   for name, item in packet['measurement_items'].items())
    page = ('<!doctype html><html lang="en"><meta charset="utf-8"><title>E4 review draft</title>'
            '<style>body{font:16px system-ui;max-width:1100px;margin:30px auto;line-height:1.6}'
            'td,th{padding:8px;border:1px solid #ccc}table{border-collapse:collapse}pre{white-space:pre-wrap}</style>'
            '<h1>E4 review draft</h1><p>Measurement approval: pending. Coaching approval: pending. No rules enabled.</p>'
            '<p><a href="review.json">Evidence and review checklist</a></p>'
            '<table><tr><th>Measurement item</th><th>Evidence status</th></tr>' + rows + '</table><pre>'
            + html.escape(json.dumps(packet, indent=2, ensure_ascii=False)) + '</pre></html>')
    (output / 'index.html').write_text(page, encoding='utf-8')
    return output / 'index.html'
