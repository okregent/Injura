"""Diagnose cached Heavy failures without changing production thresholds."""

import csv
import json
from dataclasses import replace
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import cv2

from engine.pose import recovery
from engine.pose.types import Landmark, PoseExtractionResult


def build(root=Path("artifacts/sample-review/model-comparison")):
    output = root / "diagnostics"
    output.mkdir(parents=True, exist_ok=True)
    findings = {}
    for number, target in [(3, 444), (5, 230)]:
        folder = root / f"video{number}-heavy-recovered"
        saved = json.loads((folder / "pose-cache-model-2.json").read_text())
        data = saved["extraction"]
        data["pose_sequence"] = [[Landmark(**p) for p in frame] for frame in data["pose_sequence"]]
        extraction = PoseExtractionResult(**data)
        source = extraction.source_frame_indices
        pos = next(i for i, (a, b) in enumerate(zip(source, source[1:])) if a < target < b)
        subset = replace(extraction, source_frame_indices=source[pos:pos + 2],
                         pose_sequence=extraction.pose_sequence[pos:pos + 2], recovered_frame_indices=[])
        attempts = []
        original = recovery._compatible

        def inspect(points, before, after, image_size, max_distance, visibility):
            score = original(points, before, after, image_size, max_distance, visibility)
            attempts.append({"accepted": score is not None, "score": score,
                             "hip_visibility": [[frame[i].visibility for i in (23, 24)]
                                                for frame in (points, before, after)]})
            return score

        recovery._compatible = inspect
        try:
            result = recovery.recover_pose_gaps(f"sample_video{number}.mp4", subset, model_complexity=2)
        finally:
            recovery._compatible = original
        findings[str(number)] = {"target": target, "anchor_sources": subset.source_frame_indices,
                                 "proposal_scope": "All frames in the original bounded gap",
                                 "valid_pose_proposals": attempts, "recovered": result.recovered_frame_indices}
        full = json.loads((root.parent / f"sample_video{number}/pose-cache.json").read_text())
        full = full.get("extraction", full)
        findings[str(number)]["full_tracking_target_observed"] = target in full["source_frame_indices"]
        # Diagnostic only: do not merge Full proposals into the Heavy stream.
        attempts = []
        recovery._compatible = inspect
        try:
            full_retry = recovery.recover_pose_gaps(f"sample_video{number}.mp4", subset, model_complexity=1)
        finally:
            recovery._compatible = original
        findings[str(number)]["full_static_probe_on_heavy_anchors"] = {
            "proposal_scope": "All frames in the original bounded Heavy gap; not target-only",
            "valid_pose_proposals": attempts, "recovered": full_retry.recovered_frame_indices,
            "diagnostic_only": True,
        }
        cap = cv2.VideoCapture(f"sample_video{number}.mp4")
        images = []
        try:
            for frame in (target - 1, target, target + 1):
                cap.set(cv2.CAP_PROP_POS_FRAMES, frame)
                success, image = cap.read()
                if not success:
                    raise OSError(f"Could not decode video {number} source frame {frame}")
                image = cv2.resize(image, (int(image.shape[1] * 450 / image.shape[0]), 450))
                cv2.putText(image, f"source {frame}", (10, 25), cv2.FONT_HERSHEY_SIMPLEX, .65, (0, 255, 255), 2)
                images.append(image)
        finally:
            cap.release()
        if not cv2.imwrite(str(output / f"video{number}-gap.jpg"), cv2.hconcat(images)):
            raise OSError("Could not save gap contact sheet")

    data = json.loads((root / "video4-heavy-recovered/analysis.json").read_text())
    rows = []
    fig, axes = plt.subplots(2, 1, figsize=(13, 7), sharex=True)
    for axis, side in zip(axes, ("left", "right")):
        values = data["sides"][side]
        threshold = values["phase_thresholds"]
        movement = threshold["bottom_y"] - threshold["standing_y"]
        cuts = {"standing": threshold["standing_y"] + .15 * movement,
                "bottom_enter": threshold["standing_y"] + .85 * movement}
        axis.plot(data["source_frame_indices"], values["hip_y_values"], label="Observed hip y")
        for name, cut in cuts.items():
            axis.axhline(cut, linestyle="--", label=f"{name}: {cut:.4f}")
        for start, end in [(0, 35), (36, 70), (240, 280)]:
            axis.axvspan(start, end, color="orange", alpha=.18)
        axis.invert_yaxis()
        axis.set_title(f"{side}: {values['calibration_method']}")
        axis.set_ylabel("Image-normalized y")
        axis.legend(loc="upper right", fontsize=8)
        for index, source in enumerate(data["source_frame_indices"]):
            rows.append({"side": side, "source_frame": source, "hip_y": values["hip_y_values"][index],
                         "phase": values["phases"][index], **cuts})
    axes[-1].set_xlabel("Source frame; orange = right-side reps absent on left")
    fig.tight_layout()
    fig.savefig(output / "video4-thresholds.png", dpi=140)
    plt.close(fig)
    with (output / "video4-phases.csv").open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    (output / "gap-retry.json").write_text(json.dumps(findings, indent=2), encoding="utf-8")
    (output / "index.html").write_text(
        '<!doctype html><meta charset="utf-8"><title>Heavy failure diagnostics</title>'
        '<style>body{font:16px system-ui;margin:28px;line-height:1.6}img{max-width:100%}</style>'
        '<h1>Heavy failure diagnostics</h1><a href="../batch-comparison.html">Comparison</a>'
        '<p>Video 3 frame 444 and video 5 frame 230 interrupt otherwise bounded candidates. '
        'Retry JSON records whether static detection yielded a pose and whether association accepted it. '
        'No confidence, association, or cycle thresholds were changed.</p>'
        '<p>Both target images decode successfully. The isolated retries reproduced the remaining gaps '
        'without association rejections: the targets yielded no usable 33-landmark proposal. '
        'The plates obscure the upper body in these frames, but the precise cause of model failure is unproven.</p>'
        '<h2>Full tracking versus isolated retry</h2>'
        '<p>Full primary video tracking observes both target frames, 444 and 230. Full static '
        'retry against the original Heavy anchors does not recover either bounded gap. '
        'For video 3 the Full gap-level probe yields a proposal rejected by association; '
        'it cannot be attributed to target 444 specifically because the gap also contains 443. '
        'For video 5 it yields no usable proposal. Tracking and static detection differ, '
        'so success in one does not imply success in the other. No cross-model coordinates '
        'are merged, no association threshold is relaxed, and primary caches are unchanged.</p>'
        '<h2>Video 3, around source 444</h2><img src="video3-gap.jpg" alt="Source frames 443-445">'
        '<h2>Video 5, around source 230</h2><img src="video5-gap.jpg" alt="Source frames 229-231">'
        '<p>Video 4 has no missing pose or hip observations. Left calibration falls back to sequence extrema; '
        'right uses posture calibration. Left has no observed standing before the first cycle; '
        'its second and seventh right-side cycle windows do not reach the left bottom-entry threshold. '
        'Different side signals and thresholds explain the missing detections; anatomical accuracy remains unverified.</p>'
        '<img src="video4-thresholds.png" alt="Observed hip positions and side-specific thresholds">'
        '<p><a href="video4-phases.csv">Per-frame phases</a> | '
        '<a href="gap-retry.json">Gap retry evidence</a></p>', encoding="utf-8")
    print(json.dumps(findings, indent=2))


if __name__ == "__main__":
    build()
