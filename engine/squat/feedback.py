"""Explain measurement availability without judging technique or injury risk."""

from dataclasses import dataclass, field
from typing import List, Optional

from engine.squat.analyzer import SquatAnalysisResult


@dataclass(frozen=True)
class MetricReference:
    repetition: int  # One-based measured repetition, never a candidate.
    metric: str
    reason: Optional[str]


@dataclass(frozen=True)
class MeasurementFeedback:
    code: str
    level: str
    message: str
    references: List[MetricReference] = field(default_factory=list)


def build_measurement_feedback(analysis: SquatAnalysisResult) -> List[MeasurementFeedback]:
    """Return deterministic Korean notices with machine-readable evidence.

    No numeric posture thresholds, scores, diagnoses, or model/side selection.
    Availability and coverage do not establish anatomical accuracy. Candidates
    never supply metric references or count toward the measured-cycle summary.
    """
    count = len(analysis.repetitions)
    result = [MeasurementFeedback(
        "detected_cycles" if count else "no_complete_cycles", "info" if count else "review",
        f"완전한 반복 구간 {count}개를 검출했습니다."
        if count else "완전한 반복 구간을 검출하지 못했습니다. 영상과 검출 누락을 확인해 주세요.",
    )]
    if analysis.candidates:
        result.append(MeasurementFeedback(
            "gap_candidates", "review",
            f"누락 구간을 가로지르는 검토 후보 {len(analysis.candidates)}개가 있습니다. 후보는 측정 반복과 통계에서 제외됩니다.",
        ))
    if analysis.calibration_method.endswith("_experimental"):
        result.append(MeasurementFeedback(
            "experimental_calibration", "review",
            "실험용 보정 기준이 적용됐습니다. 반복 경계와 측정값을 영상과 함께 검토해 주세요.",
        ))
    unavailable, partial, recovered = [], [], []
    for number, repetition in enumerate(analysis.repetitions, 1):
        for name, outcome in repetition.metrics.items():
            reference = MetricReference(number, name, outcome.quality.reason)
            if outcome.value is None or outcome.quality.status == "unavailable":
                unavailable.append(reference)
            elif outcome.quality.status == "partial":
                partial.append(reference)
            if outcome.quality.recovered_frames:
                recovered.append(reference)
    for references, code, message in [
        (unavailable, "unavailable_metrics", "계산할 수 없는 측정 항목이 있습니다. 항목별 사유를 확인해 주세요."),
        (partial, "partial_metrics", "일부 측정 항목은 관측 자료가 제한적이거나 재검출을 포함해 검토가 필요합니다."),
        (recovered, "recovered_observations", "원본 프레임 재검출이 포함된 측정 항목이 있습니다. 해당 반복의 관절 표시를 확인해 주세요."),
    ]:
        if references:
            result.append(MeasurementFeedback(code, "review", message, references))
    result.append(MeasurementFeedback(
        "measurement_scope", "info",
        "관측 자료의 충족 여부는 측정 정확도를 보장하지 않습니다. 현재 결과는 자세 점수나 의학적 판단을 제공하지 않습니다.",
    ))
    return result
