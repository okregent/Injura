"""Offline P5/P95 fallback experiment; no production settings or labels change."""

import csv
import argparse
import html
import json
from pathlib import Path

import cv2

from engine.pose.orientation import FacingDirection
from engine.pose.side import BodySide
from engine.pose.types import Landmark, PoseExtractionResult
from engine.squat.analyzer import SquatAnalyzer
from engine.squat.cycles import detect_cycle_phases
from engine.squat.phases import SquatPhaseThresholds
from engine.squat.reps import SquatRep, detect_squat_reps
from engine.squat.smoothing import smooth_squat_phases


def replay(features, source, thresholds):
    """Replay strict spans only; verify parity with analyzer before experiments."""
    spans, start = [], None
    for index, value in enumerate(features.hip_y_values):
        if start is not None and (value is None or source[index] != source[index - 1] + 1):
            spans.append((start, index))
            start = None
        if value is not None and start is None:
            start = index
    if start is not None:
        spans.append((start, features.frame_count))
    reps = []
    for start, stop in spans:
        if stop - start < 2:
            continue
        phases = smooth_squat_phases(detect_cycle_phases(features.hip_y_values[start:stop], thresholds), min_duration=3)
        reps.extend(SquatRep(r.start_index + start, r.bottom_index + start, r.end_index + start)
                    for r in detect_squat_reps(phases))
    return reps


def percentile(values, fraction):
    ordered = sorted(values)
    rank = fraction * (len(ordered) - 1)
    lower = int(rank)
    return ordered[lower] + (rank - lower) * (ordered[min(lower + 1, len(ordered) - 1)] - ordered[lower])


def evaluate(root=Path("artifacts/sample-review"), numbers=(3, 4, 5, 6)):
    output = root / "model-comparison/calibration-experiment"
    output.mkdir(parents=True, exist_ok=True)
    rows, boundaries = [], []
    for number in numbers:
        stem = "sample_video" if number == 1 else f"sample_video{number}"
        full = root / stem
        heavy = root / f"model-comparison/video{number}-heavy-recovered"
        facing = FacingDirection(json.loads((full / "analysis.json").read_text())["facing"])
        for label, path in [("Full", full / "pose-cache.json"),
                            ("Full + retry", full / "recovered-pose-cache.json"),
                            ("Heavy", heavy / "pose-cache-model-2.json"),
                            ("Heavy + retry", heavy / "recovered-pose-cache.json")]:
            data = json.loads(path.read_text())
            data = data.get("extraction", data)
            data["pose_sequence"] = [[Landmark(**p) for p in frame] for frame in data["pose_sequence"]]
            extraction = PoseExtractionResult(**data)
            for side in BodySide:
                result = SquatAnalyzer().analyze(extraction, side=side, facing_direction=facing,
                                                 use_posture_calibration=True)
                baseline = replay(result.features, extraction.source_frame_indices, result.phase_thresholds)
                if baseline != [r.rep for r in result.repetitions]:
                    raise AssertionError("Diagnostic replay diverged from production analyzer")
                threshold = result.phase_thresholds
                eligible = result.calibration_method == "sequence_extrema"
                if eligible:
                    values = [y for y in result.features.hip_y_values if y is not None]
                    standing, bottom = percentile(values, .05), percentile(values, .95)
                    if standing < bottom:
                        threshold = SquatPhaseThresholds(standing, bottom, .03 * (bottom - standing))
                    else:
                        eligible = False
                proposed = replay(result.features, extraction.source_frame_indices, threshold)
                source = extraction.source_frame_indices
                shifts = [abs(source[getattr(a, field)] - source[getattr(b, field)])
                          for a, b in zip(baseline, proposed) for field in ("start_index", "end_index")]
                max_shift = max(shifts, default=0) if len(baseline) == len(proposed) else None
                before = threshold.standing_y
                movement = threshold.bottom_y - before
                rows.append({"video": number, "model": label, "side": side.value,
                             "baseline_calibration": result.calibration_method,
                             "experimental_fallback_applied": eligible,
                             "baseline_reps": len(baseline), "experimental_reps": len(proposed),
                             "max_start_end_shift_frames": max_shift,
                             "experimental_standing_cut": before + .15 * movement,
                             "experimental_bottom_cut": before + .85 * movement})
                for variant, repetitions in [("baseline", baseline), ("experimental", proposed)]:
                    for i, rep in enumerate(repetitions, 1):
                        deepest = max(range(rep.start_index, rep.end_index + 1),
                                      key=lambda j: result.features.hip_y_values[j])
                        boundaries.append({"video": number, "model": label, "side": side.value,
                                           "variant": variant, "rep": i,
                                           "start_source": extraction.source_frame_indices[rep.start_index],
                                           "deepest_observed_source": extraction.source_frame_indices[deepest],
                                           "end_source": extraction.source_frame_indices[rep.end_index],
                                           "status": "unverified model output, not reference annotation"})
    for filename, data in [("comparison.csv", rows), ("boundaries.csv", boundaries)]:
        with (output / filename).open("w", newline="", encoding="utf-8-sig") as handle:
            writer = csv.DictWriter(handle, fieldnames=list(data[0]))
            writer.writeheader()
            writer.writerows(data)
    # Inspect the three previously omitted cycles; these remain predictions.
    selected = [r for r in boundaries if r["video"] == 4 and r["model"] == "Heavy + retry"
                and r["side"] == "left" and r["variant"] == "experimental" and r["rep"] in (1, 2, 7)]
    cap = cv2.VideoCapture("sample_video4.mp4")
    strips = []
    try:
        for rep in selected:
            images = []
            for key in ("start_source", "deepest_observed_source", "end_source"):
                cap.set(cv2.CAP_PROP_POS_FRAMES, rep[key])
                success, frame = cap.read()
                if not success:
                    raise OSError(f"Could not read source {rep[key]}")
                frame = cv2.resize(frame, (int(frame.shape[1] * 360 / frame.shape[0]), 360))
                cv2.putText(frame, f"rep {rep['rep']}: {rep[key]}", (8, 22), cv2.FONT_HERSHEY_SIMPLEX, .5, (0, 255, 255), 1)
                images.append(frame)
            strips.append(cv2.hconcat(images))
    finally:
        cap.release()
    if strips and not cv2.imwrite(str(output / "video4-predicted-boundaries.jpg"), cv2.vconcat(strips)):
        raise OSError("Could not write boundary contact sheet")
    parts = ['<!doctype html><meta charset="utf-8"><title>Offline calibration experiment</title>',
             '<style>body{font:15px system-ui;margin:28px;line-height:1.6}td,th{border:1px solid #ccd;padding:7px}table{border-collapse:collapse}</style>',
             '<h1>Offline calibration fallback experiment</h1>',
             '<p>P5 standing / P95 bottom only where posture calibration is unavailable. '
             'This reduces the influence of extrema; it is an unvalidated engineering hypothesis. '
             'No count labels, interpolation, gap bridging, confidence changes, or automatic side selection. '
             f'Production analyzer and default Full model remain unchanged. All {len(rows)} baseline replays '
             'must exactly match the analyzer before experimental output is generated.</p>',
             '<p>Counts and boundaries remain unverified predictions. No count references are used. '
             'Unchanged counts do not establish unchanged boundaries or metric accuracy. For additional '
             'recordings, inspect camera suitability and actual repetitions before interpreting performance.</p>',
             '<p><a href="comparison.csv">Comparison CSV</a> | <a href="boundaries.csv">Predicted boundaries</a></p>',
             '<table><tr>' + ''.join(f'<th>{html.escape(k)}</th>' for k in rows[0]) + '</tr>']
    if strips:
        parts.insert(-1, '<h2>Previously omitted video 4 cycles: predicted start / deepest / end</h2>'
                     '<img style="max-width:100%" src="video4-predicted-boundaries.jpg" alt="Original frames at experimental predicted boundaries for repetitions 1, 2 and 7">')
    if (output.parent / "diagnostics/index.html").is_file():
        parts.insert(-1, '<p><a href="../diagnostics/index.html">Failure evidence</a></p>')
    if 1 in numbers:
        parts.insert(-1, '<p><b>Video 1 has a frontal/oblique view; it is a robustness check, '
                     'not validation of side-view angles. Facing input is a placeholder there and '
                     'does not enter this hip-y cycle replay. Actual counts and exact boundaries '
                     'for videos 1/2 are unannotated. These recordings were already used in project '
                     'tests, so they are additional recordings, not an untouched independent test set.</b></p>')
    parts.extend('<tr>' + ''.join(f'<td>{html.escape(str(v))}</td>' for v in row.values()) + '</tr>' for row in rows)
    parts.append('</table>')
    (output / "index.html").write_text('\n'.join(parts), encoding="utf-8")
    print(json.dumps([r for r in rows if r["baseline_reps"] != r["experimental_reps"]], indent=2))
    return rows


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path("artifacts/sample-review"))
    parser.add_argument("--videos", type=int, nargs="+", default=[3, 4, 5, 6], choices=range(1, 7))
    args = parser.parse_args()
    evaluate(args.root, args.videos)
