# ADR 001: Bounded Synchronous Local E5 API

Status: accepted for local development, 2026-11-05.
Implementation branch: `feature/biomechanics`.

## Context

E4 results and their pending-validation states need a transport boundary and a
remote-work-friendly way to exercise upload → inference → results without a
mobile app or production infrastructure. Existing data remains development-only.

## Decision

Use a thin FastAPI adapter over the existing engine/JSON response. Accept one
explicit-side/facing video per synchronous request with bounded request/file,
decoded-frame and dimension limits. Own temporary storage and a fresh model per
request, close/delete both after completion, and serialize inference admission
with a nonblocking process-local lock. Supply a same-origin browser preview.
Keep capture-review and personal-baseline uploads out of the public request
contract until trusted provenance/authorization is designed. Use empty coaching
defaults and preserve E4 unknown/withheld states. Bind to localhost, one worker.

## Consequences

This is immediately testable without a queue/database/account/deployment and
avoids accidental user assertions becoming coaching approval. It blocks competing
analyses with 429, repeats decoding/model setup, and requires the client to wait.
It provides no distributed queue, hard subprocess deadline, authentication or
public-production upload protection. A future production stage must revisit
isolation, job ownership, storage lifecycle, polling/cancellation and access control
before public exposure. An inference response is not validated posture feedback.

Details and tests: [local API runbook](../architecture/e5-local-api.md).
