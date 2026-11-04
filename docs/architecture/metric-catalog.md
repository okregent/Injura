# Squat Metric Catalog

This document defines the current measurement contract for squat metrics.
Implemented metrics below refer to `feature/biomechanics`, not the code currently
on `main`. Documents are maintained on `main` independently of engine merges.
Metrics return explainable measurements only. User-specific interpretation and
feedback belong to the future feedback engine.

## Shared Input Contract

- Metric indices use pose-sequence indices and are inclusive.
- `SquatRep.start_index` and `SquatRep.end_index` define the search window.
- `SquatRep.bottom_index` is the final frame classified as `BOTTOM`; it is not
  guaranteed to be the physical deepest frame.
- Callers own landmark visibility validation and signal preprocessing.
- `MediaPipePoseEstimator.extract_with_metadata()` must be used whenever a
  result needs to map back to an original video frame.
- Metrics must preserve raw values and representative indices. Threshold-based
  labels do not belong in this layer.

## Derived-Feature Preprocessing

`extract_squat_features()` converts a `PoseSequence` into aligned, side-specific
feature sequences before metric calculation.

- The caller explicitly selects `BodySide.LEFT` or `BodySide.RIGHT`.
- The caller must supply `image_size=(width, height)` in pixels, available from
  `extract_with_metadata().image_size` when a video frame was decoded. An empty
  or unreadable video has no image size and must not be passed to preprocessing.
- Angle and length calculations use `(x, y * height / width)`, putting both axes
  in image-width units. Raw hip/heel y and knee/toe landmarks retain their
  original image-normalized coordinates.
- Knee and hip flexion are `180 - joint interior angle` in degrees: extension
  is 0 degrees and bending increases the value. These are unsigned 2D proxies;
  they do not distinguish hyperextension.
- Foot length is measured in image-width units, suitable as the denominator
  for image-normalized horizontal knee travel.
- Side selection remains fixed for the whole sequence.
- The default landmark visibility threshold is `0.5`.
- A landmark is usable only when its x, y, z, and visibility values are finite
  and its visibility meets the threshold.
- Invalid frames are preserved as `None`; preprocessing never removes a frame.
- Every feature has an aligned boolean valid mask and valid-frame ratio.
- Degenerate angles and zero-length foot measurements are invalid.
- Automatic side selection and missing-value interpolation are intentionally
  deferred until their policies can be validated.

Example using extracted video metadata:

```python
result = estimator.extract_with_metadata(video_path)
if result.image_size is None:
    raise ValueError("No video frame was decoded")
features = extract_squat_features(
    result.pose_sequence,
    side=BodySide.LEFT,
    image_size=result.image_size,
)
```

Current derived features:

- Selected-side hip y-position
- Torso angle from vertical
- Knee flexion angle
- Hip flexion angle
- Knee and toe landmarks
- Heel y-position
- Heel-to-toe foot length

## Relative Hip Descent

- **Status:** IMPLEMENTED (MVP proxy)
- **Implementation:** `engine/squat/metrics/depth.py`
- **Feature entry point:** `calculate_squat_depth_from_features(features, rep,
  thresholds)` uses `hip_y_values` and `valid_masks["hip_y"]`. Thresholds must
  come from the same selected-side hip signal. The existing
  `calculate_squat_depth()` entry point remains available.
- **Missing-data policy:** Skip `None` and masked frames inside the inclusive
  repetition window without compacting indices or interpolating. Raise
  `ValueError` if no valid hip value remains in that repetition. Results describe
  observed valid frames; a missing deepest frame can underestimate depth.
- **Purpose:** Compare descent magnitude across reps in one calibrated sequence.
- **Required view:** Side view
- **Input:** Hip y-value sequence, repetition window, phase thresholds
- **Output:** Relative descent ratio, deepest analysis index, raw calibration
  values
- **Definition:** `(deepest_hip_y - standing_y) / (bottom_y - standing_y)`
- **Limitations:** This is not an absolute biomechanical squat-depth
  assessment. The calibration extrema come from the analyzed sequence, and
  values are intentionally not clamped.
- **Future direction:** Add a distinct hip-to-knee depth metric for absolute
  posture interpretation while retaining this metric for rep consistency.

## Torso Lean

- **Status:** IMPLEMENTED (MVP measurement)
- **Implementation:** `engine/squat/metrics/torso_lean.py`
- **Feature entry point:** `calculate_torso_lean_from_features(features, rep)`
  uses `torso_angles` and `valid_masks["torso_angle"]`. The existing
  `calculate_torso_lean()` entry point remains available.
- **Missing-data policy:** Skip `None` and masked frames without changing
  indices or interpolating. Raise `ValueError` if the repetition contains no
  valid angle or its start frame is invalid. Do not substitute a later frame
  for the rep-start baseline. Missing interior frames can hide the true maximum.
- **Purpose:** Measure the largest torso inclination and its change during a rep.
- **Required view:** Side view
- **Input:** Torso-angle sequence in degrees from vertical, repetition window
- **Output:** Maximum angle, representative analysis index, rep-start angle,
  angle change
- **Limitations:** The rep-start frame is not necessarily a stable standing
  baseline. Visibility and smoothing are caller responsibilities.
- **Future direction:** Use a calibrated standing-window baseline and retain
  bottom-frame and maximum values separately.

## Knee Travel

- **Status:** IMPLEMENTED (MVP proxy)
- **Implementation:** `engine/squat/metrics/knee_travel.py`
- **Feature entry point:** `calculate_knee_travel_from_features(features, rep,
  facing_direction)` uses knee/toe landmarks and both corresponding valid masks.
  Facing direction is explicitly supplied, independently of `BodySide`.
- **Missing-data policy:** Use only same-frame pairs where both landmarks are
  present and both masks are true. Preserve indices without interpolation and
  raise `ValueError` if no pair is valid inside the repetition. A missing peak
  frame can underestimate the maximum. The existing raw-input API remains available.
- **Purpose:** Measure signed forward knee displacement relative to the toe.
- **Required view:** Side view and facing direction
- **Input:** Knee and toe landmark sequences, repetition window, facing
  direction
- **Output:** Maximum signed travel, representative analysis index, raw x
  coordinates
- **Units:** MediaPipe image-normalized x-coordinate difference
- **Limitations:** Camera framing and subject distance affect the value. It must
  not be treated as a cross-video score.
- **Future direction:** Normalize by a stable body segment such as foot or shin
  length. A separate foot-normalized entry point is now available below.

## Foot-Normalized Knee Travel

- **Status:** IMPLEMENTED (side-view 2D proxy)
- **Implementation:** `engine/squat/metrics/normalized_knee_travel.py`
- **Entry point:** `calculate_normalized_knee_travel(features, rep, facing_direction,
  recording_conditions=conditions)`
- **Recording gate:** `KneeTravelRecordingConditions(side_view=True,
  foot_side_on=True)` must reflect external review of this repetition. Default
  conditions are unknown. Both flags must be explicitly true; otherwise raise
  `KneeTravelNormalizationUnavailable` without producing a normalized value.
  Its `reason` distinguishes `side_view_unverified`, `not_side_view`,
  `foot_orientation_unverified`, and `foot_not_side_on`; `raw_result` retains
  the image-coordinate measurement for callers that still need it.
- **Verification boundary:** This is a required review gate, not an automatic
  recording classifier. Landmark visibility and a nonzero projected foot length
  cannot establish side-on orientation. A UI or caller must obtain recording
  review; do not set both flags automatically. Automated view/foot-orientation
  validation remains pending until a detector is independently validated.
- **Definition:** Maximum signed knee-over-toe x displacement divided by the
  median valid heel-to-toe 2D length inside the inclusive repetition window.
  Both numerator and denominator use image-width units.
- **Output:** Dimensionless `normalized_travel`, `reference_foot_length`,
  `reference_frame_count`, and the unchanged `raw_result` including peak index.
  A value of 0.5 means the observed peak exceeds the toe by half a reference
  foot length; negative values mean the knee remains behind the toe.
- **Reference policy:** Use one fixed denominator per rep. Ignore missing,
  masked, non-finite, and non-positive foot lengths. The heel need not be visible
  at the peak if another frame in the rep supplies a valid length. Raise
  `ValueError` when no usable reference remains; do not use another rep's frames.
- **Limitations:** Reduces uniform image-scale dependence; does not correct
  perspective, foot rotation, or landmark error. A single valid reference is
  allowed and exposed through the frame count; confidence scoring is deferred.
  Missing knee/toe peak frames can still underestimate travel.

## Joint Flexion at the Deepest Observed Frame

- **Status:** IMPLEMENTED (side-view 2D measurements)
- **Implementation:** `engine/squat/metrics/bottom_angles.py`
- **Entry point:** `calculate_bottom_joint_angles(features, rep)`
- **Bottom selection:** Find maximum finite, unmasked hip y in the inclusive
  rep window; use the first frame on ties. Do not use `rep.bottom_index`, which
  denotes the final BOTTOM phase frame, or independently maximize each angle.
- **Output:** `deepest_index`, `deepest_hip_y`, `knee_flexion_angle`, and
  `hip_flexion_angle`. Angles are degrees, with extension at 0 degrees.
- **Missing-data policy:** Return `None` independently for each angle missing,
  masked, or non-finite at the selected frame. Never borrow another frame's
  angle. Raise `ValueError` if no usable hip position identifies a bottom.
- **Limitations:** The bottom is the deepest observed hip position; missing
  frames can hide the actual bottom. These projected measurements assume a
  suitable side view and do not assess recording orientation automatically.

## Hip-to-Knee Depth

- `calculate_hip_to_knee_depth(features, rep)` returns the deepest observed
  frame and signed `vertical_gap = hip_y - knee_y` in image-height units.
- Positive means the estimated hip joint center is lower than the estimated
  knee center. These landmarks are not the anatomical hip crease or knee surface,
  and the result is not a competition-depth classification.
- Missing knee data at the selected frame makes this measurement unavailable;
  do not replace it with a neighboring frame. Camera orientation remains an
  input assumption.

## Heel-Rise Proxy

- `calculate_heel_lift(features, rep, extraction=None, lift_threshold=0.005)`
  compares `(toe_y - heel_y)` to its valid rep-start baseline. Maximum positive
  change and its first frame are returned in image-height units.
- The start must show a planted foot for physical interpretation. Shared image
  translation cancels, but perspective, foot rotation, and an already raised
  starting heel remain limitations. This is not proof of ground-contact loss.
- The threshold is a configurable image-coordinate noise tolerance, not a
  biomechanical or medical cutoff. Camera framing affects it.
- When FPS is known, `lifted_seconds` sums source-frame intervals above threshold
  at their left endpoint only when both endpoints are valid and adjacent in the
  source. Gaps are excluded. `timed_coverage` reports observed intervals divided
  by elapsed source intervals; duration is a lower-bound observation when partial.
  No FPS or no usable interval gives `None`, not zero seconds.

## Phase Timing

- `PoseExtractionResult.fps` preserves positive finite FPS, or `None` when the
  decoder cannot provide it. Original frame indices remain authoritative.
- `calculate_rep_timing(extraction, phases, rep)` measures half-open intervals
  `[start, end)`: end is the first return-to-standing/lockout frame. Total time
  is `(source_end - source_start) / fps`; no extra endpoint frame is added.
- Require consecutive source frames and ordered DESCENDING, BOTTOM, ASCENDING
  runs. Reject missing source frames, unknown/reordered phases, or unknown FPS.
  The three phase durations sum to total duration. Variable-frame-rate timestamp
  support is deferred; these times assume constant frame rate.

## Repetition Consistency

- `calculate_consistency(values)` returns finite sample count, total count,
  mean, population standard deviation, and range in the metric's original units.
- At least two available repetitions are required for variation; otherwise
  standard deviation and range are `None`. No good/bad classification or
  coefficient of variation is used, especially for signed or near-zero values.

## Integrated Analysis and Data Quality

- `SquatAnalyzer` implements `ExerciseAnalyzer`. Call `analyze(extraction,
  side=BodySide.LEFT, facing_direction=FacingDirection.RIGHT,
  recording_conditions=...)` after pose extraction.
- It calibrates phase thresholds using the selected-side valid hip signal,
  detects reps separately in uninterrupted source/hip spans, and never bridges
  missing pose or hip frames. No missing-feature interpolation is performed.
- Each rep includes depth, hip-to-knee gap, knee/hip bottom angles, torso lean,
  raw and normalized knee travel, heel rise, and timing as separate outcomes.
  Expected missing-data failures yield unavailable results plus reasons; other
  measurements continue. Partial heel-duration observation is explicitly marked.
- Quality contains valid and expected frame counts, observed coverage, and
  available/partial/unavailable status. Coverage uses inclusive original source
  frames and the required feature masks. It is data support, NOT calibrated
  confidence, accuracy probability, or confirmation of suitable camera geometry.
- The analyzer summarizes between-rep depth, total tempo, torso angle, raw knee
  travel, and normalized knee travel. Clinical/empirical confidence calibration,
  automatic camera/foot validation, automatic side selection, adaptive feedback,
  and video upload/mobile UI remain future work.

## Feedback Inferences

The following are not standalone metrics. They will be produced by the feedback
engine from multiple measurements and must use conservative language:

- Possible trunk collapse
- Possible ankle mobility limitation
- Excessive movement variability
- Compensation patterns

Hip shift, knee valgus, and left-right asymmetry are deferred because they
require front, rear, or multi-view input.
