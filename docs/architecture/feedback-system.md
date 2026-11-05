# Injura — Feedback System

## Current Implementation

Implemented on `feature/biomechanics`; agreed E4 implementation scope is complete.
Empirical measurement/coaching validation remains deferred. See
[acceptance and deferred scope](../validation/E4_IMPLEMENTATION_ACCEPTANCE.md).

The flow is measurement analysis → capture/quality-gated cards → optional
descriptive personal comparison → prioritized actions and session overview.
Every result retains reasons and repetition/metric evidence. Unknown capture
conditions request review; rejected conditions request retake. No posture score
or injury-risk judgment is supplied.

Configured numeric conditions use `engine/squat/squat_rules.json`, empty by
default. YAML and other exercise rules are future work. Conditions compare
explicit caller-supplied values, not validated coaching criteria; see
[measurement rules](measurement-rules.md) and [recording review](recording-review.md).

[Projected body profiles](body-profile.md) retain original source identity,
manual point measurements and uncertainty. Preparation baselines describe observed
movements, not ideal technique. Changes in profile/setup/side/facing/runtime
withhold comparison; unsupported current observations also remain withheld.
Body proportions do not yet adjust posture thresholds automatically.

[Session overview](e4-session-overview.md) preserves partial/unavailable states
and exposes the first action without discarding lower-priority evidence.
The E3 evaluation handoff is an unapproved review packet, not runtime coaching
authorization. Validated corrective messages and adaptive thresholds require
independent measurement and feedback validation before activation.
