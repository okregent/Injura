# E5 Squat Response v1

Implementation branch: `feature/biomechanics`. `engine.squat.response` is a
framework-independent response adapter, not a running HTTP API or upload service.
E4 agreed implementation is complete; E5 begins with this transport boundary.

```python
from engine.squat.response import build_squat_response

response = build_squat_response(analysis, extraction,
    source_sha256=actual_video_sha256, facing="left", recording_review=review)
```

The caller must bind the actual source hash, extraction, selected side/facing and
analysis to the same recording. Matching frame counts do not prove identity.
No body side is selected automatically. Personal comparisons may be supplied with
`baseline_requested=True` only after the caller performs the existing reviewed
baseline/context checks; the adapter validates overview linkage, not provenance.

## Contract

The detached JSON object contains schema version 1, exercise, source hash/frame
counts/FPS/image size, explicit selection, overview, capture gates, notices/cards/
actions/personal comparisons, repetition metrics/quality, candidates, consistency,
calibration/recovery/issues and pending interpretation status. Local paths, video
bytes and the complete pose landmark sequence are excluded.

Frame boundaries refer to zero-based original source frames, including sparse
pose detections. `bottom_phase_end` names the final BOTTOM-phase frame; it does not
claim a physical deepest posture. Candidates have separate boundaries, observed
bottom and reasons, with no fabricated metric values or measured-repeat numbers.
Quality coverage remains data availability, not accuracy probability.

Unavailable measurements remain null with their existing quality/reason. Empty
cycles are a valid response. Invalid indices/frame counts and nonfinite raw
numbers fail explicitly rather than emitting invalid JSON or silently rewriting
measurements. Returning a response does not approve posture, coaching or medical
interpretation. The original analysis is not modified, and response mutation does
not change engine objects.

## Verification and Remaining Integration

Eight adapter tests plus related E4/baseline/overview tests: **42 passed**. The
last full-suite run before this isolated adapter was 411 passed; it was not rerun
for this change. No new dependencies, personal artifacts or network service.
Subsequently integrated into the [local FastAPI and browser preview](e5-local-api.md).
Deployment, authentication/storage and actual filmed accuracy evaluation remain
outside the current development scope.
