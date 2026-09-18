# Py-FEAT Web Interface — Design Spec

**Date:** 2026-09-18  
**Status:** Draft for review  
**Repo:** `pyfeat-webtool` (greenfield)

## Goal

Build a simple web UI that wraps [Py-FEAT](https://py-feat.org/) so a user can upload a face image and receive emotions, Action Units (AUs), landmarks, and a visualization overlay. Start simple (local, ephemeral, single-user friendly) while keeping a job-shaped API so the system can grow to concurrent workers and video without rewriting the UI contract.

## Non-goals (v1)

- User accounts, auth, or server-side analysis history
- Video upload or frame-by-frame analysis UI
- Multi-face detailed reporting (beyond noting face count and analyzing the primary face)
- Real-time webcam streaming
- Production queue/Redis/object storage on day one

## Decisions locked in

| Topic | Choice |
|-------|--------|
| Analysis source | Fresh integration against Py-FEAT `Detector` API |
| Outputs | Emotions + AUs + landmarks + overlay image |
| Inputs | Still images only; documented extension point for video |
| Persistence | Ephemeral (in-memory jobs + short TTL) |
| Architecture style | Next.js UI + FastAPI analysis API with async job contract |
| UI stack | Next.js App Router, Tailwind CSS, shadcn/ui |

## Architecture

### Monorepo layout

```
apps/web/          # Next.js + Tailwind + shadcn/ui
apps/api/          # FastAPI + Py-FEAT
docker-compose.yml # web + api (optional redis/worker profiles later)
docs/superpowers/  # specs and plans
```

Optional later: OpenAPI-generated TypeScript client for the web app. v1 may use hand-written types mirrored from the API schema to keep setup light.

### Runtime (v1)

```
Browser → Next.js (apps/web) → HTTP → FastAPI (apps/api)
                                         ├─ in-memory job store
                                         ├─ process/thread pool
                                         └─ Py-FEAT Detector (loaded once at startup)
```

- The Next.js app does **not** run Py-FEAT or perform inference.
- FastAPI validates uploads, owns job lifecycle, runs detection, and returns structured results.
- Results live only in the API process memory until TTL expiry or process restart.

### Scale path (same contract)

| Concern | v1 | Later (no UI rewrite) |
|---------|----|------------------------|
| Job store | In-memory dict + TTL | Redis |
| Execution | In-process pool | Celery / RQ / Arq workers |
| Overlay delivery | Base64 in JSON | Object storage + short-lived URL |
| Media types | `image` only | `job_type: image \| video` |
| API topology | Single FastAPI container | API replicas + dedicated worker pools |

## API contract

Base path: `/v1`

### `POST /v1/analyze`

- **Content-Type:** `multipart/form-data`
- **Field:** `image` (required) — JPEG, PNG, or WebP
- **Limits:** max 10 MB; must decode as an RGB image
- **Behavior:** create job (`queued`), schedule processing, return immediately
- **Response `202`:**

```json
{ "job_id": "uuid" }
```

### `GET /v1/jobs/{job_id}`

- **Response `200`:**

```json
{
  "job_id": "uuid",
  "status": "queued | running | succeeded | failed",
  "error": null,
  "result": null
}
```

On success, `result` is populated:

```json
{
  "face_count": 1,
  "emotions": {
    "anger": 0.01,
    "disgust": 0.0,
    "fear": 0.02,
    "happiness": 0.85,
    "sadness": 0.03,
    "surprise": 0.04,
    "neutral": 0.05
  },
  "action_units": {
    "AU01": 0.12,
    "AU12": 0.91
  },
  "landmarks": [[x, y]],
  "overlay_image_base64": "<png base64 without data-URL prefix>"
}
```

Exact emotion and AU key sets follow the configured Py-FEAT detector. The API normalizes keys to strings and values to floats, passing through library-native scores (no rescaling). The API README documents the detector config and what those scores mean (e.g. emotion probabilities vs AU intensities).

On failure:

```json
{
  "job_id": "uuid",
  "status": "failed",
  "error": {
    "code": "no_face | invalid_image | timeout | internal",
    "message": "Human-readable, safe message"
  },
  "result": null
}
```

Unknown `job_id` → `404`.

### Job lifecycle

1. `POST /analyze` → create job, status `queued`
2. Worker picks job → `running`
3. Success → `succeeded` + `result`; failure → `failed` + `error`
4. TTL (default **20 minutes**) removes job from memory

### Multi-face policy (v1)

- Detect all faces; set `face_count`
- Analyze **primary face** = largest bounding box
- Overlay draws the primary face (landmarks at minimum)
- UI may show a note when `face_count > 1`

### Video extension point (not implemented in v1)

Future request field or endpoint variant, e.g. `media_type: "video"` and/or `POST /v1/analyze-video`, reusing the same `GET /v1/jobs/{id}` polling model. Job result shape would add frame-level arrays; the UI would add a separate media picker later.

## Py-FEAT integration

- Instantiate `Detector` **once** at API startup (models are heavy).
- Document default model configuration in `apps/api` README so runs are reproducible.
- Processing steps per job:
  1. Decode and validate image bytes
  2. Run detection
  3. If zero faces → fail with `no_face`
  4. Select primary face; extract emotions, AUs, landmarks
  5. Render overlay PNG with landmarks on the primary face (required); AU/emotion text labels are optional polish, not required for v1
  6. Persist structured result on the job record
- Inference runs in a bounded executor so the FastAPI event loop is not blocked.
- Concurrency for v1: small pool (e.g. 1–2 workers) — Py-FEAT/GPU/CPU contention is expected; horizontal scale comes later via real workers.

## Web UI

### Screen

One primary composition (not a multi-panel dashboard):

1. **Upload** — drag-and-drop / file picker; image preview; Analyze CTA
2. **In progress** — status from polling (`queued` → `running`) with progress/skeleton
3. **Results** — four sections:
   - Emotions (ranked list or bars)
   - Action Units (table or bars)
   - Landmarks (summary + optional detail)
   - Overlay image from API
4. **Reset** — clears client state only

### Component guidance

- Tailwind + shadcn/ui: `Button`, `Progress`/skeletons, `Alert`, minimal `Card` only where it wraps interaction
- Avoid dashboard clutter: no stats strips, no secondary marketing chrome
- Explicit client states: `idle` | `ready` | `submitting` | `polling` | `succeeded` | `failed`

### Polling

- Poll `GET /v1/jobs/{id}` with modest backoff (e.g. 500ms → 1s → 2s, cap ~2s)
- Client hard timeout ~2 minutes → show retry
- Stop polling on `succeeded` or `failed`

## Error handling

| Layer | Behavior |
|-------|----------|
| Upload validation (web) | Block non-image / oversized files before submit |
| API validation | `400` with safe message |
| Inference | Job `failed` with typed `error.code` |
| Logging | Full detail server-side only |
| UI | `Alert` / inline error; no stack traces |

## Local development

- `docker compose up` runs `web` and `api`
- Env:
  - `NEXT_PUBLIC_API_URL` — browser-facing API base URL
  - API: model cache directory, max upload size, job TTL, worker pool size
- First API start may download Py-FEAT models; document that in README

## Testing strategy

- **API unit tests:** request validation, job state transitions, result serialization with a mocked Detector
- **API smoke:** optional integration test with a fixture face image; CI may mock Detector to avoid model downloads
- **Web:** component tests for upload and result state machine
- **E2E:** optional Playwright happy path after core flows work

## Success criteria

1. User can upload a clear face photo and see emotions, AUs, landmarks, and overlay without using a notebook.
2. Job API works end-to-end with ephemeral storage.
3. Failed cases (no face, bad file) show clear UI errors.
4. README documents run instructions and the scale-up path (Redis/workers/video).
5. Architecture keeps ML isolated in `apps/api` and UI in `apps/web`.

## Open implementation notes (resolved preferences)

- Overlay encoding: **base64 PNG in JSON** for v1 (ephemeral, no storage service).
- Auth: **none** in v1.
- Primary face: **largest bbox**.
- Job TTL: **20 minutes** default, configurable.
