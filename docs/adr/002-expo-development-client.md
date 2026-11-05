# ADR 002: Expo Development Client over the Local E5 Contract

Status: accepted for development, 2026-11-05.
Implementation branch: `feature/biomechanics`.

## Decision

Use Expo SDK 58 and Expo Router with a typed, independently tested HTTP adapter.
Keep inference in the existing bounded API. Require explicit API connection,
video selection, side/facing selection and upload. Preserve all response review
and validation gates rather than deriving coaching approvals in the client.

Use source-keyed SDK video players to own replacement/unmount lifecycle. Keep
native projects generated through Expo; do not weaken platform transport policy
for a local demonstration. Add opt-in loopback-only CORS for Expo web, disabled
by default. CORS is not authentication or permission to expose the API publicly.

## Consequences

Web exercises the real transport immediately. Physical Android/iOS checks still
require a matching runtime and reachable trusted API. Signing, authentication,
deployment, persistence and clinical/coaching acceptance remain separate work.
See the [client runbook](../architecture/e5-mobile-client.md) for verification,
dependency-audit findings and deferred scope.
