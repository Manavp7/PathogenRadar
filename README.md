# PathogenRadar

> A government-grade **disease-intelligence platform**. Phase 1 MVP — **Kerala**.

PathogenRadar takes raw public-health signals and turns them into executive decisions:

```
Raw signals (synthetic + real Google Trends + weather)
  → data quality / confidence scoring
  → feature engineering
  → per-signal anomaly detection
  → fusion engine → district risk score
  → outbreak classification (level + disease category) + explainability
  → deterministic spread forecast (neighbouring districts, 7/14/21/30d)
  → SEIR simulation (projected cases + intervention levers)
  → alerting (Watch…Emergency, with escalation)
  → minister briefing (templated; LLM optional)
  → React dashboard (national / state / district / executive)
```

**The platform runs fully offline with zero external AI dependencies.** Real data
connectors (Google Trends, OpenWeather) and LLM briefing providers (OpenAI, Anthropic,
Gemini, Ollama) are optional plug-ins enabled via configuration.

> Status: **Phase 1 (in development).** See `data/config/regions.yaml` for the Kerala
> definition; adding states is configuration, not re-engineering.

## Quick start

```bash
make install          # create .venv and install backend deps
make seed             # generate synthetic data + run the pipeline once
make demo             # inject the golden dengue outbreak scenario end-to-end
make api              # serve the FastAPI backend at http://localhost:8000
make install-frontend && make dev-frontend   # React dashboard at http://localhost:5173
make test             # run the backend test suite
```

## Architecture

Phase 1 is deliberately **deterministic / statistical / ML** — no LLM is used for
forecasting, risk scoring, alerting, spread prediction, or simulation. Key seams are
behind interfaces so heavier systems can be added without rewrites:

- `Connector` — data sources (synthetic, Google Trends, OpenWeather).
- `KnowledgeGraphRepo` — disease graph (NetworkX now, Neo4j later).
- `LLMProvider` — briefing generation (Template default; cloud/local adapters optional).

## Roadmap

- **Phase 2:** mobility graph, GNN spread prediction, novel-pathogen detection, RL alert optimization.
- **Phase 3:** federated learning, genomic surveillance, multi-state scaling, real government integrations.
