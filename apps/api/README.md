# Py-FEAT Analysis API

FastAPI service that runs face analysis jobs (emotions, action units, landmarks) via py-feat.

## Analyzer modes

| Mode | When | Behavior |
|------|------|----------|
| Stub | `PYFEAT_USE_STUB_ANALYZER=true` | Deterministic fake output; no models |
| Py-FEAT | default (`false`) | Loads py-feat at startup and runs real inference |

## Default detector (non-stub)

When stub mode is off, the app constructs **`Detectorv2`** (imported as `Detector` when the legacy `feat.Detector` alias is unavailable — py-feat ≥ 2.x).

Typical defaults for `Detectorv2`:

- **Face detection:** RetinaFace (`retinaface`)
- **Multitask model:** `face_multitask_v2` (AU, emotion, gaze, pose, 478-point mesh)
- **Identity:** ArcFace embeddings (`identity_model='arcface'`)
- **Device:** CPU unless you pass `device='cuda'` / `'mps'` when constructing the detector in code

Scores (emotions, AUs, etc.) are passed through as **library-native** values from py-feat; they are not re-normalized by this API.

### First run / model download

The first time you start with the real analyzer, py-feat downloads pretrained weights (Hugging Face / bundled URLs). This can take several minutes and requires network access. Subsequent starts reuse cached weights under your user cache (see py-feat docs).

**macOS note:** py-feat depends on XGBoost, which may require OpenMP (`brew install libomp`) if import fails.

## Environment variables

All settings use the `PYFEAT_` prefix:

| Variable | Default | Description |
|----------|---------|-------------|
| `PYFEAT_USE_STUB_ANALYZER` | `false` | Use `StubAnalyzer` instead of py-feat |
| `PYFEAT_MAX_UPLOAD_BYTES` | `10485760` (10 MiB) | Max uploaded image size |
| `PYFEAT_JOB_TTL_SECONDS` | `1200` (20 min) | In-memory job TTL |
| `PYFEAT_WORKER_POOL_SIZE` | `1` | Thread pool size for analysis workers |
| `PYFEAT_CORS_ORIGINS` | `http://localhost:3000` | Comma-separated CORS origins |

Unit tests set `PYFEAT_USE_STUB_ANALYZER=true` so CI never loads models.

## Video (future)

The job API currently accepts **images** only. py-feat’s `Detector.detect(..., data_type="video")` is the intended extension point for a future `job_type=video` that streams frames through the same `PyFeatAnalyzer` mapping.

## Development

```bash
cd apps/api
source .venv/bin/activate
uvicorn app.main:create_app --factory --reload
pytest tests/ -v
```

Adapter unit tests mock the detector; they do not download models or run inference.
