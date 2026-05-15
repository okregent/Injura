# Injura - Adaptive AI Squat Analyzer

## Claude Behavior Rules
- Always ask for confirmation before executing unless the user has explicitly instructed to proceed.
- Wait for the user's answer before executing. Do not execute at the same time as asking.
- If the user gives a direct command, execute without re-confirming.
- All written content (code, comments, documentation, files) must be in English.
- The user receives code from Claude, understands it, and runs it themselves. Write code that is readable and easy to follow. Do not skip explanations.
- Always monitor .gitignore throughout the project. When new files or directories are introduced that should be ignored (e.g. build artifacts, env files, caches, generated files), explicitly mention it to the user.

## Coding Rules
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
│   └── feedback-system.md   ← YAML-based configurable rule system
├── management/
│   ├── PROJECT_STATUS.md    ← current project status
│   ├── CURRENT_SPRINT.md    ← active sprint tasks
│   ├── ROADMAP.md           ← phase-by-phase roadmap
│   ├── DECISIONS.md         ← ADR log
│   └── DAILY_LOG.md         ← daily activity log
└── sessions/
    └── 2026-05-15.md        ← latest session log
```

## Session Context
Last session: 2026-05-14
See docs/sessions/2026-05-14.md for full context.

### Current Status
- Project setup and documentation structure established
- Proposal document split into docs/
- `engine/pose/` skeleton created (files empty, implementation not started)
- `requirements.txt` created: mediapipe, opencv, numpy, matplotlib, scipy, jax, sounddevice

### In Progress
- Engine scaffolding (`engine/pose/` — files exist, implementation pending)

### Next Steps
- Set up `.claude/commands/` for common workflows
- Implement `PoseEstimator` interface (`engine/pose/base_estimator.py`)
- Implement `MediaPipePoseEstimator` adapter (`engine/pose/mediapipe_estimator.py`)
- Define pose types (`engine/pose/types.py`)
