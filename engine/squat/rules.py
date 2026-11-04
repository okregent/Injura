"""Explicitly configured measurement rules; no built-in technique thresholds."""

import json
import math
import operator
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from engine.squat.analyzer import SquatAnalysisResult


TARGETS = {
    ("timing", "total_seconds"): "seconds",
    ("timing", "descent_seconds"): "seconds",
    ("timing", "bottom_seconds"): "seconds",
    ("timing", "ascent_seconds"): "seconds",
    ("knee_flexion", None): "degrees",
    ("hip_flexion", None): "degrees",
    ("torso_lean", "max_lean_angle"): "degrees",
    ("torso_lean", "lean_change"): "degrees",
    ("depth", "depth_ratio"): "ratio",
}
COMPARATORS = {"gt": operator.gt, "gte": operator.ge, "lt": operator.lt,
               "lte": operator.le, "eq": operator.eq, "ne": operator.ne}


@dataclass(frozen=True)
class MeasurementRule:
    id: str
    metric: str
    field: Optional[str]
    comparator: str
    threshold: float
    message: str
    enabled: bool = False

    def __post_init__(self):
        if not isinstance(self.id, str) or not self.id.strip():
            raise ValueError("rule id must be a nonempty string")
        if not isinstance(self.metric, str) or (self.field is not None and not isinstance(self.field, str)):
            raise ValueError("invalid metric target")
        if (self.metric, self.field) not in TARGETS:
            raise ValueError("unsupported metric target")
        if not isinstance(self.comparator, str) or self.comparator not in COMPARATORS:
            raise ValueError("unsupported comparator")
        if isinstance(self.threshold, bool) or not isinstance(self.threshold, (int, float)) or not math.isfinite(self.threshold):
            raise ValueError("threshold must be a finite number")
        if not isinstance(self.message, str) or not self.message.strip():
            raise ValueError("message must be a nonempty string")
        if not isinstance(self.enabled, bool):
            raise ValueError("enabled must be boolean")


@dataclass(frozen=True)
class RuleEvaluation:
    rule_id: str
    repetition: int
    metric: str
    field: Optional[str]
    comparator: str
    threshold: float
    unit: str
    status: str
    value: Optional[float]
    message: Optional[str]
    reason: Optional[str]


def load_rules(path: Path):
    data = json.loads(Path(path).read_text(encoding="utf-8-sig"))
    if not isinstance(data, dict) or set(data) != {"rules"} or not isinstance(data["rules"], list):
        raise ValueError("configuration must contain only a rules list")
    try:
        rules = [MeasurementRule(**item) for item in data["rules"]]
    except TypeError as error:
        raise ValueError("invalid rule fields") from error
    _unique_rules(rules)
    return rules


def _unique_rules(rules):
    if any(not isinstance(rule, MeasurementRule) for rule in rules):
        raise ValueError("rules must contain MeasurementRule values")
    if len({rule.id for rule in rules}) != len(rules):
        raise ValueError("duplicate rule ids")


def evaluate_rules(analysis: SquatAnalysisResult, rules):
    """Evaluate measured cycles only; withhold unsupported quality/calibration.

    A match means only that a caller's numeric condition holds. This is not
    validated coaching, a posture grade, or a medical inference. Experimental
    calibration is withheld conservatively; coverage alone is not accuracy.
    """
    rules = list(rules)
    _unique_rules(rules)
    results = []
    for number, repetition in enumerate(analysis.repetitions, 1):
        for rule in rules:
            status, value, message, reason = "withheld", None, None, None
            outcome = repetition.metrics.get(rule.metric)
            if not rule.enabled:
                status, reason = "disabled", "rule disabled"
            elif analysis.calibration_method.endswith("_experimental"):
                reason = "experimental calibration requires review"
            elif outcome is None or outcome.value is None:
                reason = outcome.quality.reason if outcome and outcome.quality.reason else "measurement unavailable"
            elif outcome.quality.status != "available" or outcome.quality.recovered_frames:
                reason = outcome.quality.reason or "measurement quality requires review"
            else:
                observed = getattr(outcome.value, rule.field, None) if rule.field else outcome.value
                if isinstance(observed, bool) or not isinstance(observed, (int, float)) or not math.isfinite(observed):
                    reason = "finite numeric measurement unavailable"
                else:
                    value = float(observed)
                    matched = COMPARATORS[rule.comparator](value, rule.threshold)
                    status = "matched" if matched else "not_matched"
                    message = rule.message if matched else None
            results.append(RuleEvaluation(rule.id, number, rule.metric, rule.field, rule.comparator,
                                          rule.threshold, TARGETS[(rule.metric, rule.field)],
                                          status, value, message, reason))
    return results
