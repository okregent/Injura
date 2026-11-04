"""Prepare local annotation templates without treating predictions as labels."""

import csv
import html
import json
import os
from pathlib import Path


def prepare(root: Path = Path("artifacts/sample-review")):
    recordings = []
    for folder in sorted(root.glob("sample_video*")):
        path = folder / "analysis.json"
        if path.exists():
            recordings.append(json.loads(path.read_text(encoding="utf-8")))
    if not recordings:
        raise ValueError("Generate sample review reports first")
    templates = {
        "count-annotations.csv": (
            ["video", "actual_reps", "reviewer", "notes"],
            [{"video": item["video"]} for item in recordings],
        ),
        "boundary-annotations.csv": (
            ["video", "actual_rep_id", "start_source", "bottom_source", "end_source", "reviewer", "notes"],
            [{"video": item["video"]} for item in recordings],
        ),
    }
    for filename, (columns, rows) in templates.items():
        path = root / filename
        if not path.exists():
            with path.open("w", newline="", encoding="utf-8-sig") as handle:
                writer = csv.DictWriter(handle, fieldnames=columns)
                writer.writeheader()
                writer.writerows(rows)
    parts = [
        '<!doctype html><html lang="en"><meta charset="utf-8"><title>Manual sample review</title>',
        '<style>body{font:16px system-ui;max-width:1150px;margin:32px;line-height:1.6}video{max-width:100%;max-height:560px}'
        'table{border-collapse:collapse;margin:12px 0}td,th{border:1px solid #ccd;padding:8px}.note{background:#fff2cf;padding:16px}</style>',
        '<h1>Manual reference review</h1><a href="index.html">Back to investigation</a>',
        '<div class="note">Watch each recording first and count completed standing-to-standing squats. '
        'Exclude partial motions at the beginning/end and rack setup. Record uncertain cases in notes. '
        'Detector counts and candidates are suggestions only; neither is ground truth.</div>',
        '<p>Fill <a href="count-annotations.csv">count-annotations.csv</a> with actual counts. '
        'For detailed review, duplicate rows in <a href="boundary-annotations.csv">boundary-annotations.csv</a> '
        'and enter one row per actual repetition. Templates are never overwritten when regenerated.</p>',
        '<p>Frame indices are zero-based. At constant frame rate, frame = round(player time in seconds × FPS). '
        'Start is departure from standing, bottom is the deepest observed physical posture, and end is return to standing. '
        'If a boundary cannot be identified reliably, leave it blank and explain why. Candidate boundaries '
        'may include preparation time; inspect the full video rather than copying these values.</p>',
    ]
    for item in recordings:
        video = Path(item["video"]).resolve()
        relative = Path(os.path.relpath(video, root.resolve())).as_posix()
        parts.extend([
            f'<h2>{html.escape(item["video"])}</h2>',
            f'<p>{item["fps"]} FPS; {item["source_frames"]} frames.</p>',
            f'<video controls preload="metadata" src="{html.escape(relative, quote=True)}"></video>',
            '<details><summary>Detector ranges for comparison after your own review</summary>',
            '<table><tr><th>Side</th><th>Type</th><th>Number</th><th>Start (s / frame)</th>'
            '<th>Observed bottom (s / frame)</th><th>End (s / frame)</th></tr>',
        ])
        for side, data in item["sides"].items():
            for kind, entries in (("Uninterrupted detection", data["repetitions"]), ("UNVERIFIED candidate", data.get("candidates", []))):
                for number, entry in enumerate(entries, 1):
                    rep = entry["rep"]
                    if kind == "UNVERIFIED candidate":
                        bottom = entry["deepest_observed_index"]
                    else:
                        depth = entry["metrics"]["depth"]["value"]
                        bottom = depth["deepest_index"] if depth else None
                    indices = [rep["start_index"], bottom, rep["end_index"]]
                    cells = [side, kind, str(number)]
                    for index in indices:
                        source = item["source_frame_indices"][index] if index is not None else None
                        cells.append(f'{source / item["fps"]:.3f} / {source}' if source is not None and item["fps"] else "unavailable")
                    parts.append('<tr>' + ''.join(f'<td>{html.escape(cell)}</td>' for cell in cells) + '</tr>')
        parts.append('</table></details>')
    parts.append('</html>')
    (root / "manual-review.html").write_text("\n".join(parts), encoding="utf-8")
    print((root / "manual-review.html").resolve())


if __name__ == "__main__":
    prepare()
