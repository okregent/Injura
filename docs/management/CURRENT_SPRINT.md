# Current Sprint

## Sprint Goal
Engine foundation — build the semantic and biomechanical layers required for squat analysis.

## Phase 1 — Landmark Semantic Layer

- [ ] Task 1: `PoseLandmark` enum (`engine/pose/landmarks.py`) — named joint access (e.g. `PoseLandmark.LEFT_HIP`)
- [ ] Task 2: MediaPipe index mapping encapsulation — `get_landmark(frame, PoseLandmark.LEFT_HIP)` helper, removes raw index usage
- [ ] Task 3: `PoseFrame` accessor — approach TBD (current `PoseFrame` is a type alias, not a class)

## Phase 2 — Kinematics Foundation

- [ ] Task 4: Vector utility module (`engine/biomechanics/vector.py`) — `distance`, `normalize`, `dot`, `angle`
- [ ] Task 5: Joint angle calculation — `calculate_joint_angle(a, b, c)` for hip, knee, ankle angles
- [ ] Task 6: Temporal smoothing layer — moving average (MVP), smooth raw landmarks before analysis

## Phase 3 — Squat Semantics

- [ ] Task 7: Squat phase detection — `standing`, `descending`, `bottom`, `ascending`, `lockout`
- [ ] Task 8: Core squat metrics
  - **High priority:** squat depth, torso lean, heel lift, knee travel
  - **Later:** hip shift, asymmetry, tempo consistency, stability

## Completed
- [x] `engine/pose/types.py` — `Landmark`, `PoseFrame`, `PoseSequence`
- [x] `engine/pose/base_estimator.py` — `BasePoseEstimator` abstract class
- [x] `engine/pose/mediapipe_estimator.py` — `MediaPipePoseEstimator`
- [x] `tests/test_pose_estimator.py` — smoke tests

## Not In This Sprint
- FastAPI scaffolding
- Mobile UI
- Database integration
- Authentication
