"""Compare saved detector counts with user references; never infer frame labels."""

import csv
import html
import json
from pathlib import Path


def reference_range(row):
    if row.get("actual_reps", "").strip():
        low = high = int(row["actual_reps"])
    elif row.get("reported_min_reps", "").strip() and row.get("reported_max_reps", "").strip():
        low, high = int(row["reported_min_reps"]), int(row["reported_max_reps"])
    else:
        return None
    if low < 0 or high < low:
        raise ValueError("reference counts must define a nonnegative ordered range")
    return low, high


def evaluate(root=Path("artifacts/sample-review")):
    with (root / "count-annotations.csv").open(encoding="utf-8-sig", newline="") as handle:
        annotations = list(csv.DictReader(handle))
    rows = []
    for reference in annotations:
        bounds = reference_range(reference)
        if bounds is None:
            continue
        video = reference["video"]
        if Path(video).name != video:
            raise ValueError("annotation video must be a filename")
        path = root / Path(video).stem / "analysis.json"
        if not path.exists():
            continue
        current = json.loads(path.read_text(encoding="utf-8"))
        low, high = bounds
        for side, data in current["sides"].items():
            measured, candidates = len(data["repetitions"]), len(data.get("candidates", []))
            rows.append({
                "video": video, "side": side, "reported_min": low, "reported_max": high,
                "measured_detections": measured, "unverified_candidates": candidates,
                "measured_count_within_reported_range": low <= measured <= high,
                "candidate_count_within_reported_range": low <= candidates <= high,
                "recovered_frames": len(current.get("recovered_frame_indices", [])),
                "calibration": data.get("calibration_method", "sequence_extrema"),
            })
    if not rows:
        raise ValueError("No reference counts matched generated reports")
    with (root / "count-evaluation.csv").open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    parts = [
        '<!doctype html><html lang="en"><meta charset="utf-8"><title>Count reference evaluation</title>',
        '<style>body{font:16px system-ui;margin:30px;line-height:1.6}table{border-collapse:collapse}'
        'td,th{border:1px solid #ccd;padding:9px}.scroll{overflow:auto}</style>',
        '<h1>User-reference count evaluation</h1><a href="index.html">Investigation</a>',
        '<p>Video 3 has a user-reported range of 6-7 because it starts at the bottom. '
        'Full standing-to-standing counting excludes the initial partial motion. '
        'Other user counts are 14, 2, and 3. Frame boundaries remain unannotated.</p>',
        '<p>Agreement of counts does not establish correct event matching, boundaries, angles, or timing. '
        'Candidates are excluded from measured repetition counts and must not be added across body sides. '
        'Opt-in re-detection and posture calibration are experimental; defaults remain unchanged.</p>',
        '<p><a href="count-annotations.csv">User references</a> | <a href="count-evaluation.csv">Comparison CSV</a></p>',
        '<div class="scroll"><table><tr>' + ''.join(f'<th>{html.escape(key)}</th>' for key in rows[0]) + '</tr>',
    ]
    for row in rows:
        parts.append('<tr>' + ''.join(f'<td>{html.escape(str(value))}</td>' for value in row.values()) + '</tr>')
    parts.append('</table></div></html>')
    (root / "count-evaluation.html").write_text('\n'.join(parts), encoding="utf-8")
    return rows


if __name__ == "__main__":
    evaluate()
