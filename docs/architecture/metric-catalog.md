# Squat Metric Catalog

This document defines the current measurement contract for squat metrics.
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
  length after the preprocessing contract is finalized.

## Planned MVP Measurements

The following measurements are part of the side-view MVP but are not yet
implemented:

- Hip-to-knee depth at the bottom
- Knee flexion angle at the bottom
- Hip flexion angle at the bottom
- Body-segment-normalized knee travel
- Heel lift magnitude, duration, and timing
- Descent, bottom, ascent, and total rep duration
- Rep-to-rep depth, tempo, torso-angle, and knee-travel consistency
- Per-metric validity and analysis confidence

## Feedback Inferences

The following are not standalone metrics. They will be produced by the feedback
engine from multiple measurements and must use conservative language:

- Possible trunk collapse
- Possible ankle mobility limitation
- Excessive movement variability
- Compensation patterns

Hip shift, knee valgus, and left-right asymmetry are deferred because they
require front, rear, or multi-view input.
