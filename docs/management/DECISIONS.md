# Decisions

## 2026-05-14

### ADR-001: Product Name
**Decision:** Rename from Kineform to Injura
**Reason:** Better reflects the product identity

---

### ADR-002: Project Orientation
**Decision:** Production-oriented system, not a portfolio demo
**Reason:** Long-term goal is an adaptive human movement intelligence platform
**Implications:** Scalability, maintainability, and modularity are core priorities from the start

---

### ADR-003: Documentation Structure
**Decision:** All high-level documents live in `docs/`; `CLAUDE.md` contains only behaviour rules and current session context
**Reason:** Keeps CLAUDE.md lightweight; `docs/` is the single source of truth
**Structure:**
```
docs/
├── product/
├── architecture/
├── management/
└── sessions/
```

---

### ADR-004: No Planning Agent
**Decision:** Dropped planning agent concept; replaced by `docs/` structure
**Reason:** `docs/` serves as a persistent, reviewable source of truth without requiring a separate agent

---

### ADR-005: Session Log Strategy
**Decision:** `docs/sessions/` for Claude context restoration; Git for code history — both maintained
**Reason:** The two serve different purposes and are not redundant

---

### ADR-006: Tech Stack
**Decision:** React Native + Expo (mobile), FastAPI + Python (backend), MediaPipe Pose + OpenCV (CV), PostgreSQL/Supabase (database)
**Reason:** Practical AI engineering focus; avoids custom model training; optimises for deployment flexibility and maintainability

---

### ADR-007: CV Pipeline Abstraction
**Decision:** Pose estimation abstracted behind a `PoseEstimator` interface (MediaPipe, MoveNet, future models)
**Reason:** Avoids hard dependency on a single framework; improves long-term flexibility

---

### ADR-008: AI Layer vs Rule Layer Separation
**Decision:** Separate AI layer (landmark extraction, pose estimation, temporal tracking) from Rule layer (biomechanics interpretation, personalised thresholds, feedback logic)
**Reason:** Improves maintainability, explainability, and scalability

---

### ADR-009: Configurable Rule System
**Decision:** Feedback rules stored in YAML files, not hardcoded
**Reason:** Enables configurable, explainable, and adaptive thresholds per user profile

---

## 2026-05-19

### ADR-010: PoseFrame Retained as Type Alias
**Decision:** `PoseFrame` remains a `List[Landmark]` type alias; do not convert to a class
**Reason:** Simpler architecture, lower complexity, avoids premature abstraction at this stage

---

### ADR-011: Accessor Strategy — Helper Functions over Methods
**Decision:** Landmark access via standalone helper functions (`get_landmark()`, `get_landmarks()`) rather than methods on `PoseLandmark`
**Reason:** Separation of responsibilities — semantic definitions (`landmarks.py`) are decoupled from data access logic (`accessors.py`); easier to refactor if `PoseFrame` structure changes

---

### ADR-012: Semantic Separation Principle
**Decision:** Split pose layer into three distinct modules: `landmarks.py` (semantic definitions), `accessors.py` (access logic), `chains.py` (body groupings)
**Reason:** Each module has a single responsibility; semantic definition is not the same as data access logic; improves maintainability and testability

---

## 2026-07-28

### ADR-013: Separate Direct Measurements from Feedback Inferences

**Decision:** E3 squat metrics produce observable, explainable measurements.
Claims that require interpretation across multiple measurements belong to the
E4 feedback layer.

**MVP direct measurements:**
- Relative hip descent and hip-to-knee depth
- Knee and hip flexion angles at bottom
- Torso lean
- Body-segment-normalized knee travel
- Heel lift magnitude and duration
- Descent, bottom, ascent, and total duration
- Rep-to-rep consistency
- Analysis confidence and data quality

**E4 feedback inferences:**
- Possible trunk collapse
- Possible ankle mobility limitation
- Excessive movement variability
- Compensation patterns

**Reason:** MediaPipe side-view landmarks can support the listed measurements,
but they cannot directly establish lumbar curvature, mobility restriction, or
injury-related conclusions. Keeping measurement separate from interpretation
preserves explainability and prevents proxy values from being presented as
diagnoses.

**Implications:**
- Current relative hip descent remains an MVP consistency measurement; it is
  not an absolute squat-depth classification.
- "Neutral spine / lumbar rounding" is renamed to a conservative trunk-collapse
  proxy and handled as feedback inference.
- Ankle mobility limitation is inferred from multiple measurements rather than
  implemented as a standalone metric.
- Hip shift, knee valgus, and left-right asymmetry are excluded from the
  side-view MVP and deferred to multi-view analysis.
- Generic movement smoothness is decomposed into measurable timing and
  variability features.

---

### ADR-014: Side-View MVP Metric Portfolio

**Decision:** The side-view MVP prioritizes depth, joint angles, torso lean,
normalized knee travel, heel lift, phase timing, repetition consistency, and
analysis confidence.

**Reason:** This set provides sufficient coverage of range of motion,
compensation, control, and measurement reliability while remaining observable
from a single side-view recording.

**Implications:**
- Bottom bounce is deferred until velocity, acceleration, FPS, and smoothing
  contracts are validated.
- Every metric must expose its units, required landmarks, representative frame,
  validity, and limitations in the metric catalog.
- Original video frame mapping and video timing metadata are required for
  overlays and tempo measurements.

## 2026-11-04

### Documentation Branch Policy

Continue the 2026-05-21 policy: maintain project documentation on `main`, and keep
unmerged implementation on its feature branch. Documentation that describes
unmerged features must name the implementation branch. Synchronize document
updates back into the feature branch without merging engine code into `main`.

### ADR-015: Preserve Measurement Availability and Original Time

**Decision:** Integrate E3 metrics through `SquatAnalyzer` with independent
outcomes, exclusion reasons, and observed-data coverage. Split repetition
detection at missing hip observations or nonconsecutive source frames. Do not
interpolate. Phase timing requires contiguous source observations and ordered
descent/bottom/ascent runs; measure half-open intervals ending at the return to
standing. FPS-based timing assumes constant frame rate.

**Reason:** Missing observations must not compress time, create repetitions, or
silently change metric baselines. One unavailable metric must not erase other
usable measurements. Coverage is data support, not calibrated confidence.

### ADR-016: Keep Projected Foot and Heel Measurements Explicit

**Decision:** Normalize knee travel by the within-rep median usable projected
foot length only after explicit external confirmation of side view and side-on
foot orientation. Unknown conditions withhold normalization. Use toe-relative
heel height change from a valid rep-start baseline as a separately documented
heel-rise proxy, with configurable image-coordinate tolerance and observed
duration coverage.

**Reason:** Visibility cannot establish camera or foot orientation. A projected
heel change cannot prove loss of ground contact. Automatic recording validation
and empirically calibrated measurement confidence remain pending.

### ADR-017: Stable Cycle Phases and Unverified Gap Candidates

**Decision:** Preserve the uninterrupted-observation requirement for measured
repetitions. Use a standing-armed position state machine, bottom entry/exit
hysteresis (85%/75% of calibrated descent), and cancel aborted descents on return
to standing. Preserve genuine bottom re-entry rather than forcing ordered timing.

With known FPS, separately track unverified candidates across individual gaps
of at most 0.2 seconds by default (zero disables this). Both standing and bottom
must be observed. Candidates expose original boundaries, deepest observed
frame, and missing-observation count, but have no measured metrics or phase
durations and never enter consistency statistics. No coordinates or missing
phases are interpolated.

**Reason:** Real recordings exposed direction chatter and an aborted-descent
state bug, while occlusion at squat bottoms made some complete repetitions
unobservable. The report must expose these hypotheses without presenting them
as measurements. Global calibration can still misplace boundaries during
preparation; human annotation and detector calibration remain necessary.

### ADR-018: Opt-in Image Recovery and Explicit Model Comparisons

**Decision:** Retry bounded missing source images using full-image and neighboring
crop inference, without coordinate interpolation or lowering detection confidence.
Preserve original detections, require agreement with both observed hip anchors,
record recovered source indices, and mark affected metric outcomes for review.
Keep image recovery and median-standing/P95-bottom calibration opt-in. Recorded
user counts are evaluation references only, never detector parameters.

Allow explicit integer model selection 0/1/2, retaining Full (1) by default.
Separate model caches and record primary/recovery model choices; the review CLI
uses the same model for extraction and recovery. Heavy's improvement on video 6
does not justify a global default change or claims of valid occluded joint angles.

**Reason:** Stable count detection, landmark continuity, anatomical accuracy, and
measurement availability are distinct validation targets. Source-image inference
can recover data but must not erase uncertainty or make sample-specific results
look like independently validated accuracy.

### ADR-019: Supported Capture Scope and Validation Before Posture Feedback

**Decision:** Limit the MVP to reviewed fixed-camera, continuous, full-body
side-view recordings with usable joints. Define item-level withholding and E3
acceptance separately from implementation/test completion. Human capture review
is acceptable initially; automatic camera/side detection and interpolation are
not prerequisites. Unknown review is not approval. Preserve supported items
when another measurement is unavailable.

Defer user-defined tempo goals; retain timing measurement. Prioritize recording
review, predeclared error/coverage limits and reference-based evaluation before
validated posture feedback. Existing exploratory clips/count matches are not
joint-angle ground truth or injury-prevention evidence. E4 rule foundations and
E5 local reports are started; validated coaching and API/mobile remain pending.

**Reason:** The user reaffirmed reliable posture guidance supporting injury
prevention as the purpose, rather than tempo targets or unrestricted camera
support. Narrowing capture scope makes validation concrete without transferring
full-frame labeling to the user. See the recording guide and E3 acceptance gates.

### ADR-020: Frozen Evaluation Inputs and Blinded Reference Preparation

**Decision:** Implement E3 evaluation separately from production measurement and
coaching rules. Register source hashes, participant/source groups and reviewed
provenance; initialize unknown capture reviews and unconfirmed references.
Freeze dataset/reference/limits bytes, analysis/policy/evaluator source, runtime
and primary landmark/detector weights/graph before acceptance evaluation.
Changes invalidate the frozen run. Preserve previous reviews and append backups.

Use raw source frames without predicted labels for reference preparation.
Require explicit independent confirmation/uncertainty and preselected positions.
Keep missing values in coverage and candidates out of measurement/count matches.
Development smoke always remains not evaluated and its local source history
cannot be promoted to held-out acceptance. Hashes supplement, not replace,
truthful provenance and annotation review. Keep outputs local under artifacts.

**Reason:** The user requested advancing all feasible work before supplying new
video. Preparing a reproducible workflow is useful now; fabricating ground truth,
acceptance or medical efficacy would undermine the purpose of measurement validation.
