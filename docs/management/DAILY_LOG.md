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

## 2026-07-21
- engine/squat/metrics.py 리뷰 필요


## 2026-11-04
- Reviewed the project working tree and verified its existing tests.
- Corrected image aspect-ratio handling and defined knee/hip flexion consistently.
- Integrated validated features with depth, torso lean, and knee travel.
- Added reviewed-condition foot normalization, bottom joint angles, hip-to-knee
  separation, heel-rise proxy, FPS timing, and repetition consistency.
- Added ExerciseAnalyzer and SquatAnalyzer with independent metric outcomes,
  exclusion reasons, source-frame gap handling, and observed-data coverage.
- Updated metric contracts, architecture usage, decisions, progress, roadmap,
  project status, README, and the session handoff.
- Full suite passed: 203 tests, including real-video integrated analysis.
- User authorized commit and push on feature/biomechanics; main merge is deferred.
- Reaffirmed documentation-on-main policy: synchronize documentation separately
  and label unmerged implementation as feature/biomechanics. Engine merge remains deferred.

- Follow-up: reviewed sample videos 3-6; corrected phase chatter, aborted descents,
  and initial partial-cycle detection. Added separate unverified gap candidates.
- Videos 3/4 have 6/14 uninterrupted detections with phase timing on both sides.
  Video 5 has 2 left / 1 right candidates; video 6 has 3 per side. All counts
  remain unannotated. Full suite: 217 passed.
- Recorded the investigation in docs/validation/sample-review-2026-11-04.md;
  implementation stays on feature/biomechanics and documentation stays on main.
- Follow-up: recorded user count references (3: 6-7, 4: 14, 5: 2, 6: 3),
  added opt-in source-image recovery with provenance and posture calibration,
  and compared Full and Heavy using separate caches and matching recovery models.
- Video 5 reaches 2 complete detections per side with Full recovery; video 6
  reaches 3 with Heavy recovery. Video 6 bottom joint angles remain unavailable.
  Full stays the default; independent accuracy validation remains pending.
- Full suite: 245 passed. Local comparison artifacts are excluded from Git.
- Cross-video Heavy validation: with matched recovery/calibration, Heavy has
  5/5, 11/14, 1/1, 3/3 left/right detections on videos 3/4/5/6 versus Full's
  6/6, 14/14, 2/2, 0/0. Full remains default. Added local batch comparison
  HTML/CSV generation; inspected representative overlays. Targeted tests: 19 passed.
