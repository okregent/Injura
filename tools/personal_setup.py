"""Prepare/check/build a source-bound personal baseline: no implicit review."""

import argparse
import html
import json
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

import cv2

from engine.pose.orientation import FacingDirection
from engine.pose.side import BodySide
from engine.squat.analyzer import SquatAnalyzer
from engine.squat.feedback import build_feedback_cards
from engine.squat.personal import build_baseline, save_baseline
from engine.squat.profile import load_profile, summarize_profile
from engine.squat.recording import RecordingReview, load_recording_reviews, recording_gate
from engine.squat.rules import TARGETS
from engine.validation.dataset import read_json, write_new, sha256, local_path
from tools.profile_measurement import measurement_aid, import_measurement
from tools.evaluate_e3 import extract
from tools.review_samples import personal_pipeline_signature


def prepare(profile_video, preparation_video, output):
    sources = [Path(path).resolve() for path in (profile_video, preparation_video)]
    hashes = [sha256(path) for path in sources]
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    manifest = dict(schema_version=1, profile_video=str(sources[0]), preparation_video=str(sources[1]),
                    profile_source_sha256=hashes[0], preparation_source_sha256=hashes[1],
                    side=None, facing=None, setup_id=None, setup_reviewed=None,
                    same_person_confirmed=None, baseline_reviewer=None)
    profile = dict(schema_version=1, profile_id='draft', source_sha256=hashes[0], source_frame=0,
                   side=None, view=None, reviewer=None, upright=None, camera_level=None,
                   joints_visible=None, body_aligned=None,
                   **{name: dict(pixels=None, uncertainty_pixels=None) for name in ('thigh', 'shank', 'torso')})
    stat = sources[1].stat()
    review = dict(video=sources[1].name, size=stat.st_size, mtime_ns=stat.st_mtime_ns,
                  reviews=[asdict(RecordingReview(side)) for side in ('left', 'right')])
    for name, value in [('manifest.json', manifest), ('profile.json', profile), ('recording-review.json', review)]:
        write_new(output / name, value)
    return status(output)


def decoded_frame_exists(video, number):
    capture = cv2.VideoCapture(str(video))
    try:
        for _ in range(number + 1):
            ok, _ = capture.read()
            if not ok:
                return False
        return True
    finally:
        capture.release()


def check(root):
    root = Path(root)
    manifest = read_json(root / 'manifest.json')
    problems, gates = [], {}
    if manifest.get('schema_version') != 1:
        raise ValueError('unsupported personal setup schema')
    for prefix in ('profile', 'preparation'):
        path = Path(manifest[prefix + '_video'])
        if sha256(path) != manifest[prefix + '_source_sha256']:
            problems.append(prefix + ' source content changed')
    for key in ('setup_reviewed', 'same_person_confirmed'):
        if manifest.get(key) is not True:
            problems.append(key + ' must be explicitly confirmed')
    for key in ('setup_id', 'baseline_reviewer'):
        if not isinstance(manifest.get(key), str) or not manifest[key].strip():
            problems.append(key + ' is missing')
    for key in ('side', 'facing'):
        if manifest.get(key) not in ('left', 'right'):
            problems.append(key + ' must be selected')
    projection = None
    try:
        profile = load_profile(local_path(root, manifest.get('profile_file', 'profile.json')))
        projection = summarize_profile(profile, source_sha256=manifest['profile_source_sha256'])
        if projection['status'] != 'reviewed_projection':
            problems.append('profile capture review incomplete or rejected')
        if profile.side != manifest.get('side'):
            problems.append('profile side differs from preparation side')
        if not decoded_frame_exists(manifest['profile_video'], profile.source_frame):
            problems.append('profile source frame cannot be decoded')
    except (ValueError, TypeError, KeyError) as error:
        problems.append('profile: ' + str(error))
    reviews = load_recording_reviews(root / 'recording-review.json', manifest['preparation_video'])
    if manifest.get('side') in ('left', 'right'):
        side = BodySide(manifest['side'])
        review = next((item for item in reviews if item.side == side.value), None)
        gates = {metric: dict(zip(('status', 'reason'), recording_gate(metric, review, side))) for metric, _ in TARGETS}
        if not any(item['status'] == 'approved' for item in gates.values()):
            problems.append('no preparation metric has approved recording conditions')
    return dict(schema_version=1, ready=not problems, problems=problems, recording_gates=gates,
                profile=projection, scope='descriptive preparation only; coaching remains pending')


def status(root):
    root = Path(root)
    try:
        report = check(root)
    except (OSError, ValueError, TypeError, KeyError) as error:
        report = dict(ready=False, problems=[str(error)])
    selected_profile = 'profile.json'
    try:
        manifest = read_json(root / 'manifest.json')
        selected_profile = local_path(root, manifest.get('profile_file', 'profile.json')).relative_to(root.resolve()).as_posix()
    except (OSError, ValueError, TypeError, KeyError):
        pass
    report['baseline_snapshots'] = []
    for path in sorted(root.glob('runs/*/baseline.json')):
        baseline = read_json(path)
        report['baseline_snapshots'].append(dict(path=path.relative_to(root).as_posix(),
            descriptive_items=sum(item['status'] == 'descriptive' for item in baseline['items']),
            pending_items=sum(item['status'] != 'descriptive' for item in baseline['items'])))
    # Status is a replaceable view; all baseline/evidence snapshots are new files.
    (root / 'status.json').write_text(json.dumps(report, indent=2, allow_nan=False), encoding='utf-8')
    page = ('<!doctype html><html lang="en"><meta charset="utf-8"><title>Personal setup readiness</title>'
            '<style>body{font:16px system-ui;max-width:950px;margin:30px auto;line-height:1.6}pre{white-space:pre-wrap}</style>'
            '<h1>Personal setup readiness</h1><p>No automatic profile approval or coaching activation.</p>'
            '<p><a href="manifest.json">Setup assertions</a> · <a href="' + html.escape(selected_profile, quote=True) + '">Profile draft</a> · '
            '<a href="recording-review.json">Capture review</a></p>'
            + ''.join('<p><a href="' + html.escape(path.relative_to(root).as_posix(), quote=True)
                      + '">Original-frame measurement aid</a></p>' for path in sorted(root.glob('measurement-*/index.html')))
            + ''.join('<p><a href="' + html.escape(item['path'], quote=True) + '">Baseline snapshot</a>: '
                      + str(item['descriptive_items']) + ' descriptive items, ' + str(item['pending_items']) + ' pending.</p>'
                      for item in report['baseline_snapshots']) + '<pre>'
            + html.escape(json.dumps(report, indent=2)) + '</pre></html>')
    (root / 'index.html').write_text(page, encoding='utf-8')
    return root / 'index.html'


def build(root, extractor=extract):
    root = Path(root)
    readiness = check(root)
    if not readiness['ready']:
        raise ValueError('setup is not ready: ' + '; '.join(readiness['problems']))
    manifest = read_json(root / 'manifest.json')
    profile_file = local_path(root, manifest.get('profile_file', 'profile.json'))
    bound = [root / 'manifest.json', profile_file, root / 'recording-review.json']
    before = {str(path): sha256(path) for path in bound}
    manifest = read_json(root / 'manifest.json')
    signature = personal_pipeline_signature()
    side = BodySide(manifest['side'])
    reviews = load_recording_reviews(root / 'recording-review.json', manifest['preparation_video'])
    review = next(item for item in reviews if item.side == side.value)
    extraction = extractor(Path(manifest['preparation_video']))
    analysis = SquatAnalyzer().analyze(extraction, side=side, facing_direction=FacingDirection(manifest['facing']))
    cards = build_feedback_cards(analysis, recording_review=review)
    context = dict(profile_sha256=before[str(profile_file)], setup_id=manifest['setup_id'],
                   side=side.value, facing=manifest['facing'], pipeline_sha256=signature)
    baseline = build_baseline(cards, context=context, source_sha256=manifest['preparation_source_sha256'],
                              reviewer=manifest['baseline_reviewer'])
    if any(sha256(path) != digest for path, digest in before.items()) or personal_pipeline_signature() != signature:
        raise ValueError('setup files or runtime changed during inference')
    if not check(root)['ready']:
        raise ValueError('source or setup changed during inference')
    output = root / 'runs' / datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    output.mkdir(parents=True, exist_ok=False)
    save_baseline(baseline, output / 'baseline.json')
    write_new(output / 'context.json', context)
    write_new(output / 'evidence.json', dict(inputs_sha256=before, preparation_source_sha256=baseline['source_sha256'],
              profile_source_sha256=manifest['profile_source_sha256'], cards=[asdict(card) for card in cards],
              complete_cycles=len(analysis.repetitions), excluded_candidates=len(analysis.candidates),
              descriptive_items=sum(item['status'] == 'descriptive' for item in baseline['items'])))
    status(root)
    return output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    draft = commands.add_parser('prepare')
    draft.add_argument('profile_video', type=Path)
    draft.add_argument('preparation_video', type=Path)
    draft.add_argument('--output', type=Path, required=True)
    for name in ('check', 'status', 'build'):
        commands.add_parser(name).add_argument('root', type=Path)
    aid = commands.add_parser('measure')
    aid.add_argument('root', type=Path)
    aid.add_argument('--frame', type=int, default=0)
    importer = commands.add_parser('import-measurement')
    importer.add_argument('root', type=Path)
    importer.add_argument('draft', type=Path)
    args = parser.parse_args()
    try:
        if args.command == 'prepare':
            print(prepare(args.profile_video, args.preparation_video, args.output).resolve())
        elif args.command == 'check':
            result = check(args.root)
            print(json.dumps(result, indent=2))
            return 0 if result['ready'] else 2
        elif args.command == 'measure':
            print(measurement_aid(args.root, args.frame).resolve())
            status(args.root)
        elif args.command == 'import-measurement':
            print(import_measurement(args.root, args.draft).resolve())
            status(args.root)
        else:
            print((build(args.root) if args.command == 'build' else status(args.root)).resolve())
    except (OSError, ValueError, KeyError, TypeError) as error:
        parser.error(str(error))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
