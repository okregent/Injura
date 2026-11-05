# Injura

Adaptive AI Squat Analyzer

Project documentation is maintained on `main`. The measurement engine described
below is implemented on `feature/biomechanics` and has not been merged into
`main`. Switch to that branch before running the analysis example.

The side-view measurement engine extracts squat repetitions and produces
per-repetition depth, joint angles, torso lean, knee travel, heel-rise proxies,
phase timing, data coverage, and between-repetition consistency.

Agreed E4 implementation is complete; see [scope and acceptance](docs/validation/E4_IMPLEMENTATION_ACCEPTANCE.md).
New filming and empirical E3 validation are deferred by the user. Measurement validation follows the
[supported recording conditions](docs/product/RECORDING_GUIDE.md), using the
[E3 acceptance gates](docs/validation/E3_ACCEPTANCE.md). Passing tests do not
establish measurement accuracy or injury-prevention efficacy. E4 includes capture/
quality-gated notices, projected profiles, descriptive personal baselines and session
summaries. Validated coaching and E5 API/mobile integration remain pending.
User-defined target-tempo functionality is deferred.

[Evaluation protocol v0.1](docs/validation/E3_PROTOCOL_v0.1.md) records initial
engineering limits and a source inventory. Existing clips are development data;
evaluation inputs/references remain pending and no accuracy pass is claimed.

The [E3 evaluation workflow](docs/architecture/e3-evaluation-workflow.md) now
provides `python -m tools.evaluate_e3` commands for registration, blind frame
review, readiness, input freeze, evaluation and local status reports. All data
outputs stay under ignored `artifacts/`; independent reference approval is required.

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

## Local sample review

On `feature/biomechanics`, run `python -m tools.review_samples sample_video3.mp4
--facing left`, then `python -m tools.build_review_index`. The generated local
report is `artifacts/sample-review/index.html`. Review candidates are separate
from measured repetitions and have no phase timing or metric values. See the
[initial sample investigation](docs/validation/sample-review-2026-11-04.md) for
the four-video results and limitations.

Experimental `--recover-missing-poses` and `--posture-calibration` options are opt-in.
`--model-complexity 2` selects Heavy; Full (`1`) remains the default. Recovery
uses the selected model and marks recovered-frame measurements as partial.
The investigation document includes reproduction commands, user count
references, and the limits of the Full/Heavy comparison. Count agreement alone
does not validate joint angles or other anatomical measurements.

Add `--robust-fallback` together with `--posture-calibration` to explicitly enable
the experimental P5/P95 position fallback when standing posture calibration is
unavailable. It is off by default. The report identifies the calibration used;
this option does not bridge missing frames or establish measurement accuracy.

`--rules PATH` explicitly loads configured JSON measurement conditions. Default
rules are empty; partial/unavailable measurements and experimental calibration
withhold evaluation. See [rule configuration](docs/architecture/measurement-rules.md).

Rule interpretation additionally requires a reviewed capture record, supplied
with `--recording-review PATH`. Missing review stays unknown and withholds rules;
raw measurements remain inspectable. See [recording review](docs/architecture/recording-review.md)
for source-bound templates and item-specific conditions.

`python -m tools.build_review_index` consolidates saved results in the Korean
local dashboard at `artifacts/sample-review/index.html`: per-video/side detected
cycles, separate candidates, metric availability counts, calibration/recovery,
and explicit model alternatives. It never sums sides or chooses a model.
