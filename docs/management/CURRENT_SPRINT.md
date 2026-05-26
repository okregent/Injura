# Current Sprint

## Sprint Goal
Complete E2 (Biomechanics Foundation) and begin E3 (Squat Movement Analysis).

---

## E1 — Semantic Pose Foundation ✅ COMPLETED

- [x] `PoseLandmark` IntEnum (`engine/pose/landmarks.py`)
- [x] Accessor helpers — `get_landmark()`, `get_landmarks()` (`engine/pose/accessors.py`)
- [x] Kinematic chain definitions (`engine/pose/chains.py`)
- [x] Tests — `test_landmark_accessor.py`, `test_pose_package_exports.py`

---

## E2 — Biomechanics Foundation 🚧 IN PROGRESS

- [x] Vector utilities (`engine/biomechanics/vector.py`)
- [x] Joint angle calculation (`engine/biomechanics/angles.py`)
- [x] Visibility helpers (`engine/biomechanics/visibility.py`)
- [x] Temporal smoothing — `OneEuroFilter`, `LandmarkOneEuroFilter` (`engine/biomechanics/smoothing.py`)
- [x] Distance utilities (`engine/biomechanics/distance.py`)
- [x] Temporal utilities — `displacement_2d`, `velocity_2d` (`engine/biomechanics/temporal.py`)
- [ ] `PoseFrameSmoother` — frame-level smoothing across selected landmarks (deferred)
- [x] Tests — `test_biomechanics_vector.py`, `test_biomechanics_angles.py`, `test_biomechanics_visibility.py`
- [x] Tests — `test_biomechanics_smoothing.py`
- [x] Tests — `test_biomechanics_temporal.py`

---

## E3 — Squat Movement Analysis ⏳ NEXT

**A. Phase & Rep**
- [ ] Phase detection — `STANDING`, `DESCENDING`, `BOTTOM`, `ASCENDING`, `LOCKOUT`, `UNKNOWN`
- [ ] Rep counting

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
