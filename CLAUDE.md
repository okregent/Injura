# Injura - Adaptive AI Squat Analyzer

## Claude Behavior Rules
- Always ask for confirmation before executing unless the user has explicitly instructed to proceed.
- Wait for the user's answer before executing. Do not execute at the same time as asking.
- If the user gives a direct command, execute without re-confirming.
- All written content (code, comments, documentation, files) must be in English.

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
└── sessions/
    └── 2026-05-14.md        ← latest session log
```

## Session Context
Last session: 2026-05-14
See docs/sessions/2026-05-14.md for full context.

### Current Status
- Project setup and documentation structure established
- Proposal document split into docs/

### In Progress
- Nothing yet

### Next Steps
- Set up .claude/commands/ for common workflows
- Begin project scaffolding
