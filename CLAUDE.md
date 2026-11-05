# Injura - Adaptive AI Squat Analyzer

## Claude Behavior Rules
- Always ask for confirmation before executing unless the user has explicitly instructed to proceed.
- Wait for the user's answer before executing. Do not execute at the same time as asking.
- If the user gives a direct command, execute without re-confirming.
- All written content (code, comments, documentation, files) must be in English.
- The user receives code from Claude, understands it, and runs it themselves. Write code that is readable and easy to follow. Do not skip explanations.
- Always monitor .gitignore throughout the project. When new files or directories are introduced that should be ignored (e.g. build artifacts, env files, caches, generated files), explicitly mention it to the user.

## Coding Rules
- Maintain project documentation on `main` and synchronize it into feature branches.
- Documents describing unmerged code must identify its implementation branch.
- Small commits
- One feature per branch
- Add tests for analysis logic
- Document major architecture decisions in docs/adr

## Docs Structure
All high-level documents are stored in docs/. Load relevant files explicitly at the start of each session as needed.

```
docs/
├── product/
│   ├── vision.md            ← product vision, problem, differentiator, long-term goals
│   └── mvp-scope.md         ← MVP constraints and core features
├── architecture/
│   ├── system-overview.md   ← tech stack, architecture flow
│   ├── cv-pipeline.md       ← pose estimation abstraction, AI/rule layer separation
│   ├── exercise-modules.md  ← modular analyzer structure
│   ├── feedback-system.md   ← YAML-based configurable rule system
│   └── class-diagram.md     ← Mermaid class diagram of current engine implementation
├── management/
│   ├── PROJECT_STATUS.md    ← current project status
│   ├── CURRENT_SPRINT.md    ← active sprint tasks
│   ├── ENGINE_PROGRESS.md   ← E1–E5 engine phase tracker (current task, completed/pending per phase)
│   ├── ROADMAP.md           ← phase-by-phase roadmap
│   ├── DECISIONS.md         ← ADR log
│   └── DAILY_LOG.md         ← daily activity log
└── sessions/
    └── 2026-11-04.md        ← latest session log
```

## Session Context
Last session: 2026-11-05
See docs/sessions/2026-11-05-e5-client.md and docs/sessions/2026-11-05.md for context.

### Current Status
- E1 (Semantic Pose Foundation) complete
- E2 (Biomechanics Foundation) complete
- E3-A (Phase & Rep) complete — phase detection, rep counting, smoothing, windowing
- `feature/biomechanics` active branch

### In Progress
- E3 empirical validation; core metrics, timing, consistency, and analyzer implemented
- Per-metric availability and observed coverage implemented; calibrated confidence pending
- Initial videos 3-6 reviewed; cycle-state fixes and unverified gap candidates implemented
- Latest full test suite: 469 passed; see docs/sessions/2026-11-05.md
- E4 agreed implementation scope complete; new filming/E3 empirical and coaching validation deferred
- Opt-in recovery/posture calibration and explicit Full/Heavy comparison implemented; Full remains default

### Next Steps
- Validate measurement proxies against annotated side-view recordings
- Validate automatic camera/foot-orientation detection (currently explicit external review)
- Calibrate confidence before exposing accuracy claims
- E5 JSON response, local FastAPI upload/inference and browser preview implemented; see docs/architecture/e5-local-api.md
- Local preview cycle/candidate navigation and selected-cycle evidence implemented; browser seeking is approximate
- Paused overlay and source-frame navigation checked in a native browser; independent filmed alignment acceptance remains pending
- Expo SDK 58 client implemented; eight transport tests and web workflow verified. Next: physical-device checks, product timeline/annotation and production integration. No public deployment or running background server
- OpenCV uses only opencv-contrib-python 4.10.0.84; pip check passes; API deps in apps/api/requirements*.txt
- Validate E4 corrective criteria after independent measurement validation; defaults remain empty

Mobile runbook: docs/architecture/e5-mobile-client.md. Known moderate npm tooling advisories remain; native device verification is pending.
