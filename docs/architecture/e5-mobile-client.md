# E5 Expo Client

Implementation: `feature/biomechanics`, commits `7b307fc` and `5f9c51e`.
Documentation on main does not merge application code. This is a development
client, not a released native application. E5 remains in progress.

## Run and Verify

Tested with Node 22.22.0, npm 10.9.4, Expo SDK 58, React 19.3 and React Native
0.88.1. From `apps/mobile` on the implementation branch:

```powershell
npm ci
npm run typecheck
npm run lint
npm test
npx expo install --check
npx expo-doctor
npm run web
```

Start the [local API](e5-local-api.md) separately. For Expo web on port 8081,
set this environment variable in the API terminal before starting Uvicorn:

```powershell
$env:INJURA_DEV_ORIGINS='http://localhost:8081,http://127.0.0.1:8081'
.\venv\Scripts\python.exe -m uvicorn apps.api.main:app --host 127.0.0.1 --port 8000 --workers 1
```

The client defaults to `http://127.0.0.1:8000`; operators can enter another
address or set `EXPO_PUBLIC_API_URL`. This is public client configuration, never
a location for secrets. A phone's loopback address refers to the phone, not the
development computer. Native testing needs a reachable, trusted API environment
and a matching SDK runtime/development build. No global ATS/cleartext exception,
public API, EAS login, signing or store deployment was configured.

For a static web build, run `npx expo export --platform web`. Generated `dist`,
`.expo`, `.test-build`, node_modules, local environment files and personal videos
are excluded from Git. Retain the Expo template's MIT attribution in LICENSE.

## Implemented Workflow

1. Explicitly connect to the operator-selected API and read its capabilities.
2. Select one MP4/MOV with DocumentPicker; select visible body side and facing.
3. Explicitly request analysis. File selection alone never uploads anything.
4. Inspect measured cycles separately from excluded candidates. Candidates have
   no assigned measurements. Source-frame controls seek approximately using FPS.

The transport handles bounded file sizes, native file/content URIs and web Blobs,
multipart requests, error envelopes, connection/upload timeouts and cancellation.
Stopping the wait aborts the client request; it does not promise server-side
inference cancellation. Request generations prevent stale responses replacing
new selections. Changing videos clears side/facing and results. A source-keyed,
SDK-managed player prevents replacement-triggered autoplay; web object URLs are
released, while native picker-cache retention remains OS-managed.

Validation/capture/coaching states remain pending as supplied by the API. The
client cannot approve posture accuracy or authorize personalized coaching.
Mobile joint overlays, saved-JSON reopening, full body-profile editing, accounts,
result persistence and production authentication are not implemented. Saved-result
reopening and paused joint overlays are available in the separate browser preview.

## Verification and Remaining Work

2026-11-05: 469 Python tests, eight mobile transport tests, TypeScript, ESLint,
Expo dependency compatibility, 20/20 Expo Doctor checks and web export passed.
Actual browser uploads exercised video 4 (14 measured cycles) and video 5 (zero
measured cycles, two excluded candidates), source seeking, video replacement,
selection reset and client cancellation. The final player change produced no
browser console errors. These exploratory clips do not establish accuracy;
video 5 still differs from the user's two-repetition reference.

Android/iOS picker, permissions, device networking and native playback remain
unverified until a physical device is available. E3 independent references,
measurement accuracy and E4 coaching acceptance remain deferred.

`npm audit` reports 12 moderate dependency paths in the SDK/tooling tree,
including glob/minimatch advisories GHSA-3g3m-2fjr-6pw4 and
GHSA-g3hv-75wg-m249. Compatible `npm audit fix` did not resolve them; its proposed
forced Expo downgrade to SDK 52 was not applied. Do not describe this dependency
tree as security-cleared. Revisit upstream-compatible patches before distribution.
