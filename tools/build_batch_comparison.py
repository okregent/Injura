"""Compare cached Full/Heavy runs with identical experimental calibration.

Generate Heavy recovery reports for videos 3-6 before running this module.
User counts are displayed only; they are never passed to the analyzer.
"""

import csv
import html
import json
from pathlib import Path

from engine.pose.orientation import FacingDirection
from engine.pose.side import BodySide
from engine.pose.types import Landmark, PoseExtractionResult
from engine.squat.analyzer import SquatAnalyzer


def build(root=Path("artifacts/sample-review")):
    output = root / "model-comparison"
    output.mkdir(parents=True, exist_ok=True)
    rows = []
    references = {3: "6-7 (starts at bottom)", 4: "14", 5: "2", 6: "3"}
    for number in references:
        full = root / f"sample_video{number}"
        heavy = output / f"video{number}-heavy-recovered"
        facing = FacingDirection(json.loads((full / "analysis.json").read_text(encoding="utf-8"))["facing"])
        for label, cache in [
            ("Full", full / "pose-cache.json"),
            ("Full + retry", full / "recovered-pose-cache.json"),
            ("Heavy", heavy / "pose-cache-model-2.json"),
            ("Heavy + retry", heavy / "recovered-pose-cache.json"),
        ]:
            data = json.loads(cache.read_text(encoding="utf-8"))
            data = data.get("extraction", data)
            data["pose_sequence"] = [[Landmark(**p) for p in frame] for frame in data["pose_sequence"]]
            extraction = PoseExtractionResult(**data)
            for side in BodySide:
                result = SquatAnalyzer().analyze(
                    extraction, side=side, facing_direction=facing,
                    use_posture_calibration=True,
                )
                available = lambda name: sum(rep.metrics[name].value is not None for rep in result.repetitions)
                rows.append({
                    "video": number, "user_count_reference": references[number],
                    "model": label, "side": side.value,
                    "source_frames": extraction.source_frame_count,
                    "pose_frames": len(extraction.pose_sequence),
                    "recovered_frames": len(extraction.recovered_frame_indices),
                    "repetitions": len(result.repetitions), "candidates": len(result.candidates),
                    "timed_repetitions": available("timing"),
                    "bottom_knee_available": available("knee_flexion"),
                    "bottom_hip_available": available("hip_flexion"),
                    "calibration": result.calibration_method,
                })
    with (output / "batch-comparison.csv").open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    parts = [
        '<!doctype html><html lang="en"><meta charset="utf-8"><title>Videos 3-6 model comparison</title>',
        '<style>body{font:15px system-ui;margin:28px}table{border-collapse:collapse}td,th{border:1px solid #ccd;padding:7px}.scroll{overflow:auto}</style>',
        '<h1>Videos 3-6: Full / Heavy comparison</h1>',
        '<p>All runs use the same experimental posture calibration. Retry uses the same model as extraction. '
        'Counts are user references, not annotated boundaries. Available angles pass visibility checks; '
        'availability is not evidence of anatomical accuracy. Full remains the default.</p>',
        '<p><a href="batch-comparison.csv">CSV</a> | <a href="index.html">Video 6 investigation</a></p>',
        '<div class="scroll"><table><tr>' + ''.join(f'<th>{html.escape(k)}</th>' for k in rows[0]) + '</tr>',
    ]
    for row in rows:
        parts.append('<tr>' + ''.join(f'<td>{html.escape(str(v))}</td>' for v in row.values()) + '</tr>')
    parts.append('</table></div><h2>Heavy plus retry: overlays and measurements</h2><ul>')
    for number in references:
        parts.append(f'<li><a href="video{number}-heavy-recovered/index.html">Video {number}</a></li>')
    parts.append('</ul></html>')
    (output / "batch-comparison.html").write_text('\n'.join(parts), encoding="utf-8")
    return rows


if __name__ == "__main__":
    build()
