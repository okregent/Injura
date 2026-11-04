"""Prepare/check/freeze/run local E3 evaluation; no implicit reference approval."""

import argparse
import html
import json
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

from engine.pose.mediapipe_estimator import MediaPipePoseEstimator
from engine.pose.orientation import FacingDirection
from engine.pose.side import BodySide
from engine.squat.analyzer import SquatAnalyzer
from engine.squat.metrics.normalized_knee_travel import KneeTravelRecordingConditions
from engine.squat.recording import load_recording_reviews, recording_gate, REQUIREMENTS
from engine.validation.dataset import (prepare, register, check, freeze, verify_frozen, read_json,
    write_new, local_path, sha256, analysis_fingerprint, evaluation_fingerprint, environment_signature)
from engine.validation.scoring import score_compliant, score_violation, decision
from engine.validation.aids import prepare_aids
from engine.validation.handoff import build_handoff, scaffold_reference


def extract(video):
    estimator = MediaPipePoseEstimator(model_complexity=1)
    try:
        return estimator.extract_with_metadata(str(video))
    finally:
        estimator.close()


def runtime_provenance():
    return dict(environment=environment_signature(), analysis_fingerprint=analysis_fingerprint(),
                evaluation_fingerprint=evaluation_fingerprint())


def raw_summary(analysis, extraction):
    source = extraction.source_frame_indices
    return dict(source_frames=extraction.source_frame_count, pose_frames=len(source), fps=extraction.fps,
                source_frame_indices=source, recovered_frame_indices=extraction.recovered_frame_indices,
                calibration=analysis.calibration_method, issues=analysis.issues,
                repetitions=[dict(start_source=source[item.rep.start_index], end_source=source[item.rep.end_index],
                                  metrics={name: asdict(outcome) for name, outcome in item.metrics.items()})
                             for item in analysis.repetitions],
                candidates=[dict(start_source=source[item.rep.start_index], end_source=source[item.rep.end_index],
                                 observed_bottom_source=source[item.deepest_observed_index],
                                 missing_source_frames=item.missing_source_frames) for item in analysis.candidates],
                consistency={name: asdict(value) for name, value in analysis.consistency.items()})


def render_report(result):
    parts = ['<!doctype html><html lang="en"><meta charset="utf-8"><title>E3 evaluation</title>',
             '<style>body{font:16px system-ui;margin:28px;line-height:1.6}table{border-collapse:collapse}td,th{padding:9px;border:1px solid #ccd}pre{white-space:pre-wrap}.note{padding:14px;background:#fff2cf}</style>',
             '<h1>E3 evaluation workflow</h1>',
             '<p class="note">Engineering measurement checks only. No posture grade, medical inference, '
             'injury-prevention efficacy or independent accuracy claim follows from a smoke run. '
             'Missing inputs remain not evaluated. Physical phase/heel-duration events remain restricted.</p>',
             f'<p>Run kind: <b>{html.escape(result["kind"])}</b> · Primary outcome: <b>{result["status"]}</b></p>',
             '<p><a href="results.json">Full evidence JSON</a></p>',
             '<table><tr><th>Clip</th><th>Case</th><th>Measured cycles</th><th>Candidates</th><th>Decision</th></tr>']
    for clip in result['clips']:
        parts.append('<tr>' + ''.join(f'<td>{html.escape(str(value))}</td>' for value in
                    (clip['id'], clip['case'], len(clip['raw']['repetitions']), len(clip['raw']['candidates']), clip['evaluation']['status'])) + '</tr>')
    parts.append('</table>')
    for clip in result['clips']:
        parts.append(f'<details><summary>{html.escape(clip["id"])}: metric evidence and exclusions</summary><pre>'
                     + html.escape(json.dumps(clip['evaluation'], indent=2, ensure_ascii=False)) + '</pre></details>')
    parts.append('</html>')
    return '\n'.join(parts)


def build_status(collection):
    collection = Path(collection)
    collection.mkdir(parents=True, exist_ok=True)
    rows = []
    for path in sorted(collection.glob('*/manifest.json')):
        root = path.parent
        try:
            report = check(root)
        except (OSError, ValueError, KeyError, TypeError) as error:
            report = dict(ready=False, problems=[str(error)], clips=[])
        runs = sorted(root.glob('runs/*/results.json'))
        latest = read_json(runs[-1]) if runs else None
        link = (runs[-1].parent / 'index.html').relative_to(collection).as_posix() if runs else None
        aids = sorted(root.glob('reference-aids*/index.html'))
        rows.append(dict(bundle=root.name, ready=report['ready'], frozen=(root / 'freeze.json').exists(),
                         check=report, latest_kind=latest['kind'] if latest else None,
                         latest_decision=latest['status'] if latest else 'not_evaluated', latest_link=link,
                         aids_link=aids[-1].relative_to(collection).as_posix() if aids else None))
    parts = ['<!doctype html><meta charset="utf-8"><title>E3 readiness</title>',
             '<style>body{font:16px system-ui;margin:28px;line-height:1.6}td,th{border:1px solid #ccd;padding:9px}table{border-collapse:collapse}pre{white-space:pre-wrap}</style>',
             '<h1>E3 validation readiness</h1><p>Registration and smoke checks do not establish accuracy. '
             'No pending input or unsigned reference counts as a pass. Frozen inputs must still verify before a primary run.</p>',
             '<p><a href="../sample-review/index.html">Sample review dashboard</a></p>',
             '<table><tr><th>Bundle</th><th>Inputs ready</th><th>Freeze present</th><th>Latest run kind</th><th>Latest decision</th><th>Evidence</th></tr>']
    for row in rows:
        links = []
        for label, field in [('Run report', 'latest_link'), ('Blind frame viewer', 'aids_link')]:
            if row[field]:
                links.append(f'<a href="{html.escape(row[field], quote=True)}">{label}</a>')
        parts.append('<tr>' + ''.join('<td>' + html.escape(str(row[field])) + '</td>'
                     for field in ('bundle', 'ready', 'frozen', 'latest_kind', 'latest_decision'))
                     + '<td>' + ' | '.join(links) + '</td></tr>')
    parts.append('</table>')
    for row in rows:
        parts.append('<details><summary>' + html.escape(row['bundle']) + ': missing inputs</summary><pre>'
                     + html.escape(json.dumps(row['check'], indent=2)) + '</pre></details>')
    parts.append('<p>Commands: prepare → register additional sources if needed → aids → complete review/references → check → freeze → run. '
                 'Development-only wiring checks use run --development-smoke and always remain not_evaluated.</p>')
    (collection / 'index.html').write_text('\n'.join(parts), encoding='utf-8')
    (collection / 'status.json').write_text(json.dumps(rows, indent=2, allow_nan=False), encoding='utf-8')
    return collection / 'index.html'


def run(root, *, smoke=False, extractor=extract):
    root = Path(root)
    if smoke and (root / 'freeze.json').exists():
        raise ValueError('development smoke cannot be run on a frozen evaluation bundle')
    manifest = read_json(root / 'manifest.json') if smoke else verify_frozen(root)
    limits = read_json(root / 'limits.json')
    check_report = check(root)
    timestamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    output = root / 'runs' / timestamp
    output.mkdir(parents=True, exist_ok=False)
    result = dict(schema_version=1, kind='development_smoke' if smoke else 'frozen_primary_evaluation',
                  status='not_evaluated', created_utc=timestamp, protocol=manifest['protocol_version'],
                  dataset_check=check_report, runtime=runtime_provenance(),
                  manifest_sha256=sha256(root / 'manifest.json'), limits_sha256=sha256(root / 'limits.json'), clips=[])
    for entry in manifest['clips']:
        video = Path(entry['video'])
        if sha256(video) != entry['sha256']:
            raise ValueError(f'source content changed: {entry["id"]}')
        side = BodySide(entry['side']) if entry.get('side') in ('left', 'right') else None
        facing = FacingDirection(entry['facing']) if entry.get('facing') in ('left', 'right') else None
        if side is None or facing is None:
            raise ValueError('select side and facing explicitly before inference, including smoke runs')
        reviews = load_recording_reviews(local_path(root, entry['recording_review']), video)
        review = next((item for item in reviews if item.side == side.value), None)
        extraction = extractor(video)
        analysis = SquatAnalyzer().analyze(extraction, side=side, facing_direction=facing,
                    recording_conditions=KneeTravelRecordingConditions(side_view=review.side_view,
                        foot_side_on=review.foot_side_on) if review and review.reviewer else None,
                    visibility_threshold=.5, phase_min_duration=3, candidate_max_gap_seconds=.2,
                    use_posture_calibration=False, use_robust_fallback=False)
        reference = read_json(local_path(root, entry['reference']))
        if smoke:
            evaluation = dict(status='not_evaluated', reason='development smoke never establishes held-out acceptance',
                              recording_gates={name: dict(zip(('status', 'reason'), recording_gate(name, review, side))) for name in REQUIREMENTS})
        else:
            if any(rep['end_source'] >= extraction.source_frame_count for rep in reference.get('repetitions', [])):
                raise ValueError('reference boundary exceeds decoded source')
            if any(item['source_frame'] >= extraction.source_frame_count for item in reference.get('frame_measurements', [])):
                raise ValueError('reference frame exceeds decoded source')
            evaluation = (score_compliant(analysis, extraction, reference, review, limits) if entry['case'] == 'compliant'
                          else score_violation(analysis, review, entry['expected_affected_items'], entry['expected_unaffected_items']))
        result['clips'].append(dict(id=entry['id'], case=entry['case'], source_sha256=entry['sha256'],
                                   side=side.value, facing=facing.value, raw=raw_summary(analysis, extraction), evaluation=evaluation))
        print(json.dumps(dict(clip=entry['id'], detected=len(analysis.repetitions), candidates=len(analysis.candidates),
                              decision=evaluation['status'])), flush=True)
        if sha256(video) != entry['sha256']:
            raise ValueError('source changed during inference')
    if not smoke:
        verify_frozen(root)
        result['status'] = decision(clip['evaluation']['status'] for clip in result['clips'])
    write_new(output / 'results.json', result)
    (output / 'index.html').write_text(render_report(result), encoding='utf-8')
    return output / 'index.html'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    preparer = commands.add_parser('prepare')
    preparer.add_argument('videos', type=Path, nargs='+')
    preparer.add_argument('--output', type=Path, required=True)
    registrar = commands.add_parser('register')
    registrar.add_argument('root', type=Path)
    registrar.add_argument('videos', type=Path, nargs='+')
    scaffolder = commands.add_parser('reference-scaffold')
    scaffolder.add_argument('reference', type=Path)
    scaffolder.add_argument('--output', type=Path, required=True)
    for command in ('check', 'freeze', 'run', 'aids', 'status', 'handoff'):
        item = commands.add_parser(command)
        item.add_argument('root', type=Path)
        if command == 'run':
            item.add_argument('--development-smoke', action='store_true', help='Never reports acceptance or uses reference labels as truth')
    args = parser.parse_args()
    try:
        if args.command == 'prepare':
            print(prepare(args.videos, args.output).resolve())
        elif args.command == 'register':
            print(register(args.videos, args.root).resolve())
        elif args.command == 'reference-scaffold':
            print(scaffold_reference(args.reference, args.output).resolve())
        elif args.command == 'check':
            report = check(args.root)
            print(json.dumps(report, indent=2))
            return 0 if report['ready'] else 2
        elif args.command == 'freeze':
            print(freeze(args.root).resolve())
        elif args.command == 'aids':
            print(prepare_aids(args.root).resolve())
        elif args.command == 'status':
            print(build_status(args.root).resolve())
        elif args.command == 'handoff':
            print(build_handoff(args.root).resolve())
        else:
            print(run(args.root, smoke=args.development_smoke).resolve())
    except (OSError, ValueError, KeyError, TypeError) as error:
        parser.error(str(error))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
