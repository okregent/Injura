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
- [ ] `PoseFrameSmoother` — frame-level smoothing across selected landmarks
- [x] Tests — `test_biomechanics_vector.py`, `test_biomechanics_angles.py`, `test_biomechanics_visibility.py`
- [x] Tests — `test_biomechanics_smoothing.py`

---

## E3 — Squat Movement Analysis ⏳ NEXT

**Squat Phase Detection**
- [ ] `STANDING`, `DESCENDING`, `BOTTOM`, `ASCENDING`, `LOCKOUT`, `UNKNOWN`

**Core Squat Metrics**
- [ ] Squat depth
- [ ] Torso lean
- [ ] Knee travel
- [ ] Heel lift
- [ ] Hip stability / hip shift
- [ ] Neutral spine failure proxy

**Neutral Spine / Lumbar Rounding Proxy**
- [ ] Shoulder–hip line angle
- [ ] Torso angle change across frames
- [ ] Hip angle collapse detection
- [ ] Trunk collapse detection at bottom position
- [ ] Spine posture change tracking (descending → bottom)

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
