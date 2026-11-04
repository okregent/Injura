# Injura — MVP Scope

## MVP Constraints
- Squat analysis only
- Side-view video only
- Upload-based analysis (offline, no real-time)
- MediaPipe Pose first
- Mobile application MVP
- No medical diagnosis
- No injury treatment claims

## Core Features
- User profile setup (body proportions, mobility limitations, discomfort areas)
- Side-view squat video upload
- Pose estimation using MediaPipe Pose
- Relative and hip-to-knee squat depth analysis
- Knee and hip flexion angles at bottom
- Torso lean analysis
- Body-segment-normalized knee travel analysis
- Heel lift magnitude and duration
- Descent, bottom, ascent, and total rep timing
- Rep-to-rep consistency
- Analysis confidence and recording quality validation
- Adaptive biomechanics-aware feedback

## Measurement Boundaries
- Side-view measurements must remain separate from feedback interpretation.
- Lumbar rounding and ankle mobility are not directly diagnosed from pose
  landmarks; the MVP may provide conservative, explainable proxy feedback.
- Hip shift, knee valgus, and left-right asymmetry require additional views and
  are outside the MVP.
