# Injura — Exercise Module Architecture

## Modular Structure
```
ExerciseAnalyzer (Base)
├── SquatAnalyzer
├── DeadliftAnalyzer
├── PushupAnalyzer
└── Future Modules
```

## Design Rules
- Each exercise module independently manages movement rules, thresholds, and feedback logic
- Modules must be independently extendable without affecting others
- MVP implements SquatAnalyzer only

## Current Entry Point

`engine/analyzer.py` defines `ExerciseAnalyzer`; `engine/squat/analyzer.py`
implements `SquatAnalyzer` for extracted pose data:

```python
from engine.pose.orientation import FacingDirection
from engine.pose.side import BodySide
from engine.squat.analyzer import SquatAnalyzer

extraction = estimator.extract_with_metadata(video_path)
analysis = SquatAnalyzer().analyze(
    extraction,
    side=BodySide.LEFT,
    facing_direction=FacingDirection.RIGHT,
)
```

The result contains aligned features/phases, per-rep metric outcomes, consistency
summaries, and issues. Each outcome exposes `.value` and `.quality`; unavailable
measurements have `.value = None` and a reason. Foot normalization is withheld
unless the caller supplies externally verified recording conditions. The default
call intentionally makes no claim to have reviewed camera or foot orientation.

Missing source/hip observations split rep detection. Results are measurement
proxies; adaptive feedback remains a separate E4 responsibility. Refer to the
metric catalog for timing, baseline, coverage, and missing-data contracts.

## Measurement Availability Notices

On the implementation branch, `engine/squat/feedback.py` provides
`build_measurement_feedback(analysis)`. It returns Korean messages with stable
machine-readable `code`, `level` (`info`/`review`), and one-based measured
repetition/metric references including original quality reasons. Codes cover
detected/no complete cycles, gap candidates, experimental calibration,
unavailable/partial metrics, recovered observations, and measurement scope.

This is an E4 foundation for explaining existing results, not a technique rule
engine. It supplies no score, diagnosis, calibrated confidence, adaptive posture
thresholds, or automatic side/model selection. Candidates never become measured
repetitions or metric references. The function does not mutate analysis results.
`tools.review_samples` includes notices in each side's JSON and HTML, with
expandable evidence. Raw measurement values and provenance remain available.

Explicit numeric comparison rules are available separately; see
[measurement rule contract](measurement-rules.md). Default rules are empty and
adaptive/validated coaching thresholds remain pending.
