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
