# Daily Log

## 2026-05-14
- Product name changed from Kineform to Injura
- Project defined as production-oriented, not a portfolio demo
- CLAUDE.md behaviour rules established
- Documentation structure agreed and created (`docs/`)
- Architecture documented: system overview, CV pipeline, exercise modules, feedback system
- Session log strategy decided: `docs/sessions/` for Claude context, Git for code history
- Planning agent concept dropped in favour of `docs/` structure

## 2026-05-15
- Repository initialised and linked to GitHub
- Base project structure created: `apps/`, `engine/`, `README.md`, `.gitignore`
- `docs/management/` created with project management files

## 2026-05-18
- `engine/pose/types.py` implemented: `Landmark`, `PoseFrame`, `PoseSequence`
- `engine/pose/base_estimator.py` implemented: `BasePoseEstimator` abstract class with `extract()` and `close()`
- `engine/pose/mediapipe_estimator.py` implemented: `MediaPipePoseEstimator` with `extract()`, `visualize()`, `close()`
- `tests/test_pose_estimator.py` created: `test_extract_pose_sequence`, `test_visualize_pose_estimation`
- `.gitignore` updated: `docs/ChatGPT/` ignored
- `.claude/commands/` setup dropped — not needed at current scale
