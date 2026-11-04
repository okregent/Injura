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
| E4    | Feedback Engine           | ⏳ Not Started  |
| E5    | Visualization & UX        | ⏳ Not Started  |

---

## Current Focus

**Phase: E3 — Squat Movement Analysis**
**Current task:** E3 measurement and analyzer implementation complete; empirical recording validation and confidence calibration pending

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
- [x] Rep counting — `SquatRep`, `detect_squat_reps()` (`engine/squat/phases.py`)
- [x] Hip y extraction — `extract_hip_y_values()` (`engine/squat/phases.py`)
- [x] Phase detection logic refactored — position-zone priority over velocity threshold
- [x] Phase smoothing (hysteresis) — `smooth_squat_phases()` (`engine/squat/phases.py`)
- [x] Movement windowing — `detect_rough_movement_window()`, `detect_squat_analysis_window()`, `detect_refined_analysis_window()` (`engine/squat/phases.py`)
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

---

## E4 — Feedback Engine ⏳

Translate movement analysis into adaptive, explainable feedback.

- [ ] `squat_rules.yaml` — configurable rule definitions
- [ ] Rule engine implementation
- [ ] Adaptive thresholds based on user profile
- [ ] Explainable feedback messages
- [ ] Possible trunk-collapse inference
- [ ] Possible ankle-mobility-limitation inference
- [ ] Excessive-variability inference
- [ ] Compensation-pattern inference
- [ ] Tests

---

## E5 — Visualization & UX ⏳

Surface analysis results to the user.

- [ ] Landmark overlay visualization
- [ ] Timeline and metric visualization
- [ ] FastAPI backend scaffolding
- [ ] Video upload endpoint
- [ ] Analysis endpoint
- [ ] React Native + Expo mobile app integration


---

