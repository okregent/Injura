"""Generate a local review report: python -m tools.review_samples VIDEO --facing left.

Compare both body sides without automatically choosing one. Foot normalization
remains unverified. Generated frames and reports default to ignored artifacts/.
"""

import argparse
import csv
import html
import json
from dataclasses import asdict
from pathlib import Path

import cv2

from engine.pose.mediapipe_estimator import MediaPipePoseEstimator
from engine.pose.orientation import FacingDirection
from engine.pose.side import BodySide, side_landmarks
from engine.pose.types import Landmark, PoseExtractionResult
from engine.pose.recovery import recover_pose_gaps
from engine.squat.analyzer import SquatAnalyzer


def load_extraction(video: Path, output: Path, reuse: bool = False, model_complexity: int = 1):
    """Cache extraction locally, invalidating when the source file changes."""
    signature = {"size": video.stat().st_size, "mtime_ns": video.stat().st_mtime_ns, "schema": 1}
    if model_complexity != 1:
        signature["model_complexity"] = model_complexity
    cache = output / ("pose-cache.json" if model_complexity == 1 else f"pose-cache-model-{model_complexity}.json")
    if reuse and cache.exists():
        saved = json.loads(cache.read_text(encoding="utf-8"))
        if saved["signature"] == signature:
            data = saved["extraction"]
            data["pose_sequence"] = [[Landmark(**point) for point in frame] for frame in data["pose_sequence"]]
            return PoseExtractionResult(**data)
    estimator = MediaPipePoseEstimator(model_complexity=model_complexity)
    try:
        extraction = estimator.extract_with_metadata(str(video))
    finally:
        estimator.close()
    cache.write_text(json.dumps({"signature": signature, "extraction": asdict(extraction)}, allow_nan=False), encoding="utf-8")
    return extraction


def review_video(video: Path, facing: FacingDirection, output: Path, reuse_extraction: bool = False,
                 recover_missing_poses: bool = False,
                 posture_calibration: bool = False, model_complexity: int = 1):
    if not video.is_file():
        raise FileNotFoundError(video)
    output.mkdir(parents=True, exist_ok=True)
    extraction = load_extraction(video, output, reuse_extraction, model_complexity)
    if extraction.image_size is None:
        raise ValueError(f"No video frames decoded: {video}")
    if recover_missing_poses:
        extraction = recover_pose_gaps(str(video), extraction, model_complexity=model_complexity)
        (output / "recovered-pose-cache.json").write_text(
            json.dumps(asdict(extraction), allow_nan=False), encoding="utf-8",
        )
    metadata = {
        "video": video.name, "fps": extraction.fps, "image_size": extraction.image_size,
        "model_complexity": model_complexity,
        "recovery_model_complexity": model_complexity if recover_missing_poses else None,
        "source_frames": extraction.source_frame_count,
        "pose_frames": len(extraction.pose_sequence), "facing": facing.value,
        "source_frame_indices": extraction.source_frame_indices,
        "recovered_frame_indices": extraction.recovered_frame_indices,
        "experimental_options": {"recover_missing_poses": recover_missing_poses,
                                 "posture_calibration": posture_calibration},
        "recording_conditions": "Unverified; normalized knee travel withheld",
        "sides": {},
    }
    rows = []
    images = []
    candidate_rows = []
    candidate_images = []
    cap = cv2.VideoCapture(str(video))
    try:
        for side in BodySide:
            analysis = SquatAnalyzer().analyze(extraction, side=side, facing_direction=facing,
                                              use_posture_calibration=posture_calibration)
            side_data = {
                "issues": analysis.issues,
                "consistency": {name: asdict(value) for name, value in analysis.consistency.items()},
                "repetitions": [],
                "candidates": [asdict(candidate) for candidate in analysis.candidates],
                "hip_y_values": analysis.features.hip_y_values,
                "hip_visibility": [frame[side_landmarks(side)["hip"]].visibility for frame in extraction.pose_sequence],
                "phases": [phase.name for phase in analysis.phases],
                "calibration_method": analysis.calibration_method,
                "phase_thresholds": asdict(analysis.phase_thresholds) if analysis.phase_thresholds else None,
            }
            metadata["sides"][side.value] = side_data
            for number, candidate in enumerate(analysis.candidates, 1):
                observed = candidate.deepest_observed_index
                source_index = extraction.source_frame_indices[observed]
                candidate_rows.append({
                    "side": side.value, "candidate": number,
                    "start_source": extraction.source_frame_indices[candidate.rep.start_index],
                    "end_source": extraction.source_frame_indices[candidate.rep.end_index],
                    "observed_bottom_source": source_index,
                    "missing_source_frames": candidate.missing_source_frames,
                    "review_status": candidate.reason,
                })
                cap.set(cv2.CAP_PROP_POS_FRAMES, source_index)
                success, frame = cap.read()
                if success:
                    cv2.putText(frame, f"UNVERIFIED {side.value} candidate {number}", (10, 25),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 200, 255), 2)
                    cv2.putText(frame, f"Observed frame {source_index}; true bottom may be missing", (10, 50),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 200, 255), 2)
                    filename = f"{side.value}-candidate-{number}-observed.jpg"
                    if not cv2.imwrite(str(output / filename), frame):
                        raise OSError(f"Could not save {filename}")
                    candidate_images.append((filename, f"UNVERIFIED {side.value} candidate {number}, observed source {source_index}"))
            for number, item in enumerate(analysis.repetitions, 1):
                side_data["repetitions"].append(asdict(item))
                metrics = item.metrics

                def value(name, attribute=None):
                    result = metrics[name].value
                    return getattr(result, attribute) if result is not None and attribute else result

                depth = metrics["depth"].value
                source_index = extraction.source_frame_indices[depth.deepest_index] if depth else None
                reasons = [
                    f"{name}: {outcome.quality.reason}"
                    for name, outcome in metrics.items() if outcome.quality.reason
                ]
                row = {
                    "side": side.value, "rep": number,
                    "start_source": extraction.source_frame_indices[item.rep.start_index],
                    "end_source": extraction.source_frame_indices[item.rep.end_index],
                    "bottom_source": source_index,
                    "depth_ratio": value("depth", "depth_ratio"),
                    "hip_knee_gap": value("hip_to_knee", "vertical_gap"),
                    "knee_flexion_deg": value("knee_flexion"),
                    "hip_flexion_deg": value("hip_flexion"),
                    "torso_max_deg": value("torso_lean", "max_lean_angle"),
                    "knee_travel_x": value("knee_travel", "max_travel"),
                    "heel_rise_y": value("heel_lift", "max_lift"),
                    "total_seconds": value("timing", "total_seconds"),
                    "descent_seconds": value("timing", "descent_seconds"),
                    "bottom_seconds": value("timing", "bottom_seconds"),
                    "ascent_seconds": value("timing", "ascent_seconds"),
                    "exclusions_or_partial": " | ".join(reasons),
                }
                rows.append(row)
                if source_index is not None:
                    cap.set(cv2.CAP_PROP_POS_FRAMES, source_index)
                    success, frame = cap.read()
                    if not success:
                        continue
                    pose = extraction.pose_sequence[depth.deepest_index]
                    indices = side_landmarks(side)
                    width, height = extraction.image_size
                    points = {}
                    for name, index in indices.items():
                        landmark = pose[index]
                        if landmark.visibility >= analysis.features.visibility_threshold:
                            point = (int(landmark.x * width), int(landmark.y * height))
                            points[name] = point
                            cv2.circle(frame, point, 5, (0, 255, 255), -1)
                            cv2.putText(frame, name, point, cv2.FONT_HERSHEY_SIMPLEX, 0.4, (0, 255, 255), 1)
                    for first, second in (("shoulder", "hip"), ("hip", "knee"), ("knee", "ankle"), ("heel", "toe")):
                        if first in points and second in points:
                            cv2.line(frame, points[first], points[second], (0, 200, 0), 2)
                    cv2.putText(frame, f"{side.value} rep {number}, source {source_index}", (10, 25),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.55, (0, 255, 255), 2)
                    filename = f"{side.value}-rep-{number}-bottom.jpg"
                    if not cv2.imwrite(str(output / filename), frame):
                        raise OSError(f"Could not save {filename}")
                    images.append((filename, f"{side.value}, rep {number}, source frame {source_index}"))
    finally:
        cap.release()
    (output / "analysis.json").write_text(json.dumps(metadata, indent=2, allow_nan=False), encoding="utf-8")
    columns = list(rows[0]) if rows else ["side", "rep"]
    with (output / "repetitions.csv").open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)
    with (output / "candidates.csv").open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(candidate_rows[0]) if candidate_rows else ["side", "candidate"])
        writer.writeheader()
        writer.writerows(candidate_rows)
    parts = [
        '<!doctype html><html lang="en"><meta charset="utf-8">',
        f"<title>{html.escape(video.name)} review</title>",
        '<style>body{font:15px system-ui;margin:28px;color:#172030}table{border-collapse:collapse;font-size:12px}'
        'td,th{border:1px solid #ccd;padding:7px}th{background:#eef}img{max-width:360px;max-height:540px}'
        'figure{display:inline-block;vertical-align:top;margin:14px} .scroll{overflow:auto}</style>',
        f"<h1>{html.escape(video.name)}</h1>",
        f"<p>{extraction.source_frame_count} source frames; {len(extraction.pose_sequence)} pose frames; "
        f"{extraction.fps} FPS; {extraction.image_size}. Facing: {facing.value} (review input).</p>",
        f'<p>Primary model complexity: {model_complexity}; '
        f'recovery model: {metadata["recovery_model_complexity"]} (if enabled).</p>',
        f'<p>Source-image pose re-detections: {len(extraction.recovered_frame_indices)}. '
        'These remain marked for review even when source-frame coverage is complete. No coordinate interpolation was used.</p>',
        f'<p>Experimental options: {html.escape(str(metadata["experimental_options"]))}.</p>',
        '<p>Compare both sides manually. Rep counts are detector outputs, not verified ground truth. '
        'Gaps may split or exclude reps. Angles are 2D proxies. Foot normalization is withheld pending recording review.</p>',
        '<p>Units: angles in degrees; hip/knee gap and heel rise in image-height units; '
        'knee travel in image-width units. Missing values are shown as unavailable.</p>',
        '<p><a href="repetitions.csv">Measured reps CSV</a> | <a href="candidates.csv">Unverified candidates CSV</a> | '
        '<a href="analysis.json">Full measurements and coverage (JSON)</a></p>',
        '<p><b>Candidates are not counted as complete reps.</b> They cross short gaps (at most 0.2 seconds per gap), '
        'have no metric values or phase times, and are excluded from consistency. Their boundaries and observed bottom require review.</p>',
    ]
    for side, data in metadata["sides"].items():
        parts.append(f"<p><b>{side}: {len(data['repetitions'])} uninterrupted detected reps; {len(data['candidates'])} unverified candidates.</b> "
                     + html.escape(" ".join(data["issues"])) + "</p>")
    parts.append('<div class="scroll"><table><tr>' + ''.join(f"<th>{html.escape(key)}</th>" for key in columns) + '</tr>')
    for row in rows:
        parts.append('<tr>' + ''.join(
            '<td>' + html.escape("unavailable" if value is None else f"{value:.4f}" if isinstance(value, float) else str(value)) + '</td>'
            for value in row.values()
        ) + '</tr>')
    parts.append('</table></div><h2>Deepest observed frames</h2>')
    for filename, caption in images:
        parts.append(f'<figure><img src="{filename}" alt="{html.escape(caption)}"><figcaption>{html.escape(caption)}</figcaption></figure>')
    if candidate_rows:
        parts.append('<h2>Unverified gap-crossing candidates</h2><div class="scroll"><table><tr>')
        parts.extend(f'<th>{html.escape(name)}</th>' for name in candidate_rows[0])
        parts.append('</tr>')
        for row in candidate_rows:
            parts.append('<tr>' + ''.join(f'<td>{html.escape(str(value))}</td>' for value in row.values()) + '</tr>')
        parts.append('</table></div>')
        for filename, caption in candidate_images:
            parts.append(f'<figure><img src="{filename}" alt="{html.escape(caption)}"><figcaption>{html.escape(caption)}</figcaption></figure>')
    parts.append('</html>')
    (output / "index.html").write_text('\n'.join(parts), encoding="utf-8")
    print(json.dumps({"video": video.name, "source_frames": extraction.source_frame_count,
                      "pose_frames": len(extraction.pose_sequence),
                      "reps": {side: len(data["repetitions"]) for side, data in metadata["sides"].items()},
                      "candidates": {side: len(data["candidates"]) for side, data in metadata["sides"].items()},
                      "recovered_frames": len(extraction.recovered_frame_indices),
                      "report": str((output / "index.html").resolve())}), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("video", type=Path)
    parser.add_argument("--facing", required=True, choices=[direction.value for direction in FacingDirection])
    parser.add_argument("--output", type=Path)
    parser.add_argument("--reuse-extraction", action="store_true", help="Reuse a local pose cache if source size and mtime match")
    parser.add_argument("--recover-missing-poses", action="store_true", help="Opt in to source-image re-detection of bounded missing frames")
    parser.add_argument("--posture-calibration", action="store_true", help="Opt in to experimental standing-posture median and bottom P95 calibration")
    parser.add_argument("--model-complexity", type=int, choices=(0, 1, 2), default=1,
                        help="MediaPipe model (default 1); 0/2 may download official weights on first use")
    args = parser.parse_args()
    review_video(args.video, FacingDirection(args.facing), args.output or Path("artifacts/sample-review") / args.video.stem,
                 reuse_extraction=args.reuse_extraction, recover_missing_poses=args.recover_missing_poses,
                 posture_calibration=args.posture_calibration, model_complexity=args.model_complexity)


if __name__ == "__main__":
    main()
