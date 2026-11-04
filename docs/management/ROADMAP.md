# Roadmap

---

## Phase 1 — MVP (Current)
**Goal:** Working squat analyzer on mobile

### Engine Development Plan

> Tracks the internal engine build-out required to power the MVP.
> E3 validation remains the priority. E4/E5 foundations may overlap, but they
> do not imply validated posture feedback or a released product.

| Phase | Name | Status |
|-------|------|--------|
| E1 | Semantic Pose Foundation | ✅ Completed |
| E2 | Biomechanics Foundation | ✅ Completed |
| E3 | Squat Movement Analysis | 🚧 Implemented; empirical validation pending |
| E4 | Feedback Engine | 🚧 Availability/configured-rule foundations; coaching pending |
| E5 | Visualization & UX | 🚧 Local developer reports; API/mobile not started |

Current gates: [E3 acceptance](../validation/E3_ACCEPTANCE.md).
Supported input: [recording guide](../product/RECORDING_GUIDE.md). User-defined
tempo targets are deferred; timing measurement remains in E3.

#### E1 — Semantic Pose Foundation
Convert raw MediaPipe indices into semantic abstractions.
- `PoseLandmark` enum — named joint access
- Accessor helpers — `get_landmark()`, `get_landmarks()`
- Kinematic chain definitions — leg, arm, torso chains
- Package exports and tests

#### E2 — Biomechanics Foundation
Convert semantic landmarks into biomechanics-aware mathematical representations.
- Vector utilities — `to_vector`, `vector_length`, `dot_product`
- Joint angle calculation — `calculate_angle(a, b, c)`
- Visibility validation — `is_visible()`, `all_visible()`
- Temporal smoothing — `OneEuroFilter`, `LandmarkOneEuroFilter`
- Distance utilities — `euclidean_distance_2d`
- Temporal utilities — `displacement_2d`, `velocity_2d`

#### E3 — Squat Movement Analysis
Interpret biomechanics data as meaningful squat movement.
- **A. Phase & Rep:** phase detection (STANDING / DESCENDING / BOTTOM / ASCENDING / LOCKOUT / UNKNOWN), rep counting
- **B. Core Metrics:** relative and hip-to-knee depth, knee and hip angles, torso lean, normalized knee travel, heel lift, metric confidence
- **C. Control & Consistency:** phase timing and rep-to-rep consistency
- **D. Interpretation boundary:** validated posture/coaching inferences belong to E4 after measurement validation
- **E. Future / Multi-view:** hip shift, knee valgus, left–right asymmetry

#### E4 — Feedback Engine
Translate movement analysis into adaptive, explainable feedback.
- Explicit JSON rule engine (`squat_rules.json`, empty defaults; YAML deferred)
- Adaptive thresholds based on user profile
- Explainable feedback messages

#### E5 — Visualization & UX
Surface analysis results to the user.
- Landmark overlay visualization
- Timeline and metric visualization
- FastAPI backend scaffolding
- React Native + Expo mobile app integration

### Product Scope
- Squat analysis only
- Side-view video upload (offline, no real-time)
- MediaPipe Pose for landmark extraction
- Adaptive feedback based on user profile (body proportions, mobility, discomfort)
- Mobile application (React Native + Expo)
- Backend API (FastAPI)

### Key Features
- User profile setup
- Side-view squat video upload
- Pose estimation (MediaPipe Pose)
- Squat depth analysis
- Torso lean analysis
- Knee travel analysis
- Tempo and stability tracking
- Biomechanics-aware adaptive feedback

---

## Phase 2 — Expansion
- Real-time video analysis
- Additional exercise modules (Deadlift, Pushup)
- Additional pose model support (MoveNet, future models)
- Multi-exercise support
- 3D landmark integration
- ML-assisted biomechanics reasoning
- Web application

---

## Phase 3 — Platform
- Strength training analysis
- Combat sports analysis
- Mobility assessment
- Ergonomics analysis
- Rehabilitation assistance
- Personalised movement intelligence systems
