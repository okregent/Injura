"""Opt-in image-based pose re-detection for short, bounded extraction gaps."""

import math
from dataclasses import replace

import cv2

from engine.pose.types import Landmark, PoseExtractionResult


def _compatible(points, before, after, image_size, max_distance, visibility):
    """Association guard using shared hip positions, not interpolated outputs."""
    width, height = image_size
    scores = []
    for index in (23, 24):
        trio = [points[index], before[index], after[index]]
        if all(p.visibility >= visibility and all(math.isfinite(v) for v in (p.x, p.y, p.z, p.visibility)) for p in trio):
            distance = max(
                math.hypot(points[index].x - anchor.x, (points[index].y - anchor.y) * height / width)
                for anchor in (before[index], after[index])
            )
            scores.append(distance)
    if not scores or max(scores) > max_distance:
        return None
    return sum(scores) / len(scores)


def recover_pose_gaps(
    video_path: str, extraction: PoseExtractionResult, *, max_gap_seconds: float = 0.2,
    max_hip_distance: float = 0.08, visibility_threshold: float = 0.5,
) -> PoseExtractionResult:
    """Retry actual missing source images at unchanged 0.5 detection confidence.

    Try the full image and a padded neighboring-person crop, choosing the result
    closest to both observed hip anchors. Accept only bounded short gaps. Crop
    landmarks map back to source-normalized coordinates. No coordinates are
    interpolated and original detections are never replaced. Association limits
    are engineering defaults, not validated identity/confidence guarantees.
    """
    if not math.isfinite(max_gap_seconds) or max_gap_seconds < 0:
        raise ValueError("max_gap_seconds must be finite and nonnegative")
    if not math.isfinite(max_hip_distance) or max_hip_distance <= 0:
        raise ValueError("max_hip_distance must be finite and positive")
    if not 0 <= visibility_threshold <= 1:
        raise ValueError("visibility_threshold must be between 0 and 1")
    if extraction.fps is None or extraction.image_size is None:
        raise ValueError("pose recovery requires source FPS and image size")
    source = extraction.source_frame_indices
    limit = int(extraction.fps * max_gap_seconds)
    gaps = [(i, a, b) for i, (a, b) in enumerate(zip(source, source[1:])) if 0 < b - a - 1 <= limit]
    if not gaps:
        return replace(extraction)

    import mediapipe as mp
    detector = mp.solutions.pose.Pose(
        static_image_mode=True, model_complexity=1, smooth_landmarks=False,
        min_detection_confidence=0.5,
    )
    cap = cv2.VideoCapture(video_path)
    frames = dict(zip(source, extraction.pose_sequence))
    recovered = set(extraction.recovered_frame_indices)
    width, height = extraction.image_size
    try:
        for pos, start, end in gaps:
            before, after = extraction.pose_sequence[pos:pos + 2]
            anchors = [p for frame in (before, after) for p in frame
                       if p.visibility >= visibility_threshold and math.isfinite(p.x) and math.isfinite(p.y)]
            crop = None
            if anchors:
                xs, ys = [p.x * width for p in anchors], [p.y * height for p in anchors]
                pad = .25 * max(max(xs) - min(xs), max(ys) - min(ys))
                bounds = (max(0, int(min(xs) - pad)), max(0, int(min(ys) - pad)),
                          min(width, int(max(xs) + pad)), min(height, int(max(ys) + pad)))
                if bounds[2] > bounds[0] and bounds[3] > bounds[1]:
                    crop = bounds
            for index in range(start + 1, end):
                cap.set(cv2.CAP_PROP_POS_FRAMES, index)
                success, image = cap.read()
                if not success or image.shape[:2] != (height, width):
                    continue
                proposals = []
                for x0, y0, x1, y1 in [(0, 0, width, height)] + ([crop] if crop else []):
                    result = detector.process(cv2.cvtColor(image[y0:y1, x0:x1], cv2.COLOR_BGR2RGB))
                    if result.pose_landmarks is None or len(result.pose_landmarks.landmark) != 33:
                        continue
                    points = [Landmark(
                        (p.x * (x1 - x0) + x0) / width,
                        (p.y * (y1 - y0) + y0) / height,
                        p.z * (x1 - x0) / width, p.visibility,
                    ) for p in result.pose_landmarks.landmark]
                    score = _compatible(points, before, after, extraction.image_size, max_hip_distance, visibility_threshold)
                    if score is not None:
                        proposals.append((score, points))
                if proposals:
                    frames[index] = min(proposals, key=lambda item: item[0])[1]
                    recovered.add(index)
    finally:
        cap.release()
        detector.close()
    indices = sorted(frames)
    return replace(extraction, pose_sequence=[frames[i] for i in indices], source_frame_indices=indices,
                   recovered_frame_indices=sorted(recovered))
