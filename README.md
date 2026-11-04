# Injura

Adaptive AI Squat Analyzer

The side-view measurement engine extracts squat repetitions and produces
per-repetition depth, joint angles, torso lean, knee travel, heel-rise proxies,
phase timing, data coverage, and between-repetition consistency.

## Analyze a recording

Use the project Python 3.9 environment with `requirements.txt` installed:

```python
from engine.pose.mediapipe_estimator import MediaPipePoseEstimator
from engine.pose.orientation import FacingDirection
from engine.pose.side import BodySide
from engine.squat.analyzer import SquatAnalyzer

estimator = MediaPipePoseEstimator()
try:
    extraction = estimator.extract_with_metadata("squat.mp4")
    analysis = SquatAnalyzer().analyze(
        extraction,
        side=BodySide.LEFT,
        facing_direction=FacingDirection.RIGHT,
    )
finally:
    estimator.close()

for repetition in analysis.repetitions:
    depth = repetition.metrics["depth"]
    print(depth.value, depth.quality.status, depth.quality.reason)
```

Choose the body side and facing direction for the actual recording. Foot-length
normalization is withheld by default until camera and foot orientation have
been externally reviewed. Coverage is observed data support, not accuracy
probability. FPS-based timing assumes constant frame rate.

See [metric contracts](docs/architecture/metric-catalog.md),
[analyzer usage](docs/architecture/exercise-modules.md), and
[project status](docs/management/PROJECT_STATUS.md) for limitations and next steps.

## Validation

Run `python -m pytest -q`. Three video-dependent tests require local sample
recordings (`sample_video.mp4`, `sample_video2.mp4`); video files are excluded
from Git. For the core suite without these tests:

```bash
python -m pytest -q --ignore=tests/test_pose_estimator.py --ignore=tests/test_squat_pipeline.py
```

Some existing video tests contain machine-specific paths. Update those paths
when setting up another computer.
