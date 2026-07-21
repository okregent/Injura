Injura — Project Structure
==========================

## Root

Injura/
├── CLAUDE.md                          ← Claude Code instructions and session context
├── README.md
├── requirements.txt
├── ai_service_dev_pipeline.svg
├── injura_dev_pipeline.svg
│
├── engine/                            ← Core analysis engine (Python)
├── tests/                             ← Unit and integration tests
├── scripts/                           ← Exploration / dev scripts
├── apps/                              ← Mobile/web app (placeholder)
└── docs/                              ← All project documentation

---

## engine/

engine/
├── __init__.py
│
├── pose/                              ← E1: Semantic Pose Foundation
│   ├── __init__.py
│   ├── types.py                       ← PoseLandmark data types, PoseFrame, PoseSequence
│   ├── landmarks.py                   ← PoseLandmark IntEnum (named joint access)
│   ├── accessors.py                   ← get_landmark(), get_landmarks()
│   ├── chains.py                      ← Kinematic chain definitions (leg, arm, torso)
│   ├── base_estimator.py              ← Abstract base class for pose estimators
│   └── mediapipe_estimator.py         ← MediaPipe implementation of pose estimator
│
├── biomechanics/                      ← E2: Biomechanics Foundation
│   ├── __init__.py
│   ├── vector.py                      ← to_vector(), vector_length(), dot_product()
│   ├── angles.py                      ← calculate_angle(a, b, c)
│   ├── visibility.py                  ← is_visible(), all_visible()
│   ├── distance.py                    ← euclidean_distance_2d()
│   ├── smoothing.py                   ← OneEuroFilter, LandmarkOneEuroFilter
│   └── temporal.py                    ← displacement_2d(), velocity_2d()
│
└── squat/                             ← E3: Squat Movement Analysis
    ├── __init__.py
    ├── phases.py                      ← SquatPhase enum, detect_squat_phases(), extract_hip_y_values()
    ├── smoothing.py                   ← smooth_squat_phases() (hysteresis)
    ├── reps.py                        ← SquatRep, detect_squat_reps()
    └── windowing.py                   ← detect_rough_movement_window(), detect_squat_analysis_window(),
                                         detect_refined_analysis_window()

---

## tests/

tests/
├── __init__.py
│
│   # E1 — Pose
├── test_landmark_accessor.py
├── test_pose_package_exports.py
├── test_pose_estimator.py
│
│   # E2 — Biomechanics
├── test_biomechanics_vector.py
├── test_biomechanics_angles.py
├── test_biomechanics_visibility.py
├── test_biomechanics_smoothing.py
├── test_biomechanics_temporal.py
│
│   # E3 — Squat
├── test_squat_detect_multiple_reps.py
├── test_squat_smooth_phases.py
├── test_squat_phase_smoothing_integration.py
└── test_squat_pipeline.py             ← Integration test: video → pose → phases → reps

---

## scripts/

scripts/
└── explore_squat_pipeline.py          ← Dev script for manual pipeline exploration

---

## docs/

docs/
├── FUTURE_IDEAS.md
│
├── product/
│   ├── vision.md                      ← Product vision, problem, differentiator, goals
│   └── mvp-scope.md                   ← MVP constraints and core features
│
├── architecture/
│   ├── system-overview.md             ← Tech stack, architecture flow
│   ├── cv-pipeline.md                 ← Pose estimation abstraction, AI/rule layer separation
│   ├── exercise-modules.md            ← Modular analyzer structure
│   ├── feedback-system.md             ← YAML-based configurable rule system
│   └── class-diagram.md              ← Mermaid class diagram of current engine
│
├── management/
│   ├── ENGINE_PROGRESS.md             ← E1–E5 phase tracker
│   ├── CURRENT_SPRINT.md              ← Active sprint tasks
│   ├── PROJECT_STATUS.md              ← Current project status
│   ├── ROADMAP.md                     ← Phase-by-phase roadmap
│   ├── DECISIONS.md                   ← Architecture decision log
│   └── DAILY_LOG.md                   ← Daily activity log
│
├── sessions/                          ← Per-session work logs
│   ├── 2026-05-14.md
│   ├── 2026-05-15.md
│   ├── 2026-05-18.md
│   ├── 2026-05-19.md
│   ├── 2026-05-21.md
│   ├── 2026-06-06.md
│   └── 2026-06-19.md                 ← Latest session
│
└── ChatGPT/                           ← ChatGPT session context files (git-ignored)

---

## Engine Phase Status

| Phase | Name                      | Status        |
|-------|---------------------------|---------------|
| E1    | Semantic Pose Foundation  | Complete      |
| E2    | Biomechanics Foundation   | Complete      |
| E3    | Squat Movement Analysis   | In Progress   |
| E4    | Feedback Engine           | Not Started   |
| E5    | Visualization & UX        | Not Started   |

E3 progress:
  - A. Phase & Rep         — Complete
  - B. Core Metrics        — In Progress (next: Squat Depth)
  - C. Control & Stability — Not Started
  - D. Mobility            — Not Started
  - Infrastructure         — Not Started

---

## Tech Stack

- Language: Python 3.9
- Pose estimation: MediaPipe
- Testing: pytest
- Mobile app: React Native + Expo (planned, E5)
- Backend API: FastAPI (planned, E5)
