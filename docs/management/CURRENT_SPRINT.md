# Current Sprint

## Sprint Goal
Complete E3 (Squat Movement Analysis).

---

## E1 — Semantic Pose Foundation ✅ COMPLETED

- [x] `PoseLandmark` IntEnum (`engine/pose/landmarks.py`)
- [x] Accessor helpers — `get_landmark()`, `get_landmarks()` (`engine/pose/accessors.py`)
- [x] Kinematic chain definitions (`engine/pose/chains.py`)
- [x] Tests — `test_landmark_accessor.py`, `test_pose_package_exports.py`

---

## E2 — Biomechanics Foundation ✅ COMPLETED

- [x] Vector utilities (`engine/biomechanics/vector.py`)
- [x] Joint angle calculation (`engine/biomechanics/angles.py`)
- [x] Visibility helpers (`engine/biomechanics/visibility.py`)
- [x] Temporal smoothing — `OneEuroFilter`, `LandmarkOneEuroFilter` (`engine/biomechanics/smoothing.py`)
- [x] Distance utilities (`engine/biomechanics/distance.py`)
- [x] Temporal utilities — `displacement_2d`, `velocity_2d` (`engine/biomechanics/temporal.py`)
- [x] Tests — `test_biomechanics_vector.py`, `test_biomechanics_angles.py`, `test_biomechanics_visibility.py`
- [x] Tests — `test_biomechanics_smoothing.py`
- [x] Tests — `test_biomechanics_temporal.py`
- [ ] `PoseFrameSmoother` — frame-level smoothing across selected landmarks _(deferred)_

---

## E3 — Squat Movement Analysis 🚧 IN PROGRESS

**A. Phase & Rep ✅**
- [x] Phase detection — `STANDING`, `DESCENDING`, `BOTTOM`, `ASCENDING`, `LOCKOUT`, `UNKNOWN`
- [x] Rep counting
- [x] Hip y extraction — `extract_hip_y_values()`
- [x] Phase detection logic refactored — position-zone priority
- [x] Phase smoothing (hysteresis) — `smooth_squat_phases()`
- [x] Movement windowing — `detect_rough_movement_window()`, `detect_squat_analysis_window()`, `detect_refined_analysis_window()`
- [x] Tests — `test_squat_detect_multiple_reps.py`
- [x] Tests — `test_squat_smooth_phases.py`, `test_squat_phase_smoothing_integration.py`
- [x] Integration test — `test_squat_pipeline.py`

**B. Core Metrics**
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

**C. Control & Stability**
- [x] Descent, bottom, ascent, and total rep duration
- [x] Depth, tempo, torso-angle, and knee-travel consistency

**D. Future / Multi-view** _(not in this sprint)_
- [ ] Hip shift
- [ ] Knee valgus
- [ ] Left–right asymmetry

**Infrastructure**
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
- [x] Opt-in source-image re-detection with explicit recovery provenance
- [x] Experimental posture calibration and model-separated Full/Heavy comparison
- [ ] Independent validation of Heavy/recovery before any default model change

---

## Not In This Sprint
- FastAPI scaffolding (E5)
- Mobile UI (E5)
- Database integration
- Authentication
