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

## Follow-up: Heavy on Videos 3-5

Compared all four videos with identical experimental posture calibration,
unchanged confidence/association thresholds, and model-matched source-image
recovery. Facing direction is the reviewed input: right for video 4, left for
3/5/6. User count references are displayed only, never supplied to analysis.

| Video | User reference | Full + retry, left/right | Heavy + retry, left/right | Heavy candidates, left/right |
|---|---|---|---|---|
| 3 | 6-7, starts at bottom | 6 / 6 | 5 / 5 | 1 / 1 |
| 4 | 14 | 14 / 14 | 11 / 14 | 0 / 0 |
| 5 | 2 | 2 / 2 | 1 / 1 | 1 / 1 |
| 6 | 3 | 0 / 0 | 3 / 3 | 0 / 0 |

Heavy without recovery produces 1/1, 11/14, 0/0, and 2/2 complete detections
respectively. Full without recovery but WITH posture calibration produces
6/6, 14/14, 1/1, and 0/0; earlier baseline results used different calibration.
Heavy retry recovers 9/0/3/3 frames across videos 3/4/5/6. A greater total pose
coverage therefore does not necessarily yield more complete repetitions.

Bottom knee and hip angles are available on the left for all detected reps in
videos 3/5 and on the right for all 14 detections in video 4, for both models.
The opposite sides fail quality checks; video 6 lacks these angles on both
sides even with Heavy. Inspected representative bottom overlays from videos
3/4/5. This is visual review, not joint-coordinate or angle ground truth.

Keep Full as default: Heavy improves the count on video 6 but regresses on
other recordings. Do not automatically select a model or body side using the
known counts. Next investigate the remaining gaps in videos 3/5 and the
left-side cycle/calibration differences in video 4 against annotated frames.

To reproduce, run the Heavy recovery command above for each video 3-5, changing
the input and output directory to `videoN-heavy-recovered`; use `--facing right`
for video 4. Then run `python -m tools.build_batch_comparison`. This reads both
raw/recovered model caches and writes local `model-comparison/batch-comparison.html`
and CSV. Model/recovery targeted regression tests: **19 passed**. The prior
full suite result remains 245 passed; engine behavior was not changed here.

## Failure Diagnosis: Heavy Gaps and Video 4 Side Differences

Reproduced the remaining Heavy failures without modifying production parameters.
Video 3's candidate spans source 417-484 and retains missing frame 444;
video 5's candidates span 213-255 (left) / 218-251 (right) and retain frame 230.
Both images decode successfully. Repeating recovery on the original bounding
anchors (442/445 and 229/231) reproduces the gaps. Video 3 recovers 443 but not
444; video 5 recovers neither proposal at 230. No proposed pose is rejected by
the association guard in these isolated runs. Thus these targets fail to yield
a usable 33-landmark proposal, rather than being discarded by association.
Original images show upper-body occlusion by the plate; this does not establish
the precise internal reason for detector failure. Missing frames remain missing.

Video 4 has no missing source/hip observations. Heavy's left side falls back to
sequence extrema because posture calibration is unavailable; the right uses
posture median/P95. Left standing/bottom-entry cutoffs are 0.489409/0.613386;
right cutoffs are 0.539181/0.653438 (source-normalized hip y).

- The right's first repetition (5-26) has no preceding left standing state;
  left remains UNKNOWN through frame 25.
- The windows 36-70 and 240-280 have left hip maxima 0.610626 and 0.606664,
  below the left bottom-entry cutoff. Descents return to standing without a
  detected bottom, explaining the other two omitted repetitions.
- Other matched repetitions can still have different boundaries: for example,
  left 366-409 versus right 380-409. Count agreement is not timing validation.

`python -m tools.build_model_diagnostics` creates local original-frame strips,
the observed hip/threshold plot, per-frame phase CSV, isolated retry JSON, and
`model-comparison/diagnostics/index.html`. The plot and representative source
images were visually inspected. No interpolation, threshold relaxation, automatic
side/model choice, or engine behavior change was introduced. Next work should
annotate boundaries and visible joints, then evaluate calibration changes on
independent recordings; do not tune to these known counts.

## Exact Source-Frame Boundary Review

Run `python -m tools.prepare_boundary_review` on the implementation branch.
It decodes all 2,059 source frames from videos 3-6 to local JPEG inspection
images and creates `artifacts/sample-review/boundary-review/index.html`.
The tool validates decoded frame counts against the current analysis. Source
size/mtime identify image folders and browser annotation storage; image changes
at unchanged file metadata are outside this cache contract.

Select a recording, step one frame at a time, and mark departure from standing,
deepest physical posture, and return to standing. Record reviewer/uncertainty
notes, add rows, then export `boundary-annotations-reviewed.csv`. For plateaus,
record the chosen convention in notes. Partial initial/final motions and setup
are not complete repetitions. Leave uncertain boundaries blank with an explanation.
Seconds are informational and assume constant FPS; source indices come directly
from sequential decoding rather than player-time rounding.

No model boundaries are prefilled, and no actual annotations have yet been
confirmed by this tool. Browser rows are convenience drafts; export a portable
copy and reconcile with the existing annotation CSV. Existing annotations are
never overwritten. UI logic smoke checks covered empty initial labels, frame
clamping, reviewer requirements, invalid ordering, partial-boundary notes, and
CSV export. Python compile and Git whitespace checks passed. No engine behavior
or model defaults changed; this step prepares human reference collection.
