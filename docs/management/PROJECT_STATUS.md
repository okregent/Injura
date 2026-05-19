# Project Status

## Overview
**Project:** Injura — Adaptive AI Squat Analyzer
**Stage:** In Development
**Last Updated:** 2026-05-19

## Completed
- Product name finalised: Injura
- Documentation structure established (`docs/`)
- Architecture decisions documented
- Repository initialised and linked to GitHub
- Base project structure created (`apps/`, `engine/`)
- `.gitignore` configured
- `README.md` created
- `engine/pose/types.py` implemented (`Landmark`, `PoseFrame`, `PoseSequence`)
- `engine/pose/base_estimator.py` implemented (`BasePoseEstimator` abstract class with `extract()` and `close()`)
- `engine/pose/mediapipe_estimator.py` implemented (`MediaPipePoseEstimator` with `extract()`, `visualize()`, `close()`)
- `tests/test_pose_estimator.py` created (`test_extract_pose_sequence`, `test_visualize_pose_estimation`)
- `engine/pose/landmarks.py` implemented: `PoseLandmark` IntEnum with named joint access
- `engine/pose/accessors.py` implemented: `get_landmark()`, `get_landmarks()` helpers
- `engine/pose/chains.py` implemented: `LEFT_LEG_CHAIN`, `RIGHT_LEG_CHAIN`, `LEFT_ARM_CHAIN`, `RIGHT_ARM_CHAIN`, `TORSO_CHAIN`
- `engine/biomechanics/vector.py` implemented: `Vector2D`, `to_vector`, `vector_length`, `dot_product`
- `engine/biomechanics/angles.py` implemented: `calculate_angle(a, b, c)` returning degrees
- `engine/biomechanics/visibility.py` implemented: `is_visible()`, `all_visible()`
- Tests added for all pose and biomechanics modules

## In Progress
- `feature/pose-foundation` — landmark semantic layer (open PR)
- `feature/biomechanics` — kinematics foundation (open PR)

## Blocked
- None

## Next Steps
- Temporal smoothing layer (`engine/biomechanics/smoothing.py`)
- Squat phase detection
- Define `ExerciseAnalyzer` base class
- Implement `SquatAnalyzer`
- Create `squat_rules.yaml`
