"""Selected-side display coordinates, not new measurements or confidence."""

import math

from engine.pose.side import side_landmarks


def build_side_overlay(extraction, side, visibility_threshold=.5):
    if (isinstance(visibility_threshold, bool) or not isinstance(visibility_threshold, (int, float))
            or not math.isfinite(visibility_threshold) or not 0 <= visibility_threshold <= 1):
        raise ValueError('visibility threshold must be between zero and one')
    if len(extraction.pose_sequence) != len(extraction.source_frame_indices):
        raise ValueError('overlay pose/source frame counts differ')
    selected = side_landmarks(side)
    recovered = set(extraction.recovered_frame_indices)
    frames = []
    for source, landmarks in zip(extraction.source_frame_indices, extraction.pose_sequence):
        points = {}
        for name, index in selected.items():
            point = landmarks[index] if index < len(landmarks) else None
            values = (point.x, point.y, point.visibility) if point else ()
            valid = (point is not None and source not in recovered
                     and all(isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value) for value in values)
                     and 0 <= point.x <= 1 and 0 <= point.y <= 1
                     and visibility_threshold <= point.visibility <= 1)
            points[name] = dict(x=float(point.x), y=float(point.y)) if valid else None
        frames.append(dict(source_frame=source, points=points,
                           status='recovered_not_shown' if source in recovered else 'observed'))
    return dict(schema_version=1, side=side.value, image_size=extraction.image_size,
                visibility_threshold=visibility_threshold, frames=frames,
                scope='Normalized selected-side image coordinates; gaps are not interpolated; visibility is not accuracy.')
