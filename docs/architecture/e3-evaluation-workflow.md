# E3 Evaluation Workflow

Implemented on `feature/biomechanics`; documents live on `main`. This workflow
executes the predeclared [v0.1 protocol](../validation/E3_PROTOCOL_v0.1.md), not a
posture score or medical assessment. It introduces no new dependencies and does
not change Full defaults, measurement algorithms or target-tempo scope.

## Commands When New Videos Arrive

Use the project's Python environment and run from the repository root:

```bash
python -m tools.evaluate_e3 prepare new_side_01.mp4 new_side_02.mp4 new_side_03.mp4 --output artifacts/e3-evaluation/batch-01
python -m tools.evaluate_e3 aids artifacts/e3-evaluation/batch-01
python -m tools.evaluate_e3 check artifacts/e3-evaluation/batch-01
```

Names are examples, not existing evaluation data. `prepare` creates a new local
bundle and refuses an existing output directory or duplicate source content.
It hashes videos, copies predeclared limits, creates side-specific unknown review
records and unconfirmed empty reference files. It does not approve sources,
infer participant identity, count actual repetitions or populate ground truth.

`aids` exports sequentially decoded original source frames and a local viewer
with exact frame stepping. No predicted joints/counts or automatic reference
boundaries are shown. When reference events exist, the ten prescribed positions
can be opened directly. Images may be resized; original dimensions/source hashes
are recorded. This is a review aid, not independent annotation. New aid runs use
a new output directory when needed and never overwrite reference JSON.

Complete the manifest's participant/source-group IDs, reviewed provenance,
development-use status, selected body side and facing direction. Review capture
conditions and independent references using the
[reference format](../validation/E3_REFERENCE_FORMAT_v0.1.md) and
[recording review](recording-review.md) contracts. Request only necessary human
confirmation; the user need not label every frame or type model-derived numbers.

Additional sources may be appended while the bundle is unfrozen:

```bash
python -m tools.evaluate_e3 register artifacts/e3-evaluation/batch-01 new_wrong_view.mp4 new_occlusion.mp4 new_cadence_case.mp4
```

Existing review/reference files remain intact; a registry backup named
`manifest.before-register-*.json` is saved before updating the manifest.
Registration is backed up, not a multi-file transactional database: interrupted
work can leave unused draft files. Preserve/recover the registry backup and
inspect `check` output rather than deleting existing annotations. Frozen bundles
cannot be appended to. Do not relabel a compliant clip as a violation without
reviewing its actual condition and expected affected items.

## Readiness and Input Freeze

`check` reports missing files/metadata/review/reference evidence. Exit code 0
means ready; 2 means incomplete/ineligible. A count agreement or available
landmarks never supplies missing review. Existing development/quarantined hashes
are blocked even after rename. Related edits/crops require truthful source-group
review; different hashes alone do not prove independence.

The predeclared three compliant clips/participants and three violation cases,
signed item conditions, independent references and uncertainty/coverage quotas
are required before primary freeze. Negative cases must explicitly partition
all metric IDs into affected and unaffected sets; wrong view may affect all.

```bash
python -m tools.evaluate_e3 check artifacts/e3-evaluation/batch-01
python -m tools.evaluate_e3 freeze artifacts/e3-evaluation/batch-01
python -m tools.evaluate_e3 run artifacts/e3-evaluation/batch-01
python -m tools.evaluate_e3 status artifacts/e3-evaluation
```

`freeze.json` is exclusive and never overwritten. It binds video SHA-256, review,
reference, manifest and limits bytes; analysis/policy and evaluation source code;
the predeclared inventory/protocol; Python/package/platform versions; and Full
landmark/detector weights and pose graph. Primary run verifies before and after
inference. Changes reject the run instead of silently accepting a new condition.
This is reproducibility checking, not a signature securing files from their owner.

Container metadata alone do not validate cadence. Source-specific side/FPS review
is required and reference frame ranges are checked against decoded source count.
In-memory testing injection is not available as a CLI prediction source.

## Results and Restrictions

Primary inference is fresh Full extraction with fixed predeclared parameters;
no optional recovery, posture/robust calibration, best-side selection or mixed
coordinates. Candidates remain separate. Output lives in a new `runs/<UTC-id>`
directory with JSON evidence and HTML; it does not overwrite earlier results.

The scorer records chronological one-to-one cycle matches, misses/spurious
cycles, boundary and total-duration error, scalar and prescribed-frame errors,
coverage, uncertainty-gated reference readiness, consistency recomputation and
phase-duration arithmetic. Required missing values remain in the coverage
denominator. Mean error cannot hide a failed maximum or quota. Unconfirmed
reference data are never graded as an accuracy pass.

Violation checks exercise reviewed item eligibility/isolation, not automatic
camera classification. Physical phase/pause and heel-duration events remain
restricted; arithmetic consistency is not physical event validation. A primary
pass is limited to evaluated scope and does not automatically mark every E3/E4
requirement or injury-prevention efficacy complete.

`status` builds `artifacts/e3-evaluation/index.html` with ready/frozen/latest-run
state and links to reports/viewers. The sample dashboard links to this hub when
present. No new browser tabs, source uploads or notifications are required.

## Development-Only Wiring Checks

```bash
python -m tools.evaluate_e3 run artifacts/e3-evaluation/development-smoke-2026-11-05 --development-smoke
```

A smoke bundle needs explicit side/facing but permits unknown reviews/references.
It always remains `not_evaluated`; reference values are not used as truth.
It cannot run on a frozen bundle. Smoke source hashes are remembered from
sibling bundles' run history in the same collection, blocking later held-out
registration/freeze. History moved outside that collection or differently edited
footage still requires truthful provenance/development-use review. Do not run
smoke on intended held-out clips before preparing independent reference evidence.

Existing video 3 produced six baseline detections in the real local smoke check;
its source remains development data, and no actual accuracy pass was claimed.
The raw viewer contains all 588 frames and leaves annotation drafts unchanged.
All videos, individual reviews/references, frames, run evidence and generated
HTML remain under ignored `artifacts/`; only implementation/tests/docs are committed.

## Prepare Later Review Stages

Implemented on `feature/biomechanics`; documentation on main does not mean code
has been merged. After manually marking at least three complete cycles with
`start_source`, `deepest_interval` and `end_source`, expand the reference draft:

```bash
python -m tools.evaluate_e3 reference-scaffold artifacts/e3-evaluation/new-set/references/clip-001.json --output artifacts/e3-evaluation/new-set/references/clip-001-expanded.json
```

This creates a new file, preserves existing numeric entries, adds missing metric
slots and the prescribed ten frames for each of three angle measures. New
values and uncertainties stay null. Confirmation, reviewer and origin are reset;
the output requires independent review and must be selected in the manifest
before freeze. Existing files are never overwritten. This reduces transcription
work but does not calculate ground truth or remove uncertainty review.

After a run, prepare a separate review packet:

```bash
python -m tools.evaluate_e3 handoff artifacts/e3-evaluation/new-set/runs/RUN/results.json
```

Each invocation creates a fresh `handoff-TIMESTAMP/` HTML/JSON snapshot beside the
result, binding the source result by SHA-256. It groups per-item evidence,
preserves signed errors/coverage and exclusions, lists failed or pending items,
and checks that all required capture cases are represented. A complete primary
pass only makes the packet eligible for human measurement review. Smoke runs,
missing metrics/cases, insufficient clips and incomplete eligibility cannot advance.

The packet is not runtime authorization: measurement approval and coaching
approval remain pending, reviewer is empty and enabled rules remain empty.
Reviewers must separately verify frozen evidence, scope, proposed threshold
rationales/populations and feedback behavior. A checksum of a result is not proof
that its contents are valid; verify the original frozen bundle and runtime hashes.
The current numeric rule API remains an explicitly configured comparison tool;
this packet does not alter or enable it. Physical phase/heel-duration semantics
and clinical efficacy remain outside the accepted measurement scope.
