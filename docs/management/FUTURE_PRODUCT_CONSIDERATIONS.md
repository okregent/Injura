# FUTURE_PRODUCT_CONSIDERATIONS

Tracks features, architectural ideas, and research topics intentionally deferred beyond the MVP.

---
         
## Rules

Only record ideas that are intentionally deferred beyond the current development phase.

Do not duplicate items already scheduled in ENGINE_PROGRESS.md.

This document is a design backlog for the final product, not an implementation checklist.

# E3 — Squat Movement Analysis

## Biomechanics

- Individual mobility baseline calibration
- Dynamic range-of-motion analysis
- Joint angle velocity / acceleration metrics
- Adaptive metric thresholds based on user characteristics

## Squat Metrics

### Squat Depth

- Competition-standard depth classification
- Multi-view depth validation

### Torso Lean

- Personalized acceptable torso angle
- Torso angle velocity
- Excessive forward collapse detection

### Lumbar Rounding

- Direct lumbar curvature estimation beyond the side-view MediaPipe proxy
- Pelvis orientation integration
- Confidence score for lumbar assessment

### Heel Lift

- Multi-view foot-pressure and contact inference
- Footwear-aware heel-contact estimation

### Knee Tracking

- Dynamic knee path analysis
- Multi-view knee tracking

## Stability

- Center-of-mass approximation
- Bilateral stability score
- Weight shift estimation
- Balance consistency across repetitions
- Bottom bounce detection after velocity and acceleration validation
- Jerk-based movement smoothness scoring

## Tempo

- Pause detection at multiple positions
- Automatic tempo prescription comparison

## Fatigue

- Technique degradation across repetitions
- Fatigue trend detection
- Automatic "last good rep" identification

## Multi-view Expansion

- Knee valgus
- Foot rotation
- Stance width
- Left-right asymmetry
- Pelvic rotation
- Shoulder rotation

## 3D Expansion

- Multi-camera support
- Depth estimation
- Full 3D pose reconstruction

---

# E4 — Feedback Engine

## Personalization

- Adaptive coaching based on user history
- Beginner / Intermediate / Advanced feedback profiles
- Mobility-specific coaching
- Injury-aware recommendations

## Explainability

- Confidence score for every feedback item
- Evidence-based explanations
- Frame references for detected issues

## Learning

- User improvement tracking
- Long-term trend analysis
- Personalized coaching progression

---

# E5 — Visualization & UX

## Visualization

- Interactive timeline
- Metric overlays
- Side-by-side repetition comparison
- Best vs worst rep comparison

## Reports

- Session summary
- Progress dashboard
- Historical trends
- Exportable reports

## Mobile UX

- Live recording guidance
- Camera positioning assistant
- Recording quality validation

---

# Future AI

- Automatic issue prioritization
- Natural-language movement explanation
- Personalized training recommendations
- Exercise recommendation engine
- Cross-exercise movement pattern analysis

---

# Research Ideas

- IMU integration
- Wearable sensor fusion
- Force estimation from vision
- Ground reaction force estimation
- Injury risk prediction
- Real-time analysis
