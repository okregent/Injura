# Current Sprint

## Sprint Goal
Project scaffolding — establish the base code structure for development to begin.

## Tasks

### Setup
- [ ] Set up `.claude/commands/` for session workflows
- [ ] Scaffold `apps/api` (FastAPI)
- [ ] Scaffold `apps/mobile` (React Native + Expo)
- [ ] Scaffold `engine/` (pose, analyzers, feedback, rules)

### Engine
- [~] Define `PoseEstimator` interface — file created (`engine/pose/base_estimator.py`), implementation pending
- [~] Implement `MediaPipePose` adapter — file created (`engine/pose/mediapipe_estimator.py`), implementation pending
- [ ] Define `ExerciseAnalyzer` base class
- [ ] Implement `SquatAnalyzer`
- [ ] Create `squat_rules.yaml`

### API
- [ ] Basic FastAPI project setup
- [ ] Video upload endpoint
- [ ] Analysis endpoint

## Not In This Sprint
- Mobile UI implementation
- Database integration
- Authentication
