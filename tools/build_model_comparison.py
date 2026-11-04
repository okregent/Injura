"""Build local video-6 model comparison after generating model-specific reports.

Use model 2 with --posture-calibration, then compare with and without
--recover-missing-poses. No count reference is passed into analysis.
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
    sources = [
        ("Full", root / "sample_video6/pose-cache.json", None),
        ("Full + source-image retry", root / "sample_video6/recovered-pose-cache.json", "../sample_video6/index.html"),
        ("Heavy", output / "video6-heavy/pose-cache-model-2.json", "video6-heavy/index.html"),
        ("Heavy + source-image retry", output / "video6-heavy-recovered/recovered-pose-cache.json", "video6-heavy-recovered/index.html"),
    ]
    rows, links = [], []
    for label, path, link in sources:
        data = json.loads(path.read_text(encoding="utf-8"))
        data = data.get("extraction", data)
        data["pose_sequence"] = [[Landmark(**point) for point in frame] for frame in data["pose_sequence"]]
        extraction = PoseExtractionResult(**data)
        for side in BodySide:
            result = SquatAnalyzer().analyze(
                extraction, side=side, facing_direction=FacingDirection.LEFT, use_posture_calibration=True,
            )
            rows.append({
                "model": label, "side": side.value,
                "source_frames": extraction.source_frame_count,
                "pose_frames": len(extraction.pose_sequence),
                "re_detected_frames": len(extraction.recovered_frame_indices),
                "detected_reps": len(result.repetitions), "unverified_candidates": len(result.candidates),
                "timed_reps": sum(rep.metrics["timing"].value is not None for rep in result.repetitions),
                "bottom_knee_angle_available": sum(rep.metrics["knee_flexion"].value is not None for rep in result.repetitions),
                "bottom_hip_angle_available": sum(rep.metrics["hip_flexion"].value is not None for rep in result.repetitions),
                "calibration": result.calibration_method,
            })
        if link and (output / link).is_file():
            links.append(f'<li><a href="{link}">{html.escape(label)}</a></li>')
    with (output / "model-comparison.csv").open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    parts = [
        '<!doctype html><html lang="en"><meta charset="utf-8"><title>Video 6 model comparison</title>',
        '<style>body{font:16px system-ui;margin:32px;line-height:1.6}table{border-collapse:collapse}'
        'td,th{border:1px solid #ccd;padding:9px}.scroll{overflow:auto}img{max-width:100%}</style>',
        '<h1>Video 6: model and landmark continuity investigation</h1><a href="../index.html">Back to investigation</a>',
        '<p>Original Full-model overlays show the same foreground lifter while upper-body '
        'landmarks shift across reacquisition. This supports landmark instability under occlusion, '
        'not proven tracking of a different person. Visual interpretation is not anatomical ground truth.</p>',
        '<p>At the four investigated gaps, mean hip displacement across adjacent observations is '
        '0.115-0.121 image-width units for Full and 0.007-0.048 for Heavy. '
        'Actual interval lengths differ where source frames are missing; these are coordinate '
        'displacements, not velocity or accuracy measurements.</p>',
        '<p>All comparison runs request the same experimental posture calibration and use '
        'the same video. Re-detection uses the same model as its primary extraction; confidence '
        'remains 0.5 and the existing association guard is unchanged. No count label is used '
        'to adjust detection. The normal default remains Full (complexity 1).</p>',
        '<p><b>Heavy plus retry detects the user-reported three reps and provides phase timing.</b> '
        'However bottom knee/hip angles are unavailable because their landmarks fail quality checks. '
        'One repetition includes a source-image re-detection and is marked partial. '
        'Count agreement and improved continuity do not validate joint accuracy or exact timing boundaries.</p>',
        '<div class="scroll"><table><tr>' + ''.join(f'<th>{html.escape(k)}</th>' for k in rows[0]) + '</tr>',
    ]
    for row in rows:
        parts.append('<tr>' + ''.join(f'<td>{html.escape(str(v))}</td>' for v in row.values()) + '</tr>')
    parts.extend([
        '</table></div><h2>Detailed outputs</h2><ul>', *links,
        '</ul><p><a href="model-comparison.csv">Comparison CSV</a></p>',
    ])
    if (output / "joint-continuity.csv").is_file():
        parts.append('<p><a href="joint-continuity.csv">Investigated joint displacements</a></p>')
    for title, source, description in [
        ("Original Full-model tracking before/after gaps", "../sample_video6/tracking-gaps-overview.jpg",
         "Original frames and pose overlays around missing frames"),
        ("Heavy plus retry: deepest observed frames", "heavy-recovered-bottoms.jpg",
         "Three deepest observed frames from Heavy plus retry"),
    ]:
        if (output / source).is_file():
            parts.append(f'<h2>{title}</h2><img src="{source}" alt="{description}">')
    parts.append('</html>')
    (output / "index.html").write_text('\n'.join(parts), encoding="utf-8")
    return rows


if __name__ == "__main__":
    build()
