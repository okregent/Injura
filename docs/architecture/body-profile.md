# Projected Body Profile v1

Implementation branch: `feature/biomechanics`. This is a manual measurement
contract and storage foundation, not automated anthropometry or active coaching.

## Capture and Measurement Contract

Use an upright, still, full-body frame with a level camera, visible shoulder,
hip, knee and ankle, and the body aligned with the declared front or side view.
Record one explicit body side. All three segments must use the same source frame,
image coordinate scale and anatomical side; do not mix different views or frames.
These are reviewer assertions, not automatically verified camera conditions.

- Thigh: image-plane distance from hip landmark to knee landmark.
- Shank: image-plane distance from knee landmark to ankle landmark.
- Torso: image-plane distance from shoulder landmark to hip landmark.

These landmarks are observable proxies, not bone endpoints. Values are pixel
distances after restoring image aspect ratio, never raw normalized x/y distances.
Retain a conservative absolute uncertainty for each segment; zero is allowed by
the storage contract but is not an accuracy claim. Uncertainty must be nonnegative
and smaller than the length. Projection bias is not covered by these bounds.
Foot length is excluded from frontal capture. A second side-view profile is a
separate observation, not automatically averaged or fused with the frontal one.

## Storage and Derived Ratios

`engine.squat.profile.BodyProfile` stores schema version 1, a local profile ID,
source SHA-256, zero-based source frame, side/view, three projected lengths,
reviewer and nullable capture checks. No name, age or medical data is required.
`save_profile` creates new JSON only; `load_profile` validates field types and
numeric ranges. Store personal measurements under ignored `artifacts/`.

`summarize_profile(profile, source_sha256=...)` requires a matching source hash.
The caller must hash the actual source, verify frame existence and ensure lengths
were measured according to this contract; this function does not decode video.
Any rejected capture check withholds ratios; unknown checks or missing reviewer
require review. Reviewed projections provide thigh/shank, torso/thigh and
torso/(thigh+shank) ratios with conservative interval bounds. These are not
statistical confidence intervals or anatomical accuracy estimates.

Accuracy remains `not_validated` and coaching remains `pending_validation` for
every profile. Profiles do not modify analysis, feedback thresholds or rules.
Preparation-movement baselines, automatic segment extraction, longitudinal
comparison and profile-to-feedback integration are subsequent work. Do not treat
a user's habitual squat as a validated ideal movement.
