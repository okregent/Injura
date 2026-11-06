# iPhone Development Smoke Test

Prepared 2026-11-06. Implementation: `feature/biomechanics`; this document on
main does not contain the app. Native device verification is still pending.

## Prerequisites

- iPhone, its iOS version, and an Expo runtime compatible with this project's
  SDK 58. Check runtime compatibility on the device rather than assuming that
  an arbitrary Expo Go version supports this project.
- The implementation branch on a development PC with dependencies installed.
- A trusted API URL reachable from the phone. `127.0.0.1` on the phone is not
  the PC. The current API has no authentication; do not publish it as an open
  internet endpoint. Use a controlled private environment with trusted TLS.
- One existing, non-sensitive MP4/MOV under the API's file limit, saved in Files.
  New filming is not required for this integration check.

The app currently uses DocumentPicker, not direct camera capture or a Photos
library browser. Save/export a Photos video to Files first. An iCloud-only file
may need downloading before selection; check free storage and connectivity.

## Launch Sequence

1. Confirm whether the phone and PC are on the same Wi-Fi or at different
   locations. The app bundle and API are two independent connections.
2. On the implementation branch, from `apps/mobile`, run `npm ci` if needed,
   then `npx expo start --go --lan` for a compatible Expo Go runtime. Scan the
   terminal QR code with the iPhone Camera and open in Expo Go.
3. Allow local-network access if iOS requests it and LAN access is intended.
   A public/guest network may isolate clients. Do not disable the PC firewall
   globally; inspect the required application/network scope if blocked.
4. If the runtime rejects SDK compatibility, record both versions and stop this
   path. Do not downgrade the project blindly. A signed development build is
   the alternative; this repository has not configured expo-dev-client/EAS or
   Apple signing. From Windows, EAS can build iOS in the cloud; physical-device
   signing requires the appropriate Apple account/provisioning setup.
5. In Injura, enter the controlled API base URL and press Connect. First check
   its `/health` and `/v1/capabilities` from Safari if connection fails. Safari
   success is useful diagnosis but does not prove native transport policy works.
6. Choose the video from Files, select visible body side and facing, then press
   Analyze. Selection alone must not upload. Do not substitute the Metro URL
   for the API URL.

`npx expo start --tunnel` can help with the development bundle connection, but
does not expose or secure the separate analysis API. No tunnel was started as
part of preparation. Native requests do not require browser CORS; enabling CORS
does not solve device routing or certificate trust problems.

## Short Acceptance Checklist

| Check | Expected behavior |
|---|---|
| Cancel picker | No upload, crash or accidental file replacement |
| Pick Files MP4/MOV | Local video opens paused; side/facing explicitly selected |
| Explicit Analyze | One request; waiting/error/result states are understandable |
| Result | Measured cycles separate from candidates; pending validation retained |
| Playback and phase seek | Play/pause and approximate FPS-based navigation work |
| Replace while playing | New video starts paused; previous results/selection clear |
| Stop waiting | Client stops waiting; no claim that server processing stopped |
| Network interruption | Recoverable error; no stale result overwrites a new selection |
| Background/foreground | No crash; document actual playback/request behavior |

These checks establish integration behavior, not anatomical accuracy or injury
prevention effectiveness. Existing video 5's zero measured cycles/two candidates
is a known development result, not acceptance against the user's two repetitions.

## Local Test Record

Keep personal test records under ignored `artifacts/iphone-review/`, not Git.
Record date, iPhone model, iOS, Expo runtime/version, implementation commit,
network type, video identifier (avoid personal filenames), checklist outcome and
exact error text. Redact tokens, personal hostnames and identifying screenshots.
Do not label unexecuted checks passed.

## Preparation Evidence

On 2026-11-06, `npx expo export --platform ios --output-dir dist/ios-check`
generated one 2.5 MB Hermes bytecode bundle successfully in the ordinary Windows
execution environment. The sandbox-only attempt failed with compiler exit 6;
the same code succeeded outside it. TypeScript and ESLint passed. Generated
bundles/logs remain ignored. This is not an IPA, Xcode compile, signature,
installation or physical-device test.

Official references checked during preparation:
[Expo start](https://docs.expo.dev/get-started/start-developing/),
[development builds](https://docs.expo.dev/develop/development-builds/introduction/),
[Windows/iOS FAQ](https://docs.expo.dev/faq/).
