# E5 Local Analysis API and Browser Preview

Implementation branch: `feature/biomechanics`, code `8d143d1`; documentation on
main does not merge engine/API code. This is a local development service and
browser preview, not a deployed/authenticated product or mobile application.

## Install and Run

Run from the repository root in the project Python 3.9 environment:

```powershell
.\venv\Scripts\python.exe -m pip install -r requirements.txt -r apps/api/requirements-dev.txt
.\venv\Scripts\python.exe -m pip check
.\venv\Scripts\python.exe -m uvicorn apps.api.main:app --host 127.0.0.1 --port 8000 --workers 1
```

For runtime only, use `apps/api/requirements.txt` instead of the dev requirements.
Open `http://127.0.0.1:8000/` for the upload/results preview; `/docs` exposes
interactive API documentation. The preview requires the running server; opening
the HTML file directly is not supported. Do not expose this unauthenticated local
service publicly. Remote use requires the user's controlled tunnel/environment;
no remote server, public deployment or background process was created here.

The new requirements pin tested FastAPI 0.128.8, Starlette 0.49.3, Pydantic 2.13.5,
python-multipart 0.0.20 and Uvicorn 0.39.0; dev adds HTTPX 0.28.1 and pytest 8.4.2.
The existing overlapping OpenCV packages were replaced by one
`opencv-contrib-python==4.10.0.84` (code `a4d9452`), retaining imported cv2 4.10.0
with NumPy 1.26.4/MediaPipe 0.10.14. Existing environments with both packages must
uninstall both and reinstall only the pinned contrib package; a simple downgrade
over overlapping packages can leave shared files inconsistent. `pip check` now
passes. New/frozen baselines must respect the changed environment fingerprint.

## HTTP Contract

| Method/path | Result |
|---|---|
| GET `/` | Same-origin local upload/results preview |
| GET `/health` | Service liveness only; does not initialize/test the model |
| GET `/v1/capabilities` | Configured limits and explicitly unsupported review/baseline uploads |
| POST `/v1/analyses` | Synchronous version-1 [squat response](e5-response.md) |

POST requires exactly one file field `video` and explicit text fields `side` and
`facing` (`left` or `right`). Upload hints: `video/mp4`, `video/quicktime` or
`application/octet-stream`. Filenames are not used as filesystem paths. MIME is
a hint only; actual content must decode. Capture reviews, baseline files, model
selection and caller assertions of approval are not accepted at this boundary.
All resulting measurement interpretation therefore remains capture-review gated.

Example from a client environment:

```bash
curl -F "video=@recording.mp4;type=video/mp4" -F "side=left" -F "facing=right" http://127.0.0.1:8000/v1/analyses
```

Defaults: file at most 25 MiB, request at most that plus 64 KiB multipart overhead,
at most 1,800 decoded frames and width/height at most 1920/1080. These are initial
engineering resource bounds, not recording-quality or clinical thresholds. The
ASGI layer counts body bytes even without Content-Length; multipart file/field
counts and field sizes are also bounded. The video is predecoded to inspect
actual frames/dimensions before fresh Full/default inference. No recovery,
experimental calibration, implicit body side, persistent upload or pose cache.
Some corrupted containers may yield a decodable prefix; decoding is not a camera
continuity approval. There is no hard subprocess CPU/decode deadline yet.

One request per process is admitted during parsing/inference; another returns
429 with Retry-After rather than queuing. CPU inference uses the thread pool,
leaving health requests responsive. Keep one worker for this local setup; a
process-local lock is not a distributed admission controller. Each request owns
and closes its model. Application temp files are deleted on success/failure;
multipart files are closed by parser/context management. There is no result DB.

Errors are `{schema_version:1,error:{code,message}}`, with 400 malformed multipart,
413 size/frame/dimension limits, 415 media/body type, 422 invalid selection/file,
429 busy and 500 generic analysis failure. Internal exception/path details are not
returned. Invalid numeric result serialization fails rather than emitting NaN.
Exact error codes are asserted in API tests; some multipart field/count errors
are parser-level 400 rather than field-validation 422.

## Preview Behavior

The browser requires an explicit file, body side and facing; it reads server
limits, previews the local video, uploads once and presents overview/actions,
expandable observations and downloadable JSON. It displays text using textContent,
not HTML from analysis data. Inputs are disabled while a request is active and
changing file/selection invalidates old results. Network/busy/validation failures
are visible. Page reload is not guaranteed to cancel server inference. Browser
downloaded results may be retained by the user even though server uploads are
temporary. Profile/review editing, annotations, timeline UI and mobile remain
future integration; this preview is not a completed consumer UX.

## Verification

Full suite: **435 passed**, 17 existing external-library warnings, 62.30 seconds.
Sixteen new tests cover temp-file cleanup, size and unannounced-body limits,
unknown/invalid/self-approved fields, malformed multipart, generic errors,
admission/health responsiveness, OpenAPI, video preflight/model closure and Node
DOM-mocked UI rendering/selection invalidation. Sandbox TestClient hung on local
event-loop I/O; it was interrupted and tests succeeded outside the sandbox with
approval. UI browser logic is tested; no native-browser visual QA was performed.

An actual local TestClient request for development video 4 returned HTTP 200,
14 left-side detected cycles and capture-review/pending-coaching state; retained
only at ignored `artifacts/api-smoke/video4-response.json`. No external upload or
accuracy claim. Downloaded dependency wheel also remains ignored under artifacts.

Sources: official [FastAPI file handling](https://fastapi.tiangolo.com/tutorial/request-files/),
[worker memory/process behavior](https://fastapi.tiangolo.com/deployment/concepts/),
[OpenCV package selection](https://pypi.org/project/opencv-contrib-python/4.10.0.84/).

## Cycle and Candidate Navigation

Implemented on `feature/biomechanics` (`e735d98`). After analysis, the local preview
lists measured cycles and excluded candidates separately. Selecting a cycle shows
only its measurement cards, availability/reasons/actions and original frame bounds.
Buttons navigate to start, BOTTOM-phase end and end; the BOTTOM-phase end is not
claimed as the deepest posture. Candidate selection shows its gap reason and
start/observed-bottom/end navigation, never measurements borrowed from a cycle.
Empty lists have explicit notices, and changing the selected file/side/facing
invalidates old controls as well as the result.

Navigation pauses the local video and requests `source_frame / reported_fps`.
It is approximate and cannot establish event accuracy, especially for variable-
rate or edited footage. Missing/nonfinite/nonpositive FPS or invalid source-frame
metadata disables time controls while preserving evidence inspection. Not-yet-
loaded video metadata, positions outside browser duration and seek errors produce
visible notices instead of silently seeking/clamping. Native browser seeking is
not frame-exact and has not been visually validated against actual source events.
No automatic playback, candidate promotion or new anatomical claim.

Latest full suite: **444 passed**, 17 existing warnings, 71.58 seconds. Nine new
Node DOM/video-mocked scenarios cover source-frame mapping, selected-cycle
filtering, candidate isolation, invalid/unknown FPS, metadata/duration/index guards,
stale callbacks and empty lists. No API/engine contract or dependency changes.
This is cycle-level navigation within the developer preview, not a complete
landmark overlay/annotation UI, native mobile app or empirical timing validation.

## Paused Selected-Side Joint Overlay

Implemented on `feature/biomechanics`. The local API now explicitly includes the
optional [selected-side coordinate payload](e5-response.md), not a full pose array.
No request-side approval/model controls were added. The browser checkbox defaults
off for each result and enables a canvas overlay only while the local video is
paused and not seeking. Cyan points/segments express observations, not good/bad
posture or injury risk. Six selected-side joints only; a segment requires both
visible endpoints. No inferred joints or frame interpolation.

The display uses floor(currentTime × reported FPS) with a small numeric tolerance
to identify an existing source frame; absent/recovered frames hide the overlay.
Unknown FPS, incompatible selected body side or different native video dimensions
also hide it. Canvas drawing uses original image dimensions and scales to the
displayed video's actual size, refreshing on resize/metadata/seek/pause events.
Playback clears it instead of presenting lagged interpolated poses. New uploads,
selection changes and resubmission clear old overlay data. Native video fullscreen/
picture-in-picture may omit the document-layer canvas.

These are approximate FPS-based associations, not verified frame timestamps or
anatomical correctness. Native-browser visual alignment and filmed accuracy still
need review. Coordinates may be retained in user-downloaded JSON just like other
results; server uploads remain temporary. Analysis values/gates/coaching status
are unchanged. Pipeline fingerprint changes conservatively invalidate earlier
personal baseline contexts.

Latest full suite: **455 passed**, 17 existing warnings, 69.22 seconds; pip check
passes. Eight new coordinate/response tests plus three Node canvas/video-mocked
cases cover selection/filtering, recovery/gaps, missing endpoints, resize,
playback/timing/side/dimension guards and stale results. A real local request for
development video 4 returned 14 cycles, 563 overlay frame entries and 278,550
response bytes with pending coaching; saved only at ignored
`artifacts/api-smoke/video4-overlay-response.json`. No native-browser visual QA,
external video transfer, new dependency or background server.
