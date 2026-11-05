# E4 Session Overview

Implementation branch: `feature/biomechanics`. `engine.squat.overview` provides a
versioned presentation summary over existing analysis, measurement cards and
optional personal comparisons. It does not change analysis or run posture rules.

`build_session_overview` retains detected cycle and excluded candidate counts,
per-status measurement-card counts, a primary action, personal comparison counts
and permanent pending validation labels. Card counts are not repetition counts or
accuracy scores. Candidates never become measured cycles.

## Session State

No detected complete cycles takes precedence and requests review of the source
and gaps. Detected cycles without cards require measurement review. Otherwise
the first present status in this order supplies the primary action:

1. `retake`: explicitly rejected recording conditions.
2. `capture_review`: unknown/unreviewed recording conditions.
3. `measurement_review`: unavailable or unsupported observations.
4. `observation`: observed measurements only, not approved technique.

Lower-priority evidence is preserved in counts and grouped actions. State
`observation` does not imply validated measurement accuracy. All summaries retain
`accuracy_status=not_validated` and `coaching_status=pending_validation`.

## Personal Comparison State

- `not_requested`: no baseline for this body side was requested.
- `no_observations`: a baseline was requested but no current cards exist.
- `comparison_unavailable`: no descriptive comparison can be provided.
- `context_mismatch`: comparison evidence contains incompatible context.
- `partial_comparison`: some, but not all, cards have descriptive comparisons.
- `descriptive_comparison`: every current card has descriptive comparison evidence.

The function rejects duplicate/out-of-range cards, duplicate/orphan comparison
evidence and descriptive comparisons over withheld observations. Absent comparison
entries remain incomplete. It validates presentation linkage, not underlying
anatomical accuracy or personal identity. See [personal baseline responsibilities](body-profile.md).

## Report Integration

The developer review JSON includes `session_overview` per explicit body side.
The HTML places the summary before evidence and collapses detailed per-repetition
cards. Existing recording gates, grouped evidence, measurement notices, raw metric
tables and configured numeric rule results remain available. No automatic side
selection, injury-risk label or personalized correction threshold is introduced.
Reports remain local and ignored under `artifacts/`.
