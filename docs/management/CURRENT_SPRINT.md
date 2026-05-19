# Current Sprint

## Sprint Goal
Engine foundation — build the semantic and biomechanical layers required for squat analysis.

## Phase 1 — Landmark Semantic Layer

- [x] Task 1: `PoseLandmark` enum (`engine/pose/landmarks.py`) — named joint access (e.g. `PoseLandmark.LEFT_HIP`)
- [x] Task 2: MediaPipe index mapping encapsulation — `get_landmark()`, `get_landmarks()` helpers in `engine/pose/accessors.py`
- [x] Task 3: Kinematic chain definitions — `LEFT_LEG_CHAIN`, `RIGHT_LEG_CHAIN`, `LEFT_ARM_CHAIN`, `RIGHT_ARM_CHAIN`, `TORSO_CHAIN` in `engine/pose/chains.py`

## Phase 2 — Kinematics Foundation

- [x] Task 4: Vector utility module (`engine/biomechanics/vector.py`) — `Vector2D`, `to_vector`, `vector_length`, `dot_product`
- [x] Task 5: Joint angle calculation (`engine/biomechanics/angles.py`) — `calculate_angle(a, b, c)` returns degrees
- [x] Task 6 (partial): Visibility helpers (`engine/biomechanics/visibility.py`) — `is_visible()`, `all_visible()`
- [ ] Task 7: Temporal smoothing layer — moving average (MVP), smooth raw landmarks before analysis

## Phase 3 — Squat Semantics

- [ ] Task 8: Squat phase detection — `standing`, `descending`, `bottom`, `ascending`, `lockout`
- [ ] Task 9: Core squat metrics
  - **High priority:** squat depth, torso lean, heel lift, knee travel
  - **Later:** hip shift, asymmetry, tempo consistency, stability

## Completed
- [x] `engine/pose/types.py` — `Landmark`, `PoseFrame`, `PoseSequence`
- [x] `engine/pose/base_estimator.py` — `BasePoseEstimator` abstract class
- [x] `engine/pose/mediapipe_estimator.py` — `MediaPipePoseEstimator`
- [x] `tests/test_pose_estimator.py` — smoke tests
- [x] `engine/pose/landmarks.py` — `PoseLandmark` IntEnum
- [x] `engine/pose/accessors.py` — `get_landmark()`, `get_landmarks()`
- [x] `engine/pose/chains.py` — leg, arm, torso kinematic chains
- [x] `engine/biomechanics/vector.py` — `Vector2D`, `to_vector`, `vector_length`, `dot_product`
- [x] `engine/biomechanics/angles.py` — `calculate_angle(a, b, c)`
- [x] `engine/biomechanics/visibility.py` — `is_visible()`, `all_visible()`
- [x] `tests/test_landmark_accessor.py`, `test_pose_package_exports.py`
- [x] `tests/test_biomechanics_angles.py`, `test_biomechanics_vector.py`, `test_biomechanics_visibility.py`

## Not In This Sprint
- FastAPI scaffolding
- Mobile UI
- Database integration
- Authentication
