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
