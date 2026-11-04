# Initial Sample Review: 2026-11-04

Implementation and commands refer to `feature/biomechanics`. Project documents
are maintained on `main`; this review does not imply an engine merge.

## Findings and Repairs

1. Frame-to-frame hip-coordinate jitter repeatedly reversed descent/ascent
   labels, so strict ordered phase timing was withheld. The analyzer now uses
   position-based cycle states and bottom-entry/exit hysteresis.
2. Returning to standing before reaching bottom left a pending descent open.
   The following rep inherited idle standing frames. Standing now cancels the
   incomplete descent and the next departure gets its own start index.
3. A span beginning mid-motion could previously count as a complete rep. The
   revised cycle state requires observed standing before descent.
4. Video 6 loses pose observations around squat bottoms. Missing observations
   still split measured detection. A separate bounded-gap tracker exposes review
   candidates without manufacturing measurements or filling missing frames.

## Results

All counts are detector outputs, not independently annotated ground truth.
Timing availability means all three phase durations were returned for an
uninterrupted detected rep; it does not establish boundary accuracy.

| Video | Side | Previous detections | Measured detections now | Review candidates | Previous / current timed reps |
|---|---|---:|---:|---:|---:|
| 3 | Left | 6 | 6 | 0 | 1 / 6 |
| 3 | Right | 6 | 6 | 0 | 1 / 6 |
| 4 | Left | 14 | 14 | 0 | 11 / 14 |
| 4 | Right | 14 | 14 | 0 | 13 / 14 |
| 5 | Left | 2 | 0 | 2 | 0 / 0 |
| 5 | Right | 2 | 0 | 1 | 0 / 0 |
| 6 | Left | 0 | 0 | 3 | 0 / 0 |
| 6 | Right | 0 | 0 | 3 | 0 / 0 |

Video 5's earlier detections are not retained as measured repetitions because
full standing-to-standing cycles are not uninterrupted in the observed data.
Video 6's candidates are hypotheses only. Preparation motion affects global
standing calibration and some candidate starts remain uncertain. Candidate
counts must not be combined across body sides or added to complete detections
as a verified repetition total.

## Reproduce Locally

Local videos are excluded from Git. From the repository root on the
implementation branch, use the configured project Python environment:

```bash
python -m tools.review_samples sample_video3.mp4 --facing left
python -m tools.review_samples sample_video4.mp4 --facing right
python -m tools.review_samples sample_video5.mp4 --facing left
python -m tools.review_samples sample_video6.mp4 --facing left
python -m tools.build_review_index
```

Output defaults to `artifacts/sample-review/`, ignored by Git on the development
branch. Each recording has an HTML report, measurements CSV, separate candidates
CSV, detailed JSON, observed-frame images, and a local pose-extraction cache.
Use `--reuse-extraction` to reuse a cache whose source size/mtime match. Regenerate
the cache after changing extraction settings. The comparison index can include
an optional previously saved `baseline-analysis.json`; baseline snapshots are
local artifacts, not annotations. Facing direction is a human review input.

## Validation and Remaining Work

- Full suite: 217 passed, including real-video integration. Existing dependency
  deprecation warnings remain.
- Regression coverage includes aborted descents, boundary chatter, initial
  partial motion, real double dips, short/long gaps, unknown FPS, missing hips,
  and an unobserved bottom that must not become an interpolated candidate.
- Independently annotate repetition counts and boundaries, then evaluate
  global calibration, detection errors, timing errors, and candidate usefulness.
- Foot normalization remains withheld without external recording review.
- Automatic camera/foot validation and calibrated accuracy confidence remain
  unfinished. No clinical interpretation or ground-contact claim is made.

## Follow-up: User References and Source-Image Recovery

The user reports video 3 as 6-7 depending on inclusion of the initial motion
that starts at bottom, then 14, 2, and 3 repetitions for videos 4, 5, and 6.
The full standing-to-standing interpretation for video 3 is 6; retain the user's
6-7 range in count references rather than silently declaring exact boundaries.
Local count annotations are compared with `tools.evaluate_counts`; this is
count-only agreement, not event matching, precision/recall, or timing validation.
`tools.prepare_manual_review` produces video playback and non-overwritten CSV
templates for independent annotation.

Opt-in source-image re-detection and posture calibration recover video 5's two
cycles with phase timing. Six missing poses are re-detected; two unresolved
source gaps remain outside those measured cycles. In Full-model video 6,
10/14 missing images produce accepted re-detections. Frames 309, 386, 450, and
468 remain unresolved because detection fails or anchor agreement is insufficient.

## Follow-up: Full vs Heavy on Video 6

Original frame/landmark inspection supports unstable landmark placement on the
same foreground lifter after occlusion; it does not establish a switch to a
different person. Across the four investigated gaps, mean hip displacement is
0.115-0.121 image-width units for Full and 0.007-0.048 for Heavy. These are selected
diagnostic displacements, not velocities or anatomical accuracy measurements.

| Primary and recovery configuration | Detected reps per side | Candidates per side | Phase timing |
|---|---:|---:|---|
| Full, no recovery | 0 | 3 | Unavailable |
| Full with Full recovery | 0 | 3 | Unavailable |
| Heavy, no recovery | 2 | 1 | Both detections |
| Heavy with Heavy recovery | 3 | 0 | All three detections |

All comparison runs request the same experimental posture calibration. Detection
confidence and association limits are unchanged. Heavy plus recovery re-detects
three missing source images; one measured repetition includes a re-detection and
is explicitly marked partial. Other remaining source gaps lie outside the
measured repetitions. Both sides lack valid bottom knee/hip angles, so those
values remain unavailable. Count agreement does not imply all metrics are usable.

### Reproduce the Model Comparison

Run on `feature/biomechanics` with local sample video 6. Heavy may download its
official weights on first use; it runs on the local machine. The default stays
Full. Model weights live in the ignored virtual environment.

```bash
python -m tools.review_samples sample_video6.mp4 --facing left --reuse-extraction --posture-calibration --recover-missing-poses
python -m tools.review_samples sample_video6.mp4 --facing left --model-complexity 2 --posture-calibration --output artifacts/sample-review/model-comparison/video6-heavy --reuse-extraction
python -m tools.review_samples sample_video6.mp4 --facing left --model-complexity 2 --posture-calibration --recover-missing-poses --output artifacts/sample-review/model-comparison/video6-heavy-recovered --reuse-extraction
python -m tools.build_model_comparison
python -m tools.build_review_index
```

Full local regression suite now passes **245 tests**, including real-video
integration, model selection, model-separated caching, source-change cache
invalidation, and matching the recovery model to primary extraction. Heavy is
still an experiment on these recordings; evaluate independent recordings and
annotated anatomy/boundaries before adopting a new default or feedback rules.
