# Roadmap

---

## Phase 1 — MVP (Current)
**Goal:** Working squat analyzer on mobile

### Engine Development Plan

> Tracks the internal engine build-out required to power the MVP.
> These phases run sequentially before the product layers (API, mobile) are assembled.

| Phase | Name | Status |
|-------|------|--------|
| E1 | Semantic Pose Foundation | ✅ Completed |
| E2 | Biomechanics Foundation | 🚧 In Progress |
| E3 | Squat Movement Analysis | ⏳ Not Started |
| E4 | Feedback Engine | ⏳ Not Started |
| E5 | Visualization & UX | ⏳ Not Started |

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

#### E3 — Squat Movement Analysis
Interpret biomechanics data as meaningful squat movement.
- Squat phase detection — `STANDING`, `DESCENDING`, `BOTTOM`, `ASCENDING`, `LOCKOUT`, `UNKNOWN`
- Squat depth analysis
- Torso lean analysis
- Knee travel analysis
- Heel lift detection
- Hip stability / hip shift
- Neutral spine failure proxy
- Neutral spine / lumbar rounding proxy:
  - Shoulder–hip line angle
  - Torso angle change across frames
  - Hip angle collapse detection
  - Trunk collapse at bottom position
  - Spine posture change tracking (descending → bottom)

#### E4 — Feedback Engine
Translate movement analysis into adaptive, explainable feedback.
- Rule engine (`squat_rules.yaml`)
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
