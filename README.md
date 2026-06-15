# PathogenRadar

> A government-grade **disease-intelligence platform**. Phase 1 MVP — **Kerala**.

PathogenRadar turns raw public-health signals into executive decisions — detecting outbreaks,
forecasting spread, simulating interventions, and briefing decision-makers, all from a single
operating picture.

![Overview](docs/img/overview.png)

**The platform runs fully offline with zero external AI dependencies.** Forecasting, risk
scoring, alerting, spread prediction and simulation use deterministic / statistical / ML
models — never an LLM. Optional plug-ins (real Google Trends + OpenWeather data, and LLM
briefing providers) can be enabled via configuration but are never required.

---

## The pipeline (raw signals → executive decision)

```
Acquire signals (synthetic + real Google Trends + weather)
  → data-quality scoring + per-source reliability + confidence
  → feature engineering (reliability-weighted multi-source fusion)
  → per-signal anomaly detection (search / hospital / social / wastewater)
  → fusion engine → unified district risk score
  → outbreak classification (level + disease category) + explainability
  → deterministic spread forecast across districts (7 / 14 / 21 / 30 days)
  → SEIR simulation (projected cases + intervention levers)
  → alerting (Watch…Emergency, escalation, multi-channel)
  → minister briefing (templated; LLM optional)
  → React dashboard (Overview / Kerala / District / Executive)
```

Run `make demo` for a narrated end-to-end walkthrough of a dengue outbreak in Ernakulam.

---

## Quick start

```bash
make install            # create .venv and install backend deps
make seed               # generate data + run the pipeline (flagship dengue scenario)
make api                # FastAPI backend at http://localhost:8000  (Swagger at /docs)

make install-frontend   # install dashboard deps
make dev-frontend       # React dashboard at http://localhost:5173

make demo               # narrated end-to-end pipeline walkthrough in the terminal
make test               # backend test suite (45 tests)
```

Or with Docker: `make up` (builds backend + frontend behind nginx).

The platform needs **no API keys**. To enable optional real data / LLM, copy `.env.example`
to `.env` and fill in what you have.

---

## Screens

| District intelligence | Executive situation report |
| --- | --- |
| ![District](docs/img/district.png) | ![Executive](docs/img/executive.png) |

The District view shows the risk trajectory, the explainable contribution breakdown
("Fever searches +163%, PCR requests +189%…"), the per-district spread forecast, a live
**SEIR intervention simulator**, and the raw signal breakdown. The Executive view delivers a
situation report, 30-day spread outlook, prioritised actions, and a downloadable minister
briefing.

---

## Architecture

Everything is **district-aware and data-source agnostic** — adding a state is a change to
`data/config/regions.yaml` plus a GeoJSON, not a re-engineering effort. Key seams sit behind
interfaces so heavier systems drop in without rewrites:

| Interface | Today | Swappable to |
| --- | --- | --- |
| `Connector` (acquisition) | Synthetic + Google Trends + OpenWeather | Hospital / ABDM / lab feeds |
| `KnowledgeGraphRepo` | NetworkX | Neo4j |
| `BriefingProvider` (LLM) | Template (offline) | OpenAI / Anthropic / Gemini / Ollama |

```
backend/pathogenradar/
  acquisition/   M1  connectors (synthetic, google_trends, weather) + orchestration
  quality/       M2  missing/outlier/drift detectors, source reliability, confidence
  knowledge/     M3  disease knowledge graph (interface + NetworkX)
  features/          reliability-weighted multi-source aggregation
  signals/       M4  anomaly detectors (search STL+z, hospital IsolationForest, social, wastewater)
  fusion/        M5  detector fusion → risk score
  detection/     M6  level + disease-category classification
  explain/       M11 contribution breakdown
  forecast/      M8  deterministic gravity-graph spread forecast
  simulation/    M9  SEIR + intervention levers
  alerting/      M14 escalation + recommended actions + channels
  llm/           M12 briefing provider abstraction (offline by default)
  security/      M17 API-key auth + audit log (basic)
  api/           M15 FastAPI
  pipeline.py        end-to-end orchestration ("the tick")
frontend/        M13 React + Vite + TS dashboard (SVG choropleth, Recharts)
```

### How the vision's modules map to this MVP

| Vision module | Status in Phase 1 |
| --- | --- |
| M1 Data Acquisition | ✅ synthetic + real Google Trends + weather (pluggable) |
| M2 Data Quality | ✅ missing/outlier/drift + reliability + confidence |
| M3 Knowledge Graph | ✅ NetworkX (Neo4j-swappable interface) |
| M4 Signal Intelligence | ✅ per-source anomaly detectors |
| M5 Fusion | ✅ reliability-weighted deterministic fusion |
| M6 Outbreak Detection | ✅ level + category classification |
| M8 Spread Forecast | ✅ deterministic graph diffusion (GNN = Phase 2) |
| M9 Simulator | ✅ SEIR + interventions |
| M11 Explainability | ✅ contribution breakdown |
| M12 LLM Layer | ✅ briefings (offline template default; providers optional) |
| M13 Dashboard | ✅ four product-grade views |
| M14 Alerting | ✅ rules + escalation + channels |
| M15 API | ✅ FastAPI |
| M17 Security | ◑ basic API-key + audit (full RBAC/HIPAA later) |
| M7 Novel pathogen, M10 RL, M16 Mobile, M18 MLOps, M19 Research | ◻ roadmap |

---

## Configuration (all optional)

| Variable | Effect |
| --- | --- |
| `PATHOGENRADAR_REGION` | Region key in `regions.yaml` (default `kerala`) |
| `ENABLE_GOOGLE_TRENDS` | Pull real Google Trends (pytrends); falls back to synthetic |
| `OPENWEATHER_API_KEY` | Enable real OpenWeather data; otherwise synthetic weather |
| `LLM_PROVIDER` | `template` (default) / `openai` / `anthropic` / `gemini` / `ollama` |
| `*_API_KEY` | Keys for the chosen LLM provider (never required) |
| `PATHOGENRADAR_API_KEY` | If set, the API requires an `X-API-Key` header |

---

## Roadmap

- **Phase 2:** mobility graph + GNN spread prediction, novel-pathogen detection (autoencoders),
  RL alert optimization.
- **Phase 3:** federated learning, genomic surveillance, multi-state scaling, real
  government / hospital / ABDM integrations, full RBAC / HIPAA, production MLOps.

The real moat is not the models — it is the historical outbreak dataset, the hospital and
government integrations, and years of learned outbreak behaviour. This platform is the spine
those assets plug into.
