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

## 2026-05-19
- `engine/pose/landmarks.py`: `PoseLandmark` IntEnum with named joint access
- `engine/pose/accessors.py`: `get_landmark()`, `get_landmarks()` — removes raw index usage
- `engine/pose/chains.py`: kinematic chain definitions for legs, arms, torso
- `engine/biomechanics/vector.py`: `Vector2D`, `to_vector`, `vector_length`, `dot_product`
- `engine/biomechanics/angles.py`: `calculate_angle(a, b, c)` returning degrees
- `engine/biomechanics/visibility.py`: `is_visible()`, `all_visible()`
- Tests added for all new modules
- `feature/pose-foundation` and `feature/biomechanics` branches pushed to remote

## 2026-05-21
- `engine/biomechanics/smoothing.py`: `OneEuroFilter` (float-level), `LandmarkOneEuroFilter` (Landmark-level)
- Inline comments added explaining algorithm variables and design rationale
- `engine/biomechanics/smoothing.py`: `float | None` → `Optional[float]` — Python 3.9 호환성 수정
- `tests/test_biomechanics_smoothing.py`: 포괄적 테스트 작성 및 통과 (15개 테스트)
- `docs/management/ENGINE_PROGRESS.md` 신규 생성 — E1–E5 엔진 진행 트래커
- `docs/management/ROADMAP.md` 업데이트 — 제품 로드맵에 E1–E5 엔진 개발 플랜 통합
- docs를 `main`에서 관리하는 방식으로 전환
