"""Framework-independent E5 response adapter over the existing E3/E4 engine."""

import json
from dataclasses import asdict, is_dataclass

from engine.squat.feedback import build_feedback_cards, build_measurement_feedback
from engine.squat.overview import build_session_overview
from engine.squat.personal import summarize_session
from engine.squat.recording import REQUIREMENTS, recording_gate


def build_squat_response(analysis, extraction, *, source_sha256, facing,
                         recording_review=None, comparisons=(), baseline_requested=False):
    """Return a detached JSON-ready result for one explicit body side.

    The caller binds source content/extraction/analysis and verifies any supplied
    personal comparisons. This adapter provides no source or coaching approval.
    Invalid/nonfinite raw values fail serialization rather than silently changing
    measured values. No local paths, video bytes or pose landmarks are exposed.
    """
    if (not isinstance(source_sha256, str) or len(source_sha256) != 64
            or any(char not in '0123456789abcdef' for char in source_sha256)):
        raise ValueError('source SHA-256 required')
    if facing not in ('left', 'right'):
        raise ValueError('explicit facing required')
    source = extraction.source_frame_indices
    if len(source) != len(analysis.features.hip_y_values) or len(source) != len(analysis.phases):
        raise ValueError('analysis and extraction frame counts differ')

    def source_frame(index):
        if type(index) is not int or not 0 <= index < len(source):
            raise ValueError('analysis frame outside extraction')
        return source[index]

    def boundaries(rep):
        if not rep.start_index <= rep.bottom_index <= rep.end_index:
            raise ValueError('invalid repetition ordering')
        return dict(start=source_frame(rep.start_index), bottom_phase_end=source_frame(rep.bottom_index),
                    end=source_frame(rep.end_index))

    cards = build_feedback_cards(analysis, recording_review=recording_review)
    comparisons = list(comparisons)
    result = dict(schema_version=1, exercise='squat',
        source=dict(sha256=source_sha256, frame_count=extraction.source_frame_count,
                    pose_frame_count=len(source), fps=extraction.fps, image_size=extraction.image_size),
        selection=dict(side=analysis.features.side.value, facing=facing),
        overview=build_session_overview(analysis, cards, comparisons=comparisons, baseline_requested=baseline_requested),
        recording_gates={name: dict(zip(('status', 'reason'), recording_gate(name, recording_review, analysis.features.side)))
                         for name in REQUIREMENTS},
        feedback=dict(notices=build_measurement_feedback(analysis), cards=cards,
                      actions=summarize_session(cards), personal_comparisons=comparisons),
        repetitions=[dict(number=number, source_frames=boundaries(item.rep), metrics=item.metrics)
                     for number, item in enumerate(analysis.repetitions, 1)],
        candidates=[dict(source_frames=boundaries(item.rep), observed_bottom=source_frame(item.deepest_observed_index),
                         missing_source_frames=item.missing_source_frames, reason=item.reason)
                    for item in analysis.candidates],
        consistency=analysis.consistency,
        provenance=dict(calibration_method=analysis.calibration_method,
                        recovered_source_frames=extraction.recovered_frame_indices, issues=analysis.issues),
        interpretation=dict(accuracy='not_validated', coaching='pending_validation',
                            scope='2D measurement proxies and descriptive feedback; no posture score or medical judgment'))

    def encode(value):
        if is_dataclass(value):
            return asdict(value)
        raise TypeError('unsupported response value: ' + type(value).__name__)

    # Round-trip enforces real JSON, rejects NaN/Infinity and detaches nested data.
    return json.loads(json.dumps(result, default=encode, allow_nan=False))
