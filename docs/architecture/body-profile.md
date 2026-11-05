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

## Source-Bound Setup Tool

Implementation branch: `feature/biomechanics` (`tools.personal_setup`). The local
developer workflow now creates the files above and builds baselines directly from
fresh preparation inference rather than accepting an arbitrary analysis report.

```bash
python -m tools.personal_setup prepare PROFILE_VIDEO PREPARATION_VIDEO --output artifacts/personal-setup/person-session
python -m tools.personal_setup status artifacts/personal-setup/person-session
python -m tools.personal_setup check artifacts/personal-setup/person-session
python -m tools.personal_setup build artifacts/personal-setup/person-session
```

`prepare` refuses an existing directory and creates `manifest.json`, `profile.json`,
`recording-review.json` and a local readiness screen. Lengths, uncertainty and
capture assertions remain empty/unknown. No identity, anatomy or camera review is
automatically inferred. Before build, fill real source-frame measurements and
review flags, select side/facing, identify the setup, name the reviewer and
explicitly confirm the profile/preparation sources belong to the same person.
This is still JSON-based developer input, not a consumer editing UI.

`check` verifies both source hashes, reviewed profile conditions, side agreement,
sequential decoding of the profile frame, and source-bound preparation review.
At least one supported item must have approved capture conditions. Input readiness
does not mean every measurement will be available, nor that E3 accuracy passed.
The command exits 2 when incomplete; `status` renders missing inputs without
approving them. Front/side perspective and landmark uncertainty still require
human judgment; metadata and hashes cannot establish identity or measurement truth.

`build` runs Full/default preparation analysis without recovery/experimental
calibration and excludes candidates. It checks source/setup/runtime changes before
writing a new `runs/TIMESTAMP/` snapshot containing baseline, context and evidence.
Evidence retains input-file hashes, source hashes, card observations and cycle/
candidate counts. Profile ratios identify context and remain descriptive.
Old snapshots are never overwritten. Fewer than three usable cycles, partial
coverage or unapproved items remain pending even after inference. Absent cards
count as missing when other items establish that a repetition exists.

The readiness screen links to snapshots and lists descriptive/pending item counts.
Pass each snapshot's `baseline.json` and `context.json` together to the report CLI.
Preserve source files, setup assertions and review records when reusing a baseline;
changed camera/stance/load conditions require a new setup and preparation review.
The screen/status JSON are refreshable views, not frozen validation evidence.
All personal files and developer HTML remain ignored under `artifacts/`.

## Point Measurement Aid

Implemented on `feature/biomechanics` (`tools.profile_measurement`):

```bash
python -m tools.personal_setup measure artifacts/personal-setup/person-session --frame 0
python -m tools.personal_setup import-measurement artifacts/personal-setup/person-session DOWNLOADED_PACKAGE.json
```

`measure` sequentially decodes the selected zero-based profile source frame,
verifies its source hash and exports an original-resolution PNG plus a standalone
local canvas page in a new `measurement-TIMESTAMP/` directory. The readiness screen
links to these pages. Select an upright frame; frame zero is a default index,
not an automatic standing-posture decision. No model points are prefilled.

Select body side/view, mark shoulder/hip/knee/ankle and enter explicit segment
uncertainty in original-image pixels. The canvas maps display coordinates back to
original pixels, retaining image aspect ratio. Missing points/selections or
uncertainty block download. The export contains point evidence and an unreviewed
profile; it is a measurement package, not the final profile schema.

`import-measurement` verifies the actual video hash, decoded frame dimensions,
finite in-image points and pixel lengths recomputed from those points. It clears
all reviewer/capture assertions even if the downloaded package supplies them.
It creates new profile/evidence files, backs up the current manifest and selects
the new profile through `profile_file`. The initial `profile.json` and previous
measured profiles remain unchanged. Changing the selected profile requires fresh
review and produces a different personal context hash. Import is backed up but is
not a multi-file atomic transaction; interrupted imports may leave unselected
new files. The manifest is checked for concurrent changes before writes.

Human capture review, uncertainty estimation and anatomical landmark placement
remain necessary; correct arithmetic does not establish correct anatomy. This aid
reduces numeric transcription but does not automatically estimate body proportions
or validate coaching. It never uploads video or silently updates runtime rules.
