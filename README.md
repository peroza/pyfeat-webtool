# pyfeat-webtool

Web UI and API for running [Py-FEAT](https://py-feat.org/) face analysis on still images: emotions, action units (AUs), landmarks, and an overlay visualization. Jobs are ephemeral (in-memory, TTL); there is no auth or saved history.

Design spec: [docs/superpowers/specs/2026-09-18-pyfeat-web-interface-design.md](docs/superpowers/specs/2026-09-18-pyfeat-web-interface-design.md)

## Architecture

```
Browser
   │
   ▼
Next.js (apps/web) ──HTTP──► FastAPI (apps/api)
                                  ├─ in-memory job store (TTL)
                                  ├─ worker thread pool
                                  └─ Py-FEAT Detector (or stub)
```

| Piece | Role |
|-------|------|
| `apps/web` | Upload UI, poll `/v1/jobs/{id}`, render results |
| `apps/api` | `POST /v1/analyze`, validate image, run analysis, return JSON |

The browser talks to the API from the client using `NEXT_PUBLIC_API_URL`. CORS is configured on the API via `PYFEAT_CORS_ORIGINS`.

## Run with Docker Compose

From the repo root:

```bash
docker compose up --build
```

- Web: http://localhost:3000  
- API: http://localhost:8000  

The web image is built with `NEXT_PUBLIC_API_URL=http://localhost:8000` so the browser can reach the API on your machine.

For UI-only work without downloading Py-FEAT models, uncomment `PYFEAT_USE_STUB_ANALYZER: "true"` under the `api` service in `docker-compose.yml`.

**First run (real analyzer):** the API container downloads Py-FEAT weights on startup. Expect several minutes and a working network connection. Use stub mode if you only need the UI.

## Local development (stub + dev server)

**API (stub, no models):**

```bash
cd apps/api
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
PYFEAT_USE_STUB_ANALYZER=true uvicorn app.main:create_app --factory --reload --host 0.0.0.0 --port 8000
```

**Web:**

```bash
cd apps/web
npm ci
NEXT_PUBLIC_API_URL=http://localhost:8000 npm run dev
```

Open http://localhost:3000 and upload a JPEG, PNG, or WebP (max 10 MB).

See [apps/api/README.md](apps/api/README.md) for real Py-FEAT mode, tests, and macOS OpenMP notes.

## Environment variables

### API (`PYFEAT_` prefix)

| Variable | Default | Description |
|----------|---------|-------------|
| `PYFEAT_USE_STUB_ANALYZER` | `false` | Deterministic stub instead of Py-FEAT |
| `PYFEAT_MAX_UPLOAD_BYTES` | `10485760` | Max upload size (10 MiB) |
| `PYFEAT_JOB_TTL_SECONDS` | `1200` | Job retention in memory (20 min) |
| `PYFEAT_WORKER_POOL_SIZE` | `1` | Analysis thread pool size |
| `PYFEAT_CORS_ORIGINS` | `http://localhost:3000` | Comma-separated allowed origins |

### Web

| Variable | When | Description |
|----------|------|-------------|
| `NEXT_PUBLIC_API_URL` | Build (Docker) or dev | Base URL for API calls from the browser (e.g. `http://localhost:8000`) |

Copy [apps/web/.env.local.example](apps/web/.env.local.example) to `.env.local` for local dev.

## Scale-up path (same API contract)

| Concern | v1 | Later |
|---------|----|-------|
| Job store | In-memory + TTL | Redis |
| Execution | In-process pool | Celery / RQ / Arq workers |
| Overlay | Base64 in JSON | Object storage + signed URLs |
| Media | Image only | `job_type: image \| video` (py-feat `data_type="video"`) |
| Topology | Single API container | API replicas + worker pools |

Video upload and frame UI are documented as future work only; v1 is still images.

## Repository layout

```
apps/web/          Next.js + Tailwind + shadcn/ui
apps/api/          FastAPI + Py-FEAT adapter
docker-compose.yml Optional full stack
docs/superpowers/  Specs and implementation plans
```
