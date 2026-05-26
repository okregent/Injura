# Engine Progress

Tracks the build-out of the Injura analysis engine across MVP phases E1–E5.
Update this file whenever a task is started, completed, or a phase status changes.

---

## Overview

| Phase | Name                      | Status         |
|-------|---------------------------|----------------|
| E1    | Semantic Pose Foundation  | ✅ Completed    |
| E2    | Biomechanics Foundation   | 🚧 In Progress  |
| E3    | Squat Movement Analysis   | ⏳ Not Started  |
| E4    | Feedback Engine           | ⏳ Not Started  |
| E5    | Visualization & UX        | ⏳ Not Started  |

---

## Current Focus

**Phase: E2 — Biomechanics Foundation**
**Current task:** Temporal utilities — frame-to-frame delta, velocity, movement direction

---

## E1 — Semantic Pose Foundation ✅

Convert raw MediaPipe indices into semantic abstractions.

- [x] `PoseLandmark` IntEnum — named joint access (`engine/pose/landmarks.py`)
- [x] Accessor helpers — `get_landmark()`, `get_landmarks()` (`engine/pose/accessors.py`)
- [x] Kinematic chain definitions — leg, arm, torso chains (`engine/pose/chains.py`)
- [x] Package exports updated (`engine/pose/__init__.py`)
- [x] Tests — `test_landmark_accessor.py`, `test_pose_package_exports.py`

---

## E2 — Biomechanics Foundation 🚧

Convert semantic landmarks into biomechanics-aware mathematical representations.

- [x] Vector utilities — `to_vector`, `vector_length`, `dot_product` (`engine/biomechanics/vector.py`)
- [x] Joint angle calculation — `calculate_angle(a, b, c)` (`engine/biomechanics/angles.py`)
- [x] Visibility helpers — `is_visible()`, `all_visible()` (`engine/biomechanics/visibility.py`)
- [x] Temporal smoothing — `OneEuroFilter`, `LandmarkOneEuroFilter` (`engine/biomechanics/smoothing.py`)
- [ ] `PoseFrameSmoother` — frame-level smoothing across selected landmarks (deferred)
- [ ] Temporal utilities — frame-to-frame delta, velocity, movement direction (`engine/biomechanics/temporal.py`)
- [x] Tests — `test_biomechanics_vector.py`, `test_biomechanics_angles.py`, `test_biomechanics_visibility.py`
- [x] Tests — `test_biomechanics_smoothing.py`

---

## E3 — Squat Movement Analysis ⏳

Interpret biomechanics data as meaningful squat movement.

### Squat Phase Detection
- [ ] `STANDING`
- [ ] `DESCENDING`
- [ ] `BOTTOM`
- [ ] `ASCENDING`
- [ ] `LOCKOUT`
- [ ] `UNKNOWN`

### Core Squat Metrics
- [ ] Squat depth
- [ ] Torso lean
- [ ] Knee travel
- [ ] Heel lift
- [ ] Hip stability / hip shift
- [ ] Neutral spine failure proxy

### Neutral Spine / Lumbar Rounding Proxy
- [ ] Shoulder–hip line angle
- [ ] Torso angle change across frames
- [ ] Hip angle collapse detection
- [ ] Trunk collapse detection at bottom position
- [ ] Spine posture change tracking across descending → bottom phase

### Infrastructure
- [ ] `ExerciseAnalyzer` base class
- [ ] `SquatAnalyzer` implementation
- [ ] Tests

---

## E4 — Feedback Engine ⏳

Translate movement analysis into adaptive, explainable feedback.

- [ ] `squat_rules.yaml` — configurable rule definitions
- [ ] Rule engine implementation
- [ ] Adaptive thresholds based on user profile
- [ ] Explainable feedback messages
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
