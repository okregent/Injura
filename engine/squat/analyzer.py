"""Side-specific squat measurement orchestration, without feedback rules."""

from dataclasses import dataclass, field
import math
from typing import Dict, List, Optional

from engine.analyzer import ExerciseAnalyzer
from engine.pose.orientation import FacingDirection
from engine.pose.side import BodySide
from engine.pose.types import PoseExtractionResult
from engine.squat.assessment import MetricOutcome, assess_metric
from engine.squat.features import SquatFeatures, extract_squat_features
from engine.squat.phases import (
    SquatPhase, SquatPhaseThresholds, calculate_squat_phase_thresholds,
)
from engine.squat.reps import SquatRep, detect_squat_reps
from engine.squat.smoothing import smooth_squat_phases
from engine.squat.cycles import detect_cycle_phases, standing_posture_reference
from engine.squat.metrics.bottom_angles import calculate_bottom_joint_angles
from engine.squat.metrics.consistency import ConsistencyResult, calculate_consistency
from engine.squat.metrics.depth import calculate_squat_depth_from_features
from engine.squat.metrics.heel_lift import calculate_heel_lift
from engine.squat.metrics.hip_to_knee import calculate_hip_to_knee_depth
from engine.squat.metrics.knee_travel import calculate_knee_travel_from_features
from engine.squat.metrics.normalized_knee_travel import (
    KneeTravelRecordingConditions, calculate_normalized_knee_travel,
)
from engine.squat.metrics.timing import calculate_rep_timing
from engine.squat.metrics.torso_lean import calculate_torso_lean_from_features


@dataclass
class SquatRepAnalysis:
    rep: SquatRep
    metrics: Dict[str, MetricOutcome]


@dataclass
class SquatRepCandidate:
    rep: SquatRep
    deepest_observed_index: int
    missing_source_frames: int
    reason: str = "Tracking hypothesis across short gaps; requires manual review, not a confirmed repetition."


@dataclass
class SquatAnalysisResult:
    features: SquatFeatures
    phases: List[SquatPhase]
    repetitions: List[SquatRepAnalysis]
    consistency: Dict[str, ConsistencyResult]
    issues: List[str]
    candidates: List[SquatRepCandidate] = field(default_factory=list)
    calibration_method: str = "sequence_extrema"
    phase_thresholds: Optional[SquatPhaseThresholds] = None


class SquatAnalyzer(ExerciseAnalyzer):
    def analyze(
        self, extraction: PoseExtractionResult, *, side: BodySide,
        facing_direction: FacingDirection,
        recording_conditions: Optional[KneeTravelRecordingConditions] = None,
        visibility_threshold: float = 0.5, phase_min_duration: int = 3,
        heel_lift_threshold: float = 0.005,
        candidate_max_gap_seconds: float = 0.2,
        use_posture_calibration: bool = False,
    ) -> SquatAnalysisResult:
        """Analyze complete reps within uninterrupted, usable hip observations.

        Never interpolate or bridge missing source frames. Individual unavailable
        metrics do not discard other measurements. Recording review gates only
        foot normalization; other outputs remain side-view measurement proxies.
        """
        if extraction.image_size is None:
            raise ValueError("source image size is unavailable")
        if not isinstance(facing_direction, FacingDirection):
            raise ValueError("unsupported facing_direction")
        if not isinstance(phase_min_duration, int) or phase_min_duration < 1:
            raise ValueError("phase_min_duration must be a positive integer")
        if not math.isfinite(candidate_max_gap_seconds) or candidate_max_gap_seconds < 0:
            raise ValueError("candidate_max_gap_seconds must be finite and nonnegative")
        features = extract_squat_features(
            extraction.pose_sequence, side, visibility_threshold,
            image_size=extraction.image_size,
        )
        phases = [SquatPhase.UNKNOWN] * features.frame_count
        issues = []
        try:
            thresholds = calculate_squat_phase_thresholds(
                [value for value in features.hip_y_values if value is not None],
            )
        except ValueError as error:
            return SquatAnalysisResult(features, phases, [], {}, [str(error)])

        calibration_method = "sequence_extrema"
        if use_posture_calibration:
            standing, samples = standing_posture_reference(features)
            ordered = sorted(value for value in features.hip_y_values if value is not None)
            rank = .95 * (len(ordered) - 1)
            lower = int(rank)
            bottom = ordered[lower] + (rank - lower) * (ordered[min(lower + 1, len(ordered) - 1)] - ordered[lower])
            if standing is not None and standing < bottom:
                thresholds = SquatPhaseThresholds(standing, bottom, .03 * (bottom - standing))
                calibration_method = "posture_median_p95_experimental"
                issues.append(f"Experimental standing calibration uses {samples} near-extended-knee frames; requires review.")
            else:
                issues.append("Posture calibration unavailable; retained sequence-extrema calibration.")

        spans = []
        start = None
        source = extraction.source_frame_indices
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
            local = smooth_squat_phases(
                detect_cycle_phases(features.hip_y_values[start:stop], thresholds),
                min_duration=phase_min_duration,
            )
            phases[start:stop] = local
            reps.extend(
                SquatRep(rep.start_index + start, rep.bottom_index + start, rep.end_index + start)
                for rep in detect_squat_reps(local)
            )
        if len(extraction.pose_sequence) < extraction.source_frame_count or any(
            value is None for value in features.hip_y_values
        ):
            issues.append("Missing observations split rep detection; incomplete reps are excluded.")
        if not reps:
            issues.append("No complete repetitions detected.")

        # Candidate tracking may cross bounded gaps, but never produces measured
        # phases, metric values, or timings for those gaps. Complete reps above
        # still require uninterrupted valid observations.
        candidates = []
        if extraction.fps is not None and candidate_max_gap_seconds > 0:
            max_missing = int(extraction.fps * candidate_max_gap_seconds)
            groups = []
            group = []
            for index, value in enumerate(features.hip_y_values):
                if value is None:
                    continue
                if group and source[index] - source[group[-1]] - 1 > max_missing:
                    groups.append(group)
                    group = []
                group.append(index)
            if group:
                groups.append(group)
            for group in groups:
                local = detect_cycle_phases([features.hip_y_values[index] for index in group], thresholds)
                for candidate in detect_squat_reps(local):
                    indices = group[candidate.start_index:candidate.end_index + 1]
                    missing = source[indices[-1]] - source[indices[0]] + 1 - len(indices)
                    if not missing or any(
                        indices[0] <= rep.end_index and indices[-1] >= rep.start_index for rep in reps
                    ):
                        continue
                    mapped = SquatRep(indices[0], group[candidate.bottom_index], indices[-1])
                    deepest = max(indices, key=lambda index: features.hip_y_values[index])
                    candidates.append(SquatRepCandidate(mapped, deepest, missing))
            if candidates:
                issues.append(f"{len(candidates)} gap-crossing candidates require manual review; excluded from measurements and consistency.")

        analyses = []
        for rep in reps:
            metrics = {}

            def measure(name, masks, callback):
                try:
                    value = callback()
                    reason = None if value is not None else "angle unavailable at the deepest frame"
                except ValueError as error:
                    value, reason = None, str(error)
                metrics[name] = MetricOutcome(value, assess_metric(
                    features, extraction, rep, masks, available=value is not None, reason=reason,
                ))

            measure("depth", ["hip_y"], lambda: calculate_squat_depth_from_features(features, rep, thresholds))
            measure("hip_to_knee", ["hip_y", "knee"], lambda: calculate_hip_to_knee_depth(features, rep))
            measure("knee_flexion", ["hip_y", "knee_angle"], lambda: calculate_bottom_joint_angles(features, rep).knee_flexion_angle)
            measure("hip_flexion", ["hip_y", "hip_angle"], lambda: calculate_bottom_joint_angles(features, rep).hip_flexion_angle)
            measure("torso_lean", ["torso_angle"], lambda: calculate_torso_lean_from_features(features, rep))
            measure("knee_travel", ["knee", "toe"], lambda: calculate_knee_travel_from_features(features, rep, facing_direction))
            measure("normalized_knee_travel", ["knee", "toe", "foot_length"], lambda: calculate_normalized_knee_travel(
                features, rep, facing_direction, recording_conditions=recording_conditions,
            ))
            measure("heel_lift", ["heel_y", "toe"], lambda: calculate_heel_lift(
                features, rep, extraction, lift_threshold=heel_lift_threshold,
            ))
            heel = metrics["heel_lift"]
            if heel.value is not None and (
                heel.value.lifted_seconds is None or heel.value.timed_coverage < 1
            ):
                heel.quality.status = "partial"
                heel.quality.reason = "Heel-rise magnitude is available; duration is unavailable or only partly observed."
            measure("timing", ["hip_y"], lambda: calculate_rep_timing(extraction, phases, rep))
            analyses.append(SquatRepAnalysis(rep, metrics))

        consistency = {}
        for name, attribute in (
            ("depth", "depth_ratio"), ("torso_lean", "max_lean_angle"),
            ("knee_travel", "max_travel"), ("normalized_knee_travel", "normalized_travel"),
            ("timing", "total_seconds"),
        ):
            consistency[name] = calculate_consistency([
                getattr(item.metrics[name].value, attribute) if item.metrics[name].value is not None else None
                for item in analyses
            ])
        return SquatAnalysisResult(features, phases, analyses, consistency, issues, candidates,
                                   calibration_method, thresholds)
