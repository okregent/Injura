# E3 Evaluation Protocol v0.1

Predeclared: 2026-11-04, before new evaluation. Status: protocol prepared; no
eligible evaluation clips or measurement-accuracy results yet. This is an initial
engineering target, not a scientifically established error bound, coaching
threshold, or injury-risk standard. Targets may fail; do not loosen them after
seeing results and call the same evaluation a pass.

## Versioned Inputs

- [Source manifest](e3-manifest-v0.1.json): SHA-256, size, metadata origin, source
  review/reference status, split and implementation revision.
- [Machine-readable limits](e3-limits-v0.1.json): proposed acceptance targets.
- [Capture scope](../product/RECORDING_GUIDE.md) and [E3 gates](E3_ACCEPTANCE.md).

Primary evaluation uses the recorded implementation revision, Full (complexity
1), unchanged 0.5 visibility policy, and no optional recovery, posture calibration
or robust fallback. Review signed conditions for the selected side. Do not pick
the model, side, thresholds or best run using known counts. Experimental variants
may be reported separately and cannot replace the primary result. Record any
pipeline/configuration change as a new evaluated revision; do not mix results.

## Existing Inventory and Initial Collection

| Source | Split | Reference status | Evaluation use |
|---|---|---|---|
| sample_video.mp4 | Development | No independent labels; frontal/oblique view observed | Existing test/debug only |
| sample_video2.mp4 | Development | No independent labels | Existing test/debug only |
| sample_video3.mp4 | Development | User reports 6-7; initial partial and source jump investigated | Development only |
| sample_video4.mp4 | Development | User reports 14 | Development only |
| sample_video5.mp4 | Development | User reports 2 | Development only |
| sample_video6.mp4 | Development | User reports 3 | Development only |
| sample_video_not_edited.mp4 | Quarantine | Origin and relation to existing clips unknown | No held-out status inferred from filename |

The current manifest's `evaluation_sources` is empty; all source eligibility is
false. Recording flags, reviewer, subject identity and direction remain unknown
until reviewed. Existing visual observations are not signed source approval.
Video 1 is already tracked on the implementation branch; its inventory hash is
from that exact Git blob and FPS/count from the existing cached report when not
present on `main`. Other metadata are container observations, not proof of
constant capture cadence. No videos or generated reports are newly added to Git.

Initial collection target: three compliant clips from three people, requesting
about three complete repetitions per clip, plus one case for each of wrong view,
joint occlusion, and uncertain/discontinuous timing. This is six coverage slots,
not a claim that six clips prove generalization. Review actual repetitions;
do not assume a recording instruction establishes the reference count.

Assign participant/source-group identifiers and record original-file provenance.
Related crops, edits and recordings from the same source group stay in one split.
Different hashes alone do not establish independence. Existing participant IDs
are unknown, so no participant-disjoint validation claim is currently supported.
Freeze the evaluation source list and implementation/configuration before runs.
If an evaluation clip is used for tuning, move it to development and collect
fresh evaluation evidence; retain original results and reasons for exclusions.

## References and Matching

Prepare reference aids autonomously; do not require the user to label every
frame. A named reviewer must confirm selected reference events/joints without
copying model output as truth. Unconfirmed assistant proposals are draft labels.
Escalate ambiguous cases for second review; unresolved uncertainty is not a pass.

Count complete standing-to-standing cycles, excluding setup and initial/final
partials. Store reviewed starts, deepest posture intervals and ends with source
frame indices, reviewer, uncertainty and source hash. Match predictions one to
one in chronological order with temporal IoU at least 0.5; use highest overlap,
then earlier reference ID to break ties while preserving order. Unmatched
predictions are spurious; unmatched references are missed. Candidates never
substitute for complete detections. Equal totals alone do not establish a match.

For framewise comparisons, preselect ten reference positions per compliant clip:
standing before the first complete repetition, then descent midpoint, deepest
posture and ascent midpoint for each of the first three complete repetitions.
Select using reviewed video events before inspecting prediction errors. Fewer
usable positions do not silently reduce the quota. Event uncertainty must be
no more than two frames; a genuine deepest-posture plateau is a separately
documented admissible interval, not an arbitrarily widened uncertainty band.

Review x/y joint coordinates independently under the catalog's aspect-corrected
2D convention: flexion = 180 minus the interior angle; torso angle from vertical.
Record annotation uncertainty (at most 2 degrees for angle references or 0.005
of the declared image axis for coordinates); unresolved labels stay pending.
Same-frame errors are evaluated at the fixed positions. Rep maxima/depth extrema
also require reviewed extremum locations; a passing selected frame does not
validate an entire-repetition maximum. Do not compare 2D proxies to 3D truth as
if they were interchangeable.

For derived ratios and extrema, propagate reference-coordinate uncertainty;
if it exceeds half of that item's MAE target, reference support is unresolved.
Do not treat a visually estimated denominator or baseline as exact.

## Initial Acceptance Targets

Apply each limit per clip and metric; publish pooled results only in addition.
Report signed bias, MAE, maximum absolute error, eligible/ready/missing counts,
withheld reasons and annotation uncertainty. MAE is over evaluated pairs and
must not hide missing pairs; the separate coverage gate still applies.

| Item | Initial engineering target |
|---|---|
| Complete repetitions | Zero missed and zero spurious on each compliant clip |
| Start / end boundary | Each at most 3 frames from reviewed event |
| Deepest observed frame | At most 2 frames from the reviewed deepest interval |
| Total repetition duration | Absolute error at most 6 source intervals (6/FPS seconds at reviewed constant cadence) |
| Knee/hip flexion, torso lean | MAE at most 5 degrees AND maximum error at most 10 degrees |
| Hip-to-knee gap / raw knee travel | MAE at most 0.01 AND maximum at most 0.02 of the declared image axis |
| Relative descent / foot-normalized knee travel | MAE at most 0.05 AND maximum at most 0.10 of the declared ratio |
| Heel-rise magnitude | MAE at most 0.005 AND maximum at most 0.01 of image height |
| Consistency | Validated inputs, correct exclusion set, recomputation error at most 1e-9 |

These limits express intended product sensitivity only. They have no established
clinical significance and are not fed into posture-feedback rules. Inspect
reference reproducibility and failures before claiming usefulness. Any revision
requires a new protocol version and a new predeclared evaluation, preserving v0.1.

Per-phase times currently describe calibrated position zones, not independently
confirmed physical pause events. Check duration sums to 1e-9 seconds, but do not
release claims of accurate physical descent/pause/ascent durations until their
independent event definitions and reference comparisons are specified. Heel-rise
duration similarly stays unvalidated without an independent event reference.
These items remain restricted, even if repetition count or total time passes.

## Coverage, Withholding and Decisions

For each metric/clip, at least 90% of predeclared eligible reference items must
be interpretation-ready: approved recording review, finite value, `available`
quality, and no recovered observations or experimental calibration. Missing
reference items are reported as unready, never dropped to improve coverage.
Do not report only easy visible cases. Ten preselected framewise references
per clip are a minimum evidence quota, not statistical confidence calibration.

Known-violation cases must withhold every affected configured-rule interpretation
with a usable reason, preserve raw values where measurable, and avoid rejecting
unrelated supported items. Record the expected affected items before the run.
Human-review rejection tests are not evidence of automatic camera classification.
Candidates must remain excluded and unknown review must never become approval.

Decisions: `pass` only with references, coverage and all applicable error/gating
targets met; `fail` for evaluated violations; `not_evaluated` for missing sources,
reviews, labels or undefined event semantics. Any pending required slot/metric
prevents overall acceptance. Unsupported metrics remain withheld/experimental
or are explicitly removed from released scope. Do not mark E3 complete yet.

## Next Execution Step

Register compliant and violation clips, complete signed capture review and
reference provenance, freeze the evaluated source list, then run the implemented
[evaluation workflow](../architecture/e3-evaluation-workflow.md). Reference
schema: [v0.1 reference format](E3_REFERENCE_FORMAT_v0.1.md).

Implementation follow-up (2026-11-05): 331 regression tests pass. A real video 3
development smoke retains six detections and stays not evaluated. There is still
no independent accuracy result; numeric v0.1 limits are unchanged. The workflow
records hashes, versioned input/code/runtime/weights and excludes candidates and
missing-reference shortcuts. Local smoke history supplements reviewed provenance
but cannot prove all source edits or annotation independence.
