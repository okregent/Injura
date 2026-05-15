# Injura — CV Pipeline

## Pose Estimation Abstraction
The system avoids hard dependency on a single pose estimation framework.

```
PoseEstimator (Interface)
├── MediaPipePose
├── MoveNet
└── Future Pose Models
```

## AI Layer vs Rule Layer

### AI Layer
Responsibilities:
- Landmark extraction
- Pose estimation
- Temporal movement tracking

### Rule Layer
Responsibilities:
- Biomechanics interpretation
- Personalised thresholds
- Feedback logic

This separation improves maintainability, explainability, and scalability.
