"""Prepare and freeze local evaluation inputs without inventing references."""

import hashlib
import json
import math
import platform
import uuid
from importlib.metadata import version, PackageNotFoundError
from dataclasses import asdict
from pathlib import Path

from engine.pose.side import BodySide
from engine.squat.recording import RecordingReview, load_recording_reviews, recording_gate


PROJECT = Path(__file__).resolve().parents[2]
PROTOCOL = PROJECT / 'docs/validation/e3-limits-v0.1.json'
INVENTORY = PROJECT / 'docs/validation/e3-manifest-v0.1.json'
CASES = ('compliant', 'wrong_view', 'required_joint_occlusion', 'timing_discontinuity_or_unknown_cadence')
METRICS = {
    'knee_flexion': ('knee_flexion', None), 'hip_flexion': ('hip_flexion', None),
    'torso_lean': ('torso_lean', 'max_lean_angle'),
    'relative_descent': ('depth', 'depth_ratio'), 'hip_to_knee_gap': ('hip_to_knee', 'vertical_gap'),
    'raw_knee_travel': ('knee_travel', 'max_travel'),
    'foot_normalized_knee_travel': ('normalized_knee_travel', 'normalized_travel'),
    'heel_rise_magnitude': ('heel_lift', 'max_lift'),
}
FRAME_METRICS = ('knee_flexion', 'hip_flexion', 'torso_lean')


def _reject_nonfinite(value):
    raise ValueError(f'nonfinite JSON: {value}')


def read_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'), parse_constant=_reject_nonfinite)


def write_new(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf-8') as handle:
        json.dump(data, handle, indent=2, allow_nan=False)
        handle.write('\n')


def sha256(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def analysis_fingerprint():
    paths = list((PROJECT / 'engine/pose').glob('*.py')) + list((PROJECT / 'engine/biomechanics').glob('*.py'))
    paths += list((PROJECT / 'engine/squat/metrics').glob('*.py'))
    paths += [PROJECT / 'engine/squat' / (name + '.py') for name in
              ('analyzer', 'features', 'cycles', 'phases', 'reps', 'smoothing', 'assessment', 'quality')]
    digest = hashlib.sha256()
    for path in sorted(paths):
        digest.update(path.relative_to(PROJECT).as_posix().encode())
        digest.update(path.read_bytes())
    return digest.hexdigest()


def evaluation_fingerprint():
    digest = hashlib.sha256()
    paths = list((PROJECT / 'engine/validation').glob('*.py')) + [PROJECT / 'tools/evaluate_e3.py']
    for path in sorted(paths):
        digest.update(path.relative_to(PROJECT).as_posix().encode())
        digest.update(path.read_bytes())
    return digest.hexdigest()


def environment_signature():
    import cv2
    import mediapipe
    packages = {}
    for name in ('mediapipe', 'numpy', 'opencv-python', 'opencv-contrib-python'):
        try:
            packages[name] = version(name)
        except PackageNotFoundError:
            packages[name] = None
    weights = Path(mediapipe.__file__).parent / 'modules/pose_landmark/pose_landmark_full.tflite'
    if not weights.is_file():
        raise ValueError('primary Full model weights must be installed before freezing evaluation')
    module_root = Path(mediapipe.__file__).parent
    graph = module_root / 'modules/pose_landmark/pose_landmark_cpu.binarypb'
    detector = module_root / 'modules/pose_detection/pose_detection.tflite'
    if not graph.is_file() or not detector.is_file():
        raise ValueError('primary pose graph and detector weights must be installed before freeze')
    return dict(python=platform.python_version(), platform=platform.platform(), cv2=cv2.__version__, packages=packages,
                full_model_sha256=sha256(weights), detector_sha256=sha256(detector), pose_graph_sha256=sha256(graph))


def local_path(root, relative):
    if not isinstance(relative, str):
        raise ValueError('bundle paths must be relative strings')
    path = (Path(root) / relative).resolve()
    if not path.is_relative_to(Path(root).resolve()):
        raise ValueError('bundle path escapes dataset directory')
    return path


def known_development_sources(root):
    known = {source['sha256']: source['id'] for source in read_json(INVENTORY)['sources']}
    # Local collection history supplements human source-provenance review.
    # Copies moved outside this collection still require truthful source grouping.
    for path in Path(root).parent.glob('*/runs/*/results.json'):
        result = read_json(path)
        if result.get('kind') == 'development_smoke':
            for clip in result.get('clips', []):
                known[clip['source_sha256']] = 'development_smoke:' + path.parent.parent.parent.name
    return known


def draft_entries(videos, output, existing=()):
    output = Path(output)
    videos = [Path(video).resolve() for video in videos]
    if not videos or len(set(videos)) != len(videos):
        raise ValueError('provide distinct source videos')
    known = known_development_sources(output)
    signatures = [sha256(video) for video in videos]
    if len(set(signatures)) != len(signatures) or set(signatures) & {entry['sha256'] for entry in existing}:
        raise ValueError('duplicate source content')
    entries, drafts = [], {}
    reserved = {entry['id'] for entry in existing}
    index = 0
    for video, digest in zip(videos, signatures):
        index += 1
        identifier = f'clip-{index:03d}'
        while (identifier in reserved or (output / f'reviews/{identifier}.json').exists()
               or (output / f'references/{identifier}.json').exists()):
            index += 1
            identifier = f'clip-{index:03d}'
        reserved.add(identifier)
        stat = video.stat()
        review_path = f'reviews/{identifier}.json'
        reference_path = f'references/{identifier}.json'
        drafts[review_path] = dict(video=video.name, size=stat.st_size, mtime_ns=stat.st_mtime_ns,
                                  reviews=[asdict(RecordingReview(side)) for side in ('left', 'right')])
        drafts[reference_path] = dict(schema_version=1, source_sha256=digest, confirmed=False,
                    reviewer=None, origin=None, notes='', repetitions=[], frame_measurements=[])
        entries.append(dict(id=identifier, video=str(video), sha256=digest, case='compliant',
                    participant_id=None, source_group_id=None, provenance_reviewed=False,
                    unused_for_development=None, side=None, facing=None,
                    recording_review=review_path, reference=reference_path,
                    expected_affected_items=[], expected_unaffected_items=[],
                    known_source_match=known.get(digest)))
    return entries, drafts


def prepare(videos, output):
    """Create drafts only. Known sources remain blocked from held-out use."""
    output = Path(output)
    entries, drafts = draft_entries(videos, output)
    output.mkdir(parents=True, exist_ok=False)
    for name, data in drafts.items():
        write_new(output / name, data)
    write_new(output / 'limits.json', read_json(PROTOCOL))
    write_new(output / 'manifest.json', dict(schema_version=1, protocol_version='e3-v0.1',
              state='draft', clips=entries, primary_configuration=read_json(INVENTORY)['primary_configuration']))
    return output / 'manifest.json'


def register(videos, root):
    """Append to an unfrozen draft without overwriting reviewed files."""
    root = Path(root)
    if (root / 'freeze.json').exists():
        raise ValueError('cannot register sources into a frozen bundle; prepare a new evaluation')
    path = root / 'manifest.json'
    original_bytes = path.read_bytes()
    before = sha256(path)
    manifest = read_json(path)
    if manifest.get('state') != 'draft' or not isinstance(manifest.get('clips'), list):
        raise ValueError('registration requires an editable draft manifest')
    entries, drafts = draft_entries(videos, root, manifest['clips'])
    for name, data in drafts.items():
        write_new(root / name, data)
    if sha256(path) != before:
        raise ValueError('manifest changed during registration; new draft files were preserved separately')
    manifest['clips'].extend(entries)
    serialized = json.dumps(manifest, indent=2, allow_nan=False) + '\n'
    backup = root / f'manifest.before-register-{uuid.uuid4().hex}.json'
    with backup.open('xb') as handle:
        handle.write(original_bytes)
    try:
        path.write_text(serialized, encoding='utf-8')
    except OSError as error:
        try:
            path.write_bytes(original_bytes)
        except OSError:
            raise OSError(f'manifest write failed; original is preserved at {backup}') from error
        raise
    return path


def finite_number(value):
    return type(value) in (int, float) and math.isfinite(value)


def reference_positions(repetitions):
    """Ten prescribed positions, derived solely from reviewed reference events."""
    if len(repetitions) < 3:
        return []
    positions = [max(0, repetitions[0]['start_source'] - 1)]
    for rep in repetitions[:3]:
        low, high = rep['deepest_interval']
        positions.extend(((rep['start_source'] + low) // 2, (low + high) // 2,
                          (high + rep['end_source']) // 2))
    return positions


def reference_problems(reference, entry, limits):
    errors = []
    if not isinstance(reference, dict):
        return ['reference must be an object']
    if reference.get('source_sha256') != entry['sha256']:
        errors.append('reference source hash mismatch')
    if reference.get('confirmed') is not True or not isinstance(reference.get('reviewer'), str) or not reference['reviewer'].strip():
        errors.append('reference needs named independent confirmation')
    if reference.get('origin') != 'independent_review':
        errors.append('reference origin must be independent_review')
    if entry['case'] != 'compliant':
        return errors
    reps = reference.get('repetitions')
    if not isinstance(reps, list) or len(reps) < 3:
        return errors + ['at least three independently reviewed complete repetitions required']
    previous_end = -1
    for rep in reps:
        if not isinstance(rep, dict):
            return errors + ['invalid repetition reference']
        start, end = rep.get('start_source'), rep.get('end_source')
        interval = rep.get('deepest_interval')
        if (type(start) is not int or type(end) is not int or start < previous_end or start < 1
                or not isinstance(interval, list) or len(interval) != 2
                or any(type(value) is not int for value in interval)
                or not start < interval[0] <= interval[1] < end):
            return errors + ['invalid or overlapping reference boundaries; include standing before first start']
        previous_end = end
        uncertainty = rep.get('uncertainty_frames')
        if not finite_number(uncertainty) or not 0 <= uncertainty <= limits['reference_requirements']['boundary_uncertainty_max_frames']:
            errors.append('reference boundary uncertainty unsupported')
        for name in METRICS:
            metrics = rep.get('metrics', {})
            item = metrics.get(name, {}) if isinstance(metrics, dict) else {}
            errors.extend(measurement_reference_problems(item, name, limits))
    samples = reference.get('frame_measurements')
    if not isinstance(samples, list):
        return errors + ['frame measurements must be a list']
    positions = reference_positions(reps)
    if len(set(positions)) != 10:
        errors.append('reference events do not define ten distinct prescribed frames')
    for name in FRAME_METRICS:
        selected = [sample for sample in samples if isinstance(sample, dict) and sample.get('metric') == name]
        frames = [sample.get('source_frame') for sample in selected]
        if len(frames) != 10 or any(type(value) is not int for value in frames) or sorted(frames) != sorted(positions):
            errors.append(f'{name}: ten prescribed frame references required')
        for sample in selected:
            errors.extend(measurement_reference_problems(sample, name, limits))
    return errors


def measurement_reference_problems(item, name, limits):
    if not isinstance(item, dict) or not finite_number(item.get('value')):
        return [f'{name}: independent numeric reference missing']
    uncertainty = item.get('uncertainty')
    maximum = (limits['reference_requirements']['angle_reference_uncertainty_max_degrees']
               if name in FRAME_METRICS else limits['metrics'][name]['max_mean_absolute_error'] * .5)
    if not finite_number(uncertainty) or not 0 <= uncertainty <= maximum:
        return [f'{name}: independent reference uncertainty unsupported']
    return []


def check(root):
    root = Path(root)
    manifest = read_json(root / 'manifest.json')
    limits = read_json(root / 'limits.json')
    if not isinstance(manifest, dict) or not isinstance(limits, dict):
        return dict(ready=False, problems=['manifest and limits must be objects'], clips=[])
    errors = []
    if limits != read_json(PROTOCOL):
        return dict(ready=False, problems=['limits differ from predeclared protocol v0.1'], clips=[])
    inventory = read_json(INVENTORY)
    if manifest.get('primary_configuration') != inventory['primary_configuration']:
        errors.append('primary configuration differs from predeclared configuration')
    if manifest.get('protocol_version') != 'e3-v0.1' or manifest.get('schema_version') != 1:
        errors.append('unsupported dataset schema/protocol')
    clips = manifest.get('clips')
    if not isinstance(clips, list) or not clips or any(not isinstance(entry, dict) for entry in clips):
        return dict(ready=False, problems=errors + ['no registered clips'], clips=[])
    known = set(known_development_sources(root))
    seen_ids, seen_hashes, groups = set(), set(), {}
    per_clip = []
    for entry in clips:
        problems = []
        identifier = entry.get('id')
        try:
            if not isinstance(identifier, str) or not identifier or identifier in seen_ids:
                raise ValueError('missing/duplicate clip id')
            seen_ids.add(identifier)
            video = Path(entry['video'])
            digest = sha256(video)
            if digest != entry['sha256']:
                problems.append('source content changed')
            if digest in known:
                problems.append('known development/quarantined source is not held-out data')
            if digest in seen_hashes:
                problems.append('duplicate source content')
            seen_hashes.add(digest)
            if entry.get('case') not in CASES:
                problems.append('unsupported evaluation case')
            for field in ('participant_id', 'source_group_id'):
                if not isinstance(entry.get(field), str) or not entry[field].strip():
                    problems.append(f'{field} missing')
            if entry.get('provenance_reviewed') is not True or entry.get('unused_for_development') is not True:
                problems.append('source provenance and lack of development use need review')
            group = entry.get('source_group_id')
            if isinstance(group, str) and group:
                previous = groups.setdefault(group, entry.get('participant_id'))
                if previous != entry.get('participant_id'):
                    problems.append('source group has conflicting participant identities')
            if entry.get('side') not in ('left', 'right') or entry.get('facing') not in ('left', 'right'):
                problems.append('selected side/facing missing')
            reviews = load_recording_reviews(local_path(root, entry['recording_review']), video)
            review = next((item for item in reviews if item.side == entry.get('side')), None)
            reference = read_json(local_path(root, entry['reference']))
            problems.extend(reference_problems(reference, entry, limits))
            if entry.get('case') == 'compliant' and entry.get('side') in ('left', 'right'):
                for metric in [item[0] for item in METRICS.values()] + ['timing']:
                    status, reason = recording_gate(metric, review, BodySide(entry['side']))
                    if status != 'approved':
                        problems.append(reason)
            elif entry.get('case') in CASES and entry.get('case') != 'compliant':
                affected = entry.get('expected_affected_items')
                unaffected = entry.get('expected_unaffected_items')
                allowed = set(METRICS) | {'total_duration'}
                if (not isinstance(affected, list) or not affected or not isinstance(unaffected, list)
                        or (not unaffected and entry['case'] != 'wrong_view')
                        or any(not isinstance(item, str) or item not in allowed for item in affected + unaffected)
                        or set(affected) & set(unaffected) or len(set(affected + unaffected)) != len(affected + unaffected)
                        or set(affected + unaffected) != allowed):
                    problems.append('negative case must partition all metric names into affected/unaffected without duplicates')
                if review is None or not review.reviewer:
                    problems.append('negative case needs named source review')
                elif entry['case'] == 'wrong_view' and review.side_view is not False:
                    problems.append('wrong-view case requires an explicitly rejected view')
                elif entry['case'] == 'required_joint_occlusion' and not any(
                        getattr(review, name) is False for name in
                        ('hips_visible', 'knees_visible', 'ankles_visible', 'shoulders_visible', 'feet_visible')):
                    problems.append('occlusion case requires an explicitly obscured joint')
                elif entry['case'] == 'timing_discontinuity_or_unknown_cadence' and review.continuous_original_speed is True and review.constant_frame_rate is True:
                    problems.append('timing-violation case cannot have both timing conditions approved')
        except (OSError, ValueError, KeyError, TypeError) as error:
            problems.append(str(error))
        per_clip.append(dict(id=identifier, ready=not problems, problems=sorted(set(problems))))
    compliant = [entry for entry in clips if entry.get('case') == 'compliant']
    if len(compliant) < limits['collection_targets']['compliant_clips']:
        errors.append('three compliant clips required before primary evaluation freeze')
    participants = {entry.get('participant_id') for entry in compliant if isinstance(entry.get('participant_id'), str) and entry['participant_id'].strip()}
    if len(participants) < limits['collection_targets']['distinct_participants_in_compliant_clips']:
        errors.append('three compliant participant identities required')
    for case in limits['collection_targets']['known_violation_cases']:
        if not any(entry.get('case') == case for entry in clips):
            errors.append(f'pending negative case: {case}')
    return dict(ready=not errors and all(item['ready'] for item in per_clip), problems=errors, clips=per_clip)


def freeze(root):
    root = Path(root)
    report = check(root)
    if not report['ready']:
        raise ValueError('dataset not ready: ' + json.dumps(report, ensure_ascii=True))
    manifest = read_json(root / 'manifest.json')
    files = {'manifest.json', 'limits.json'}
    for entry in manifest['clips']:
        files.update((entry['reference'], entry['recording_review']))
    record = dict(schema_version=1, analysis_fingerprint=analysis_fingerprint(), evaluation_fingerprint=evaluation_fingerprint(),
                  environment=environment_signature(),
                  protocol_sha256=sha256(PROTOCOL), inventory_sha256=sha256(INVENTORY),
                  files={name: sha256(local_path(root, name)) for name in sorted(files)},
                  sources={entry['id']: entry['sha256'] for entry in manifest['clips']})
    write_new(root / 'freeze.json', record)
    return root / 'freeze.json'


def verify_frozen(root):
    root = Path(root)
    frozen = read_json(root / 'freeze.json')
    manifest = read_json(root / 'manifest.json')
    expected_files = {'manifest.json', 'limits.json'}
    for entry in manifest['clips']:
        expected_files.update((entry['reference'], entry['recording_review']))
    if (not isinstance(frozen, dict) or frozen.get('schema_version') != 1
            or not isinstance(frozen.get('files'), dict) or set(frozen['files']) != expected_files
            or not isinstance(frozen.get('sources'), dict)
            or set(frozen['sources']) != {entry['id'] for entry in manifest['clips']}):
        raise ValueError('frozen input ledger incomplete or invalid')
    if frozen.get('analysis_fingerprint') != analysis_fingerprint():
        raise ValueError('analysis source changed after freeze')
    if frozen.get('evaluation_fingerprint') != evaluation_fingerprint():
        raise ValueError('evaluation source changed after freeze')
    if frozen.get('protocol_sha256') != sha256(PROTOCOL) or frozen.get('inventory_sha256') != sha256(INVENTORY):
        raise ValueError('predeclared protocol or source inventory changed after freeze')
    if frozen.get('environment') != environment_signature():
        raise ValueError('runtime or primary model weights changed after freeze')
    for name, digest in frozen['files'].items():
        if sha256(local_path(root, name)) != digest:
            raise ValueError(f'frozen input changed: {name}')
    for entry in manifest['clips']:
        if sha256(entry['video']) != frozen['sources'].get(entry['id']):
            raise ValueError(f'frozen video changed: {entry["id"]}')
    report = check(root)
    if not report['ready']:
        raise ValueError('frozen dataset no longer satisfies eligibility')
    return manifest
