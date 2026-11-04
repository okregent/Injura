# MVP Squat Recording Guide

Status: supported scope, 2026-11-04. Validate measurement reliability within
these conditions; compliance does not guarantee accuracy or injury prevention.

## Before Recording

1. **Record from the side.** Front, rear and oblique views are outside this
   MVP's posture-interpretation scope.
2. **Fix the camera in place.** Do not move it or change zoom during repetitions.
   Approximately hip-height placement is an initial engineering guideline;
   validated placement/angular tolerances have not yet been established.
3. **Keep the whole body and floor visible.** Include head, hips, knees, ankles,
   heels and toes throughout standing and the deepest posture, with margin.
4. **Make joints distinguishable.** Avoid backlighting, poor lighting and
   overlapping people. Clothing or equipment hiding a required joint may make
   the corresponding item unavailable, including occlusion by barbell plates.
5. **Record continuously from standing to standing.** Include a brief standing
   view at the beginning/end. Initial/final partial movements are not complete reps.
6. **Use original-speed footage.** Exclude slow motion, speed changes, cuts and
   stitched clips. Current phase timing assumes constant frame intervals; review
   timing eligibility separately when cadence is variable or uncertain.

## When Conditions Are Not Met

- Request another recording when view or whole-body framing clearly fails.
- Withhold items depending on obscured joints; preserve other supported items.
- Gap-crossing candidates are excluded from measured reps, angles, timings and
  consistency summaries.
- Withhold foot-length-normalized knee travel unless side view and side-on foot
  orientation are reviewed. This does not withhold every other metric.
- Observation support does not establish posture grades or injury-risk predictions.

## Current Implementation Boundary

The engine checks coordinate validity, visibility and missing observations. It
does not automatically validate every view, camera-motion, framing, source-speed
or editing condition. Human recording review is used during development today.
A user checklist alone is not automatic validation of recording/joint accuracy.

Frontal valgus, left-right asymmetry, true 3D angles and injury prediction are
outside this side-view MVP's E3 completion criteria. User-defined target-tempo
functionality is deferred; timing measurement remains in scope.

See [E3 acceptance](../validation/E3_ACCEPTANCE.md) for item gates and completion.
