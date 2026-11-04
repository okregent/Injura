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
