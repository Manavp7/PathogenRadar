# PathogenRadar

PathogenRadar is a foundation for a national disease intelligence operating
system. It is designed around a realistic public-health workflow:

```text
Detect outbreaks → predict spread → recommend interventions → coordinate response → learn from outcomes
```

This repository is intentionally a **demo-grade vertical slice**, not a
production medical device. It uses deterministic synthetic data and baseline
models to prove the platform architecture without claiming real outbreak
prediction capability.

## What is included

- Python/FastAPI backend with public-health intelligence APIs.
- React/Vite dashboard for national, district, executive, and module-roadmap
  views.
- Synthetic India-like district fixtures, signal observations, mobility edges,
  and disease knowledge-graph data.
- Modular layers for acquisition, quality scoring, signal intelligence, fusion,
  outbreak detection, novel-anomaly detection, spread forecasting, simulation,
  decision recommendations, explainability, reports, alerts, security, audit,
  and research mode.
- Automated tests for the backend risk pipeline and API.
- Documentation for product vision, architecture, data contracts, security,
  MLOps, and roadmap.

## What is not included yet

- No live hospital, government, search, social, wastewater, WhatsApp, SMS, ABDM,
  genomic, or WHO/CDC integrations.
- No trained LSTM, transformer, GNN, autoencoder, PPO, A3C, DQN, or LLM models.
- No PII ingestion or storage.
- No production authentication, authorization, encryption, deployment, or
  compliance certification.

The backend exposes stable interfaces where those systems can be added later.

## Repository layout

```text
apps/api     FastAPI backend and tests
apps/web     React/Vite dashboard prototype
docs         Product, architecture, data, security, MLOps, roadmap docs
```

## Quick start

### Backend

```bash
cd apps/api
python3 -m venv .venv
. .venv/bin/activate
pip install -e ".[dev]"
pytest
uvicorn pathogenradar_api.main:app --reload
```

Open:

- API docs: <http://127.0.0.1:8000/docs>
- Health: <http://127.0.0.1:8000/health>
- Demo district intelligence:
  <http://127.0.0.1:8000/intelligence/district/kerala-ernakulam>

### Dashboard

```bash
cd apps/web
npm install
npm run build
npm run dev
```

The dashboard defaults to `http://127.0.0.1:8000` for API calls and falls back
to bundled demo data if the API is unavailable.

### One-command checks

```bash
make test
```

## Platform modules

The long-term platform is modeled as 19 products inside one system:

1. Data Acquisition Layer
2. Data Quality Engine
3. Disease Knowledge Graph
4. Signal Intelligence Layer
5. Multimodal Fusion Transformer
6. Outbreak Detection Engine
7. Novel Pathogen Detector
8. Spread Forecast Engine
9. Epidemiological Simulator
10. RL Decision Engine
11. Explainability Engine
12. LLM Intelligence Layer
13. Dashboard
14. Alerting System
15. Public API
16. Mobile App
17. Security Layer
18. MLOps Layer
19. Research Mode

See `docs/MODULE_ROADMAP.md` for the MVP, state-ready, national-grade, and
future-version roadmap.

## Safety note

PathogenRadar outputs in this repository are synthetic decision-support
demonstrations. They must not be used for clinical diagnosis, individual
medical decisions, or emergency public-health action without validated data,
qualified epidemiological review, governance, and regulatory approval.