# Project Status

## Overview
**Project:** Injura — Adaptive AI Squat Analyzer
**Stage:** In Development
**Last Updated:** 2026-11-04

**Branch scope:** Documents are maintained on `main`; implementation and test
status below refer to `feature/biomechanics`. Its engine code has not been merged
into `main`.

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
- `engine/biomechanics/smoothing.py` implemented: `OneEuroFilter`, `LandmarkOneEuroFilter`
- Tests added for all pose and biomechanics modules including `test_biomechanics_smoothing.py`
- `engine/biomechanics/distance.py` implemented: `euclidean_distance_2d`
- `engine/biomechanics/temporal.py` implemented: `displacement_2d`, `velocity_2d`
- `engine/squat/phases.py` implemented: `SquatPhase`, `SquatPhaseThresholds`, `detect_squat_phase`, `detect_squat_phases`, `SquatRep`, `detect_squat_reps`
- `tests/test_squat_detect_multiple_reps.py` created and passing
- `extract_hip_y_values()` added to `engine/squat/phases.py`
- `tests/test_squat_pipeline.py` integration test passing (video → pose → phases → reps)
- `detect_squat_phase()` logic refactored: position-zone priority over velocity threshold
- `smooth_squat_phases()` implemented: phase hysteresis to remove short noise segments
- `detect_rough_movement_window()` implemented: first DESCENDING to last ASCENDING
- `detect_squat_analysis_window()` implemented: rep-based analysis window
- `detect_refined_analysis_window()` implemented: two-pass windowing for precise rep crop
- `tests/test_squat_smooth_phases.py` created and passing
- `tests/test_squat_phase_smoothing_integration.py` created and passing

## In Progress
- E3 — Squat Movement Analysis (`engine/squat/`)
  - A. Phase & Rep ✅
  - B. Core metric implementation ✅ (2D proxies; empirical validation pending)
  - C. Phase timing and rep consistency ✅
  - `ExerciseAnalyzer` and `SquatAnalyzer` integration ✅
  - Data availability, coverage, and per-metric exclusion reasons ✅
  - Infrastructure: visibility, explicit side selection, and derived-feature
    preprocessing contract ✅

## Blocked
- None

## Next Steps
- Validate measurements against annotated recordings with varied camera geometry
- Validate an automatic side-view/foot-orientation detector; manual review is required today
- Calibrate measurement confidence empirically; current coverage is not accuracy probability
- Decide whether validated interpolation or automatic side selection is needed
- Implement E4 feedback rules after measurement validation

## Latest Validation
- Full local suite: 245 passed, including real-video extraction, phase/rep detection,
  and integrated `SquatAnalyzer` analysis (2026-11-04).
- External-library deprecation warnings remain; no test failures.
- Initial sample review completed for videos 3-6. Videos 3 and 4 retain 6 and 14
  detections with all phase timings available on both sides. Video 5 has no
  uninterrupted complete detections (2 left / 1 right review candidates); video
  6 has 3 candidates per side and no measured repetitions. Counts are not
  annotated ground truth. See `docs/validation/sample-review-2026-11-04.md`.
- The initial results above describe the conservative baseline. Subsequent
  opt-in source-image recovery and posture calibration detect video 5's two
  user-reported reps with timing. For video 6, Heavy plus same-model recovery
  detects all three user-reported reps with timing; bottom knee/hip angles remain
  unavailable. Full stays the default. See the follow-up validation document.
