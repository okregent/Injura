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
- [ ] Squat depth
- [ ] Torso lean
- [ ] Knee travel
- [ ] Heel lift
- [ ] Neutral spine / lumbar rounding proxy

**C. Control & Stability**
- [ ] Tempo
- [ ] Bottom bounce detection
- [ ] Movement smoothness
- [ ] Hip stability / hip shift

**D. Mobility / Compensation**
- [ ] Ankle mobility limitation proxy

**E. Future / Multi-view** _(not in this sprint)_
- [ ] Knee valgus
- [ ] Left–right asymmetry

**Infrastructure**
- [ ] `ExerciseAnalyzer` base class
- [ ] `SquatAnalyzer` implementation
- [ ] Tests

---

## Not In This Sprint
- FastAPI scaffolding (E5)
- Mobile UI (E5)
- Database integration
- Authentication
