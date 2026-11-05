# Current Sprint

## Sprint Goal
Close the agreed E4 observation/personal-comparison implementation scope.
**Completed**; see [acceptance](../validation/E4_IMPLEMENTATION_ACCEPTANCE.md).
New filming and E3 empirical evaluation remain deferred by the user; empirical
acceptance and validated coaching remain open.

## Current Priorities

- [x] Define [MVP capture conditions](../product/RECORDING_GUIDE.md).
- [x] Define [item gates and E3 acceptance](../validation/E3_ACCEPTANCE.md).
- [x] Connect reviewed recording conditions to configured-rule interpretation gates.
- [x] Predeclare initial engineering error/coverage limits and prepare a versioned source inventory ([protocol v0.1](../validation/E3_PROTOCOL_v0.1.md)).
- [x] Implement registration, independent-reference aids, frozen-input verification and scoring ([workflow](../architecture/e3-evaluation-workflow.md)).
- [x] Prepare empty reference scaffolds, failed-item triage and an unapproved E4 evidence-review packet ([workflow](../architecture/e3-evaluation-workflow.md#prepare-later-review-stages)); implementation stays on `feature/biomechanics`.
- [ ] Register eligible evaluation clips and reviewed references; freeze the evaluated dataset before runs.
- [ ] Evaluate against reviewed references; resolve or restrict failed items.

- [x] Add per-repetition measurement feedback cards with capture review, retake,
  measurement review and observation states on `feature/biomechanics`.
- [x] Define and store source-bound [projected body profiles](../architecture/body-profile.md), with capture checks and uncertainty; manual inputs only.
- [x] Add descriptive preparation baselines, matching-context comparisons and grouped session actions; retain validation gates.
- [x] Add source-bound personal setup drafts, readiness screen and fresh-inference baseline generation.
- [x] Add original-frame point measurement/download/import with preserved profile history and review reset.
- [x] Add conservative [E4 session overview](../architecture/e4-session-overview.md) and explicit personal-comparison completeness states.
- [ ] Obtain reviewed user-specific profile/preparation evidence before real personalized comparisons; filming remains deferred.

Latest regression: 411 passed (2026-11-05). The local development smoke result
remains not evaluated. New sources/reviewed references are still required.
Profile and baseline tests are now included in the full regression suite.

Prepare evidence autonomously; the user need not annotate every frame. Existing
exploratory clips are not independent validation. User-defined tempo goals are
deferred. E4 agreed implementation is complete; validated coaching and E5 API/mobile remain pending.

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
