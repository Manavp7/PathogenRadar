# PathogenRadar API

FastAPI backend for the PathogenRadar demo foundation.

## Run locally

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -e ".[dev]"
pytest
uvicorn pathogenradar_api.main:app --reload
```

## Useful endpoints

- `GET /health`
- `GET /districts`
- `GET /intelligence/national`
- `GET /intelligence/district/kerala-ernakulam`
- `GET /forecasts/district/kerala-ernakulam`
- `POST /simulations/district/kerala-ernakulam`
- `GET /reports/executive`
- `GET /alerts`
- `POST /research/query`

All outputs are generated from deterministic synthetic fixtures.
