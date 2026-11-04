# E3 Acceptance Contract — Supported Side-View MVP

Status: scope and completion gates defined, validation not complete (2026-11-04).
Implementation described here lives on `feature/biomechanics`; this document is
maintained on `main`. The user-facing scope is the
[recording guide](../product/RECORDING_GUIDE.md).

## Objective and Non-goals

E3 must produce traceable squat measurements within the supported recording
conditions, or explicitly withhold an unsupported item. E4 may interpret only
appropriately reviewed measurements using separately justified rules. This is
not evidence that the product prevents injury or predicts individual injury risk.

Limit validation to fixed-camera, continuous, full-body side-view clips with
usable visible joints. Do not expand the release requirement to every camera
angle, automatic side selection, interpolation, 3D truth, frontal valgus or
asymmetry. User-defined target-tempo functionality is deferred; existing timing
measurement remains part of E3. Automatic recording review is not a prerequisite
if documented human review is used, but an unreviewed clip is not approved.

## Recording Review and Item Gates

The following is the validation/interpretation contract. Human recording-review
gates are connected to configured rules; automated view classification and
empirical measurement validation remain pending.

| Condition | Required action | Current enforcement |
|---|---|---|
| Cannot decode frames or determine image size | Stop analysis with a reason | Implemented |
| Nonfinite or insufficiently visible required joint | Withhold dependent values/segments | Implemented via masks and metric outcomes |
| Missing source/hip observations inside a cycle | Exclude incomplete measured cycle; preserve separate candidates | Implemented |
| Wrong/unknown view or selected side/direction | Withhold posture interpretation; inspect or request another recording | Human review gate for view/side implemented; facing remains explicit caller input |
| Camera motion, zoom, body clipping or overlapping people | Review affected intervals/items; request another recording when support is inadequate | Human item-level recording gates; no validated automatic detector or interval-specific review |
| Unverified side view or foot orientation | Withhold foot-normalized knee travel | Implemented external-review flags |
| Missing FPS | Withhold timing and dependent summaries | Implemented |
| Variable/uncertain frame cadence or edit within measured interval | Withhold timing interpretation until source timing/continuity is established | Human timing gate implemented; raw analyzer still assumes constant FPS |
| Initial/final partial movement or setup | Exclude from complete-cycle references | Cycle-state support implemented; reference review required |
| Source-image re-detection or partial metric coverage | Preserve provenance; review before interpretation | Implemented quality status and rule withholding |
| Experimental calibration | Label experimental; withhold configured-rule interpretation | Implemented; independent validation pending |

A suspected source jump and a pose gap are separate observations. Do not infer
corrupt footage solely from a failed detector. Review the affected interval;
do not reject an entire clip solely because an unrelated interval has a jump.
Full remains default, model/side is explicit, and model coordinates are not mixed.

## Per-Item Validation

| Item | Reference needed | Evidence to report |
|---|---|---|
| Complete repetitions | Reviewed complete-cycle count, partial/setup exclusions | Missed/spurious detections per clip; candidates separately |
| Start/deepest/end | Reviewed frame ranges with uncertainty/plateau convention | Signed/absolute boundary error in source frames; seconds only with supported cadence |
| Knee/hip flexion, torso lean | Independently reviewed same-frame visible joint positions under the same 2D convention | Angle error in degrees; annotation uncertainty; unavailable cases |
| Hip-to-knee gap and relative descent | Reviewed joint positions and baseline/depth convention | Signed/absolute error in declared image units or ratio; perspective limitations |
| Heel rise proxy | Reviewed heel/toe motion and contact visibility | Proxy agreement and observed duration support; no ankle-mobility diagnosis |
| Raw/foot-normalized knee travel | Reviewed direction, knee/foot positions; side-on foot confirmed for normalization | Error in declared units/ratio; reasons for withholding |
| Consistency summaries | Validated constituent per-repetition measures | Included/excluded repetitions and propagation of exclusions |

An image strip or an assistant-proposed boundary is a review aid, not an
independent reference. Existing user counts are count references only. The
user need not label every frame: prepare evidence autonomously and request
review only where needed; retain reference provenance and unresolved uncertainty.

## E3 Completion Gates

Track implementation completion separately from validated readiness. No single
test-count, model benchmark, or sample-count constitutes empirical acceptance.

- [x] Supported recording scope and item-level withholding policy documented.
- [x] Core metric implementation, provenance, candidates and regression tests.
- [x] General recording-review record/gate connected to configured-rule interpretation;
  record reviewer, status and reasons, with unknown distinct from rejected.
- [x] Evaluation registration, blinded source-frame aids, readiness checks,
  input/code/runtime freeze and reference-based scoring infrastructure.
- [x] Validation manifest records clip identity/version, view, side/direction,
  cadence/continuity review, annotation origin and development/evaluation use.
- [x] Define initial engineering acceptance limits **before** the next evaluation: per-metric units,
  allowed reference uncertainty, boundary/measurement error targets, count
  criteria, usable-item coverage and withholding checks. See the versioned
  [v0.1 protocol](E3_PROTOCOL_v0.1.md). Defined targets are not validated accuracy;
  missing reviews, references or evaluation clips prevent acceptance.
- [ ] Review a bounded set of compliant recordings from different people and a
  small set of known violations. Keep clips used to tune the algorithm separate
  from later evaluation clips; do not claim statistical generalization from a
  small set or require an arbitrary sample total as proof.
- [ ] Evaluate each in-scope item against its reviewed reference and predeclared
  limits; record misses, spurious detections, unavailable outputs and uncertainty.
- [ ] Verify unsupported inputs/items are withheld with actionable reasons,
  and that otherwise supported items remain accessible.
- [ ] Resolve failures or explicitly narrow supported scope and reevaluate;
  publish versioned results and remaining limitations.

E3 is not marked complete until these gates are resolved. A metric that fails
validation stays experimental/unavailable for posture feedback; passing repetition
counting does not release unvalidated angles. Clinical injury-prevention efficacy
and E4's posture interpretation are separate validation work, not E3 test claims.

## Current Evidence and Next Work

Current automated suite: 331 passed at the last code change (2026-11-05). Videos 1-6 support
debugging and exploratory comparisons; 1/2 were existing test clips, 3-6 informed
algorithm changes. None forms an untouched independently annotated release set.
Full 3/4/5 produces 6/14/2 complete cycles with optional recovery/calibration;
Heavy helps video 6 and has documented failures elsewhere. These observations
are not empirical acceptance of joint accuracy or timing boundaries.

Recording-review gates are implemented for configured-rule evaluation; see
[review contract](../architecture/recording-review.md). The
[source inventory](e3-manifest-v0.1.json) and [limits](e3-limits-v0.1.json) are
prepared; no eligible evaluation clips or results exist. Next register sources,
complete recording/reference review and freeze the evaluation set. Continue within the agreed capture
scope rather than adding tempo targets, more report variants or unsupported
biomechanical diagnoses. See [sample evidence](sample-review-2026-11-04.md).

The [evaluation workflow](../architecture/e3-evaluation-workflow.md) is now
implemented. Its development-only smoke reproduces video 3's six detections
without claiming accuracy, and cannot become a primary acceptance result.
