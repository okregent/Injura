# Current Sprint

## Sprint Goal
Project scaffolding — establish the base code structure for development to begin.

## Tasks

### Setup
- [x] Scaffold `engine/` (pose module complete)
- [ ] Scaffold `apps/api` (FastAPI)
- [ ] Scaffold `apps/mobile` (React Native + Expo)

### Engine
- [x] Define `PoseEstimator` interface (`engine/pose/base_estimator.py`)
- [x] Implement `MediaPipePoseEstimator` adapter (`engine/pose/mediapipe_estimator.py`)
- [x] Define pose types (`engine/pose/types.py`)
- [ ] Define `ExerciseAnalyzer` base class
- [ ] Implement `SquatAnalyzer`
- [ ] Create `squat_rules.yaml`

### Tests
- [x] `test_extract_pose_sequence`
- [x] `test_visualize_pose_estimation`

### API
- [ ] Basic FastAPI project setup
- [ ] Video upload endpoint
- [ ] Analysis endpoint

## Not In This Sprint
- Mobile UI implementation
- Database integration
- Authentication
