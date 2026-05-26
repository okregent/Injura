# Class Diagram — Engine (Current State)

> Last updated: 2026-05-26
> Covers: `engine/pose/` and `engine/biomechanics/`

---

```mermaid
classDiagram

    %% ══════════════════════════════════════════
    %% LAYER 1 — Pose Data
    %% Core data structures that flow through the entire engine
    %% ══════════════════════════════════════════

    class Landmark {
        +float x
        +float y
        +float z
        +float visibility
    }

    class PoseFrame {
        <<type alias>>
        List~Landmark~
    }

    class PoseSequence {
        <<type alias>>
        List~PoseFrame~
    }

    PoseFrame --> Landmark : contains
    PoseSequence --> PoseFrame : contains


    %% ══════════════════════════════════════════
    %% LAYER 2 — Pose Estimation
    %% Extracts raw landmarks from video
    %% ══════════════════════════════════════════

    class BasePoseEstimator {
        <<abstract>>
        +extract(video_path str) PoseSequence
        +close()
    }

    class MediaPipePoseEstimator {
        -mp_pose
        -pose
        +extract(video_path str) PoseSequence
        +close()
        +visualize(frame, pose_landmarks)
    }

    MediaPipePoseEstimator --|> BasePoseEstimator
    BasePoseEstimator ..> PoseSequence : returns


    %% ══════════════════════════════════════════
    %% LAYER 3 — Pose Semantics
    %% Gives raw landmark indices human-readable names
    %% ══════════════════════════════════════════

    class PoseLandmark {
        <<IntEnum>>
        NOSE = 0
        LEFT_SHOULDER = 11
        RIGHT_SHOULDER = 12
        LEFT_HIP = 23
        RIGHT_HIP = 24
        LEFT_KNEE = 25
        RIGHT_KNEE = 26
        LEFT_ANKLE = 27
        RIGHT_ANKLE = 28
        ...
    }

    class Chains {
        <<constants>>
        LEFT_LEG_CHAIN : List~PoseLandmark~
        RIGHT_LEG_CHAIN : List~PoseLandmark~
        LEFT_ARM_CHAIN : List~PoseLandmark~
        RIGHT_ARM_CHAIN : List~PoseLandmark~
        TORSO_CHAIN : List~PoseLandmark~
    }

    class Accessors {
        <<functions>>
        get_landmark(frame, landmark) Landmark
        get_landmarks(frame, landmarks) List~Landmark~
    }

    Chains --> PoseLandmark : groups
    Accessors ..> PoseLandmark : uses as index
    Accessors ..> PoseFrame : reads from
    Accessors ..> Landmark : returns


    %% ══════════════════════════════════════════
    %% LAYER 4 — Biomechanics
    %% Computes meaningful measurements from landmarks
    %% ══════════════════════════════════════════

    class VectorUtils {
        <<functions>>
        to_vector(a, b) Vector2D
        vector_length(v) float
        dot_product(v1, v2) float
    }

    class AngleUtils {
        <<functions>>
        calculate_angle(a, b, c) float
    }

    class VisibilityUtils {
        <<functions>>
        is_visible(landmark, threshold) bool
        all_visible(landmarks, threshold) bool
    }

    class OneEuroFilter {
        <<dataclass>>
        +float min_cutoff
        +float beta
        +float derivative_cutoff
        -Optional~float~ previous_value
        -float previous_derivative
        +filter(value float, dt float) float
    }

    class LandmarkOneEuroFilter {
        <<dataclass>>
        +OneEuroFilter x_filter
        +OneEuroFilter y_filter
        +OneEuroFilter z_filter
        +OneEuroFilter visibility_filter
        +create(min_cutoff, beta, derivative_cutoff)$ LandmarkOneEuroFilter
        +filter(landmark Landmark, dt float) Landmark
    }

    AngleUtils ..> VectorUtils : delegates to
    AngleUtils ..> Landmark : takes 3 landmarks
    VectorUtils ..> Landmark : takes as input
    VisibilityUtils ..> Landmark : takes as input

    LandmarkOneEuroFilter *-- OneEuroFilter : x / y / z / visibility
    LandmarkOneEuroFilter ..> Landmark : takes / returns
```

---

## Layer Overview

```
VIDEO
  │
  ▼
┌─────────────────────────────┐
│  LAYER 2 — Pose Estimation  │  MediaPipePoseEstimator
│  video → PoseSequence        │  (extracts raw landmarks)
└─────────────────────────────┘
  │  PoseSequence
  ▼
┌─────────────────────────────┐
│  LAYER 3 — Pose Semantics   │  PoseLandmark, Accessors, Chains
│  index → named landmark      │  (gives landmarks human-readable names)
└─────────────────────────────┘
  │  Landmark (by name)
  ▼
┌─────────────────────────────┐
│  LAYER 4 — Biomechanics     │  vectors, angles, visibility, smoothing
│  landmark → measurement      │  (computes meaningful values)
└─────────────────────────────┘
  │  angles, velocity, direction  (temporal utilities — upcoming)
  ▼
┌─────────────────────────────┐
│  E3 — Squat Analysis        │  (not yet implemented)
└─────────────────────────────┘
```

---

## Data Flow Example: "What is the knee angle?"

```
PoseSequence[frame_n]
    → get_landmark(frame, PoseLandmark.LEFT_HIP)      → Landmark
    → get_landmark(frame, PoseLandmark.LEFT_KNEE)     → Landmark
    → get_landmark(frame, PoseLandmark.LEFT_ANKLE)    → Landmark
    → calculate_angle(hip, knee, ankle)               → float (degrees)
```
