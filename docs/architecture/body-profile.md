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
Automatic segment extraction and validated proportional correction thresholds
remain subsequent work. Do not treat a user's habitual squat as an ideal movement.

## Descriptive Preparation Baselines

Implemented on `feature/biomechanics`: `engine.squat.personal` builds per-item
median/minimum/maximum from at least three observation cards. Each included item
must have complete usable coverage across its supplied cycle cards and a named
reviewer. Unknown capture conditions, partial/recovered observations, experimental
calibration and unavailable values are already withheld by `build_feedback_cards`.
Missing items stay explicit and pending. The reviewer confirms evidence/provenance,
not that the movement is optimal or clinically correct.

The caller must supply truthful identity/setup assertions and reviewed,
source-bound preparation cards. `source_sha256` binds the preparation video;
`context` contains exactly:

- `profile_sha256`: SHA-256 of the reviewed profile JSON, not just its display ID.
- `setup_id`: caller-reviewed camera position/scale, stance, load and exercise setup.
- `side`, `facing`: explicit left/right inputs.
- `pipeline_sha256`: runtime signature from
  `tools.review_samples.personal_pipeline_signature` with matching model/options.

Before creating a baseline, verify the profile's actual source hash/frame and
reviewed projection status using the profile contract above. The baseline API
does not independently establish a person's identity, camera placement or profile
review. Do not reuse a setup ID when camera/stance/load conditions change.

```python
from engine.squat.personal import build_baseline, save_baseline

# preparation_cards come from reviewed preparation analysis, not gap candidates.
baseline = build_baseline(preparation_cards, context=context,
                          source_sha256=preparation_source_sha256,
                          reviewer=reviewer)
save_baseline(baseline, "artifacts/personal/baseline.json")
```

`save_baseline` creates a new JSON file only; `load_baseline` validates the stored
descriptive evidence. Passing no reviewer creates pending items, never an ideal
reference. The context/profile inputs and preparation intervals still need actual
user-specific evidence; no real baseline has been fabricated from existing clips.

The review API accepts `personal_baseline` and `personal_context`; the CLI accepts
both JSON files together:

```bash
python -m tools.review_samples VIDEO --facing left --recording-review REVIEW --personal-baseline BASELINE --personal-context CONTEXT
```

Reports compare only the declared body side and require matching facing/runtime.
Changed profile/setup/side/facing/pipeline context withholds comparison. Runtime
signatures include analysis code, installed model/environment artifacts and
model/recovery/calibration options. A changed runtime must not silently reuse an
old baseline. Current observations still need independent capture approval.
Signed differences from the preparation median remain descriptive, never posture
errors, improvements, scores or correction triggers. Body ratios identify the
profile context but do not yet mathematically adjust movement thresholds.

## Session Actions

Review HTML/JSON groups duplicate actions by status/action, prioritizing retake,
capture review, measurement review and then observations. Every grouped item
retains repetitions, metric fields and reasons. Existing no-cycle/candidate notices
remain available when there are no measurement cards. Raw analysis is unchanged.
