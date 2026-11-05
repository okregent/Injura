# E4 Implementation Acceptance — 2026-11-05

Status: **Agreed implementation scope complete; empirical/coaching validation deferred.**
Implementation branch: `feature/biomechanics`. This document on main does not
merge engine code or authorize a product release.

## Delivered Scope

| Capability | Acceptance evidence |
|---|---|
| Measured-cycle notices and quality/capture withholding | Measurement feedback, card and recording-review tests |
| Configured numeric conditions with empty defaults | Measurement-rule tests; no default coaching thresholds |
| Source-bound projected body profile with uncertainty | Body-profile and measurement-package tests |
| Original-frame click measurement and safe import/history | JavaScript coordinate/export checks and import validation |
| Personal setup readiness and fresh preparation inference | Setup lifecycle/source/frame/provenance tests |
| Descriptive baseline and compatible-context comparisons | Personal-baseline tests, runtime/context mismatch gates |
| Prioritized actions and session overview with supporting evidence | Overview tests and existing-video report smoke checks |
| Profile → preparation → current observations → overview boundary | `tests/test_e4_acceptance.py` synthetic integration tests |

Final full regression: **411 passed**, 17 existing external-library warnings.
Synthetic acceptance covers successful descriptive comparison, changed profile
context withholding and current-capture review withholding despite an existing
reviewed baseline. Test success establishes software behavior, not anatomical
accuracy, ideal technique or injury-prevention efficacy.

Local tools: `tools.review_samples`, `tools.personal_setup`; supporting contracts:
[session overview](../architecture/e4-session-overview.md),
[body profile and baseline workflow](../architecture/body-profile.md),
[numeric rules](../architecture/measurement-rules.md),
[capture review](../architecture/recording-review.md).

## Explicitly Deferred Validation and Future Work

- New filming, actual personal profile/preparation evidence and independent E3
  measurement evaluation, deferred at the user's request.
- Validated posture interpretation, correction wording and body-proportion-based
  adaptive thresholds. Ratios currently identify/describe the profile; they do not
  prescribe an ideal squat or automatically tune rules.
- Trunk-collapse, ankle-mobility limitation, compensation and variability
  interpretation; none is approved as a biomechanical/medical diagnosis.
- Automatic anatomical measurement, camera/side selection, calibrated confidence,
  physical phase/heel-duration interpretation and target-tempo goals.
- Product-facing API/mobile UX, release deployment and clinical efficacy claims.

Do not mark deferred items as passed merely to close E4 implementation. Default
rules remain empty; all coaching remains pending. Current-image observations and
habitual preparation movements are not ground truth. Existing sample clips are
development evidence only. All personal/generated outputs stay local and ignored
under `artifacts/`.

## Next Development Boundary

E5 product integration can consume the E4 result/overview without replacing its
withholding states or turning descriptive differences into errors. E5/API/mobile
implementation has not started as part of this closure. Reopen validation when
appropriate footage and reviewed references become available.
