# Engine Progress

Tracks the build-out of the Injura analysis engine across MVP phases E1–E5.
Update this file whenever a task is started, completed, or a phase status changes.

---

## Overview

| Phase | Name                      | Status         |
|-------|---------------------------|----------------|
| E1    | Semantic Pose Foundation  | ✅ Completed    |
| E2    | Biomechanics Foundation   | ✅ Completed    |
| E3    | Squat Movement Analysis   | 🚧 In Progress  |
| E4    | Feedback Engine           | ✅ Agreed implementation complete; coaching validation deferred |
| E5    | Visualization & UX        | 🚧 Local API/browser preview; product timeline/mobile pending |

---

## Current Focus

**Phase: E4 implementation closure; E3 empirical validation deferred**
**Current task:** E5 [local API and browser preview](../architecture/e5-local-api.md) are implemented and tested. E4 agreed implementation remains complete; new filming/E3 evaluation and validated coaching remain deferred. Product timeline/mobile and production integration remain pending.

See [recording guide](../product/RECORDING_GUIDE.md) and
[E3 acceptance gates](../validation/E3_ACCEPTANCE.md). Core implementation is
complete; empirical validation is not. Test counts are not accuracy claims.

---

## E1 — Semantic Pose Foundation ✅

Convert raw MediaPipe indices into semantic abstractions.

- [x] `PoseLandmark` IntEnum — named joint access (`engine/pose/landmarks.py`)
- [x] Accessor helpers — `get_landmark()`, `get_landmarks()` (`engine/pose/accessors.py`)
- [x] Kinematic chain definitions — leg, arm, torso chains (`engine/pose/chains.py`)
- [x] Package exports updated (`engine/pose/__init__.py`)
- [x] Tests — `test_landmark_accessor.py`, `test_pose_package_exports.py`

---

## E2 — Biomechanics Foundation ✅

Convert semantic landmarks into biomechanics-aware mathematical representations.

- [x] Vector utilities — `to_vector`, `vector_length`, `dot_product` (`engine/biomechanics/vector.py`)
- [x] Joint angle calculation — `calculate_angle(a, b, c)` (`engine/biomechanics/angles.py`)
- [x] Visibility helpers — `is_visible()`, `all_visible()` (`engine/biomechanics/visibility.py`)
- [x] Temporal smoothing — `OneEuroFilter`, `LandmarkOneEuroFilter` (`engine/biomechanics/smoothing.py`)
- [x] Distance utilities — `euclidean_distance_2d` (`engine/biomechanics/distance.py`)
- [x] Temporal utilities — `displacement_2d`, `velocity_2d` (`engine/biomechanics/temporal.py`)
- [x] Tests — `test_biomechanics_vector.py`, `test_biomechanics_angles.py`, `test_biomechanics_visibility.py`
- [x] Tests — `test_biomechanics_smoothing.py`
- [x] Tests — `test_biomechanics_temporal.py`
- [ ] `PoseFrameSmoother` — frame-level smoothing across selected landmarks _(deferred — implement when organically needed)_

---

## E3 — Squat Movement Analysis 🚧

Interpret biomechanics data as meaningful squat movement.

### A. Phase & Rep ✅
- [x] Phase detection — `STANDING`, `DESCENDING`, `BOTTOM`, `ASCENDING`, `LOCKOUT`, `UNKNOWN` (`engine/squat/phases.py`)
- [x] Rep counting — `SquatRep`, `detect_squat_reps()` (`engine/squat/reps.py`)
- [x] Hip y extraction — `extract_hip_y_values()` (`engine/squat/phases.py`)
- [x] Phase detection logic refactored — position-zone priority over velocity threshold
- [x] Phase smoothing — `smooth_squat_phases()` (`engine/squat/smoothing.py`)
- [x] Movement windowing — `detect_rough_movement_window()`, `detect_squat_analysis_window()`, `detect_refined_analysis_window()` (`engine/squat/windowing.py`)
- [x] Tests — `test_squat_detect_multiple_reps.py`
- [x] Tests — `test_squat_smooth_phases.py`, `test_squat_phase_smoothing_integration.py`
- [x] Integration test — `test_squat_pipeline.py` (video → pose → phases → reps)

### B. Core Metrics
- [x] Relative hip descent (MVP squat-depth proxy)
- [x] Hip-to-knee depth — signed joint-center gap
- [x] Knee flexion angle at bottom — deepest observed hip frame
- [x] Hip flexion angle at bottom — same-frame measurement
- [x] Torso lean
- [x] Knee travel (image-normalized MVP proxy)
- [x] Body-segment-normalized knee travel — rep-median foot-length reference
- [x] Require explicit recording review before foot-length normalization
- [ ] Validated automatic side-view and foot-orientation detector
- [x] Heel lift — toe-relative rise proxy and observed duration
- [x] Metric availability and observed-data coverage
- [ ] Empirically calibrated measurement confidence

### C. Control & Stability
- [x] Descent duration
- [x] Bottom duration
- [x] Ascent duration
- [x] Total rep duration
- [x] Depth consistency
- [x] Tempo consistency
- [x] Torso-angle consistency
- [x] Knee-travel consistency

### D. Future / Multi-view Expansion
- [ ] Hip shift
- [ ] Knee valgus (requires front view)
- [ ] Left–right asymmetry (requires front view)

### Infrastructure
- [x] Visibility policy and valid-frame masks
- [x] Explicit side-selection policy
- [x] Derived squat feature extraction
- [x] Connect depth, torso lean, and knee travel to validated derived features
- [ ] Automatic side selection
- [ ] Missing-feature interpolation policy
- [x] Video FPS metadata
- [x] `ExerciseAnalyzer` base class
- [x] `SquatAnalyzer` implementation
- [x] Metric and analyzer regression tests
- [x] Initial review of sample videos 3-6 and stable cycle-state transitions
- [x] Separate gap-crossing review candidates from measured repetitions
- [ ] Annotated repetition boundaries and independent measurement validation
- [x] Source-bound evaluation registration, blinded reference aids, frozen-input checks and scoring infrastructure
- [x] Opt-in source-image re-detection with explicit recovery provenance
- [x] Experimental posture calibration and model-separated Full/Heavy comparison
- [ ] Independent validation of Heavy/recovery before any default model change

---

## E4 — Feedback Engine ✅ Agreed Implementation Complete

Translate movement analysis into adaptive, explainable feedback.

- [x] Measurement availability notices with per-repetition evidence (foundation only)
- [x] Projected body profile and descriptive personal preparation baseline workflow (review/validation gated)
- [x] Session overview, prioritized actions and explicit partial/unavailable personal comparisons

- [x] Explicit configurable measurement rules (`squat_rules.json`, empty by default; YAML deferred)
- [x] Quality-gated numeric rule evaluation with evidence and withholding reasons
- [x] Explainable measurement availability messages
- [x] Cross-module personal feedback acceptance tests
- [x] Availability/configured-rule infrastructure tests

Deferred validation/future scope (not accepted as complete):

- [ ] Adaptive posture thresholds based on user profile (validation pending; tempo goals deferred)
- [ ] Validated posture interpretation and coaching messages
- [ ] Possible trunk-collapse inference
- [ ] Possible ankle-mobility-limitation inference
- [ ] Excessive-variability inference
- [ ] Compensation-pattern inference
- [ ] Validated coaching-rule tests

---

## E5 — Visualization & UX 🚧 Local API and Preview

Surface analysis results to the user.

- [x] Local review overlays, diagnostic plots and summary dashboard
- [x] Framework-independent JSON result adapter with original-frame provenance and E4 states
- [ ] Product-facing landmark/timeline/metric visualization
- [x] Local FastAPI backend scaffolding and liveness/capabilities
- [x] Bounded local video upload endpoint
- [x] Synchronous analysis endpoint and browser upload/results preview
- [x] Cycle/candidate source-frame navigation and selected-cycle evidence (approximate FPS-based seeking)
- [x] Local paused selected-side joint overlay; filmed/native-browser alignment validation pending
- [ ] React Native + Expo mobile app integration


---

