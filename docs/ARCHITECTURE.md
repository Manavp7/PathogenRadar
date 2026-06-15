# Architecture

PathogenRadar is structured as layered disease intelligence infrastructure.
This repository implements a deterministic demo vertical slice where every
layer has a real interface and synthetic inputs.

## End-to-end intelligence loop

```mermaid
flowchart LR
  A[Data acquisition] --> B[Data quality]
  B --> C[Signal intelligence]
  C --> D[Multimodal fusion]
  D --> E[Outbreak detection]
  E --> F[Spread forecast]
  E --> G[Epidemiological simulation]
  F --> H[Decision policy]
  G --> H
  H --> I[Explainability]
  I --> J[Reports and alerts]
  J --> K[Dashboard and API]
  K --> L[Response outcomes]
  L -. future learning .-> B
  L -. future learning .-> H
```

## Backend dependency graph

```mermaid
flowchart TD
  Repo[DemoRepository] --> Acquisition
  Acquisition --> Quality
  Quality --> SignalIntel[Signal intelligence]
  SignalIntel --> Fusion
  Repo --> KnowledgeGraph[Knowledge graph]
  Fusion --> Detection
  KnowledgeGraph --> Detection
  Detection --> Novel[Novel anomaly detector]
  Detection --> Forecast
  Detection --> Simulation
  Forecast --> Decision
  Simulation --> Decision
  SignalIntel --> Explain
  Quality --> Explain
  Detection --> Explain
  Decision --> Reports
  Explain --> Reports
  Decision --> Alerts
  Reports --> Routes[FastAPI routes]
  Alerts --> Routes
```

## Dashboard and API relationship

```mermaid
flowchart LR
  Dashboard[React dashboard] -->|HTTP JSON| API[FastAPI API]
  API --> Pipeline[Intelligence pipeline]
  Pipeline --> Fixtures[Synthetic fixtures]
  Dashboard -. fallback .-> Demo[Bundled demo state]
```

## Runtime modules

- **Data acquisition:** connector interfaces and synthetic connectors.
- **Data quality:** missing data, outlier, drift, integrity, and reliability
  scoring.
- **Signal intelligence:** deterministic source-specific encoders.
- **Knowledge graph:** fixture-backed disease/symptom/vector/weather graph.
- **Fusion:** weighted multimodal disease-state calculation.
- **Detection:** alert level and disease-category classification.
- **Novel anomaly:** deterministic novelty flag for unknown high-risk patterns.
- **Forecast:** graph propagation over district mobility edges.
- **Simulation:** simple deterministic SEIR-style intervention comparison.
- **Decision:** rule-based placeholder for a future RL policy.
- **Explainability:** top source drivers and caveats.
- **LLM intelligence:** report generation only; no prediction logic.
- **Alerts:** escalation payloads and channel readiness metadata.
- **Security/audit:** demo API-key and audit scaffolding.
- **Research mode:** safe predefined demo queries.

## Production extension points

- Replace demo connectors with hospital, ABDM, search, social, environmental,
  mobility, and wastewater integrations.
- Replace fixture knowledge graph with Neo4j.
- Replace baseline detectors with trained temporal, transformer, and anomaly
  models.
- Replace rule policy with governed RL optimization after outcome data exists.
- Add feature store, model registry, drift monitoring, and retraining pipelines.
