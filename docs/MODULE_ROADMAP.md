# Module roadmap

This roadmap maps the full company-grade vision to what is implemented in this
repository and what remains for later maturity stages.

| # | Module | Demo foundation | Serious MVP | State-ready | National-grade |
| --- | --- | --- | --- | --- | --- |
| 1 | Data Acquisition | Synthetic connectors | 2-3 real pilots | Hospital/government feeds | Nationwide integrations |
| 2 | Data Quality | Deterministic scoring | Source SLAs | Drift and integrity monitoring | Automated trust learning |
| 3 | Disease Knowledge Graph | JSON graph | Managed graph schema | Neo4j deployment | National disease ontology |
| 4 | Signal Intelligence | Baseline encoders | Source-specific models | Retrained detectors | Ensemble model governance |
| 5 | Multimodal Fusion | Weighted fusion | Learned calibration | Fusion transformer pilot | Production multimodal model |
| 6 | Outbreak Detection | Threshold classifier | Calibrated alerts | Validated alert policy | Audited national alerting |
| 7 | Novel Pathogen | Novelty placeholder | Unsupervised baseline | Contrastive/anomaly models | Genomic-aware anomaly ops |
| 8 | Spread Forecast | Mobility graph propagation | Better mobility data | GNN/GAT pilots | National forecast service |
| 9 | Simulator | Simple SEIR | Scenario library | Calibrated district models | Agent-based simulations |
| 10 | RL Decision | Rule policy class | Offline policy evaluation | Human-in-loop RL | Governed optimization |
| 11 | Explainability | Source drivers | SHAP/attention pilots | Regulator-ready explanations | Continuous audit evidence |
| 12 | LLM Intelligence | Template reports | RAG over bulletins | Approved briefing workflows | Multilingual intelligence |
| 13 | Dashboard | React prototype | Pilot ops dashboard | State command center | National command platform |
| 14 | Alerts | JSON payloads | Email/API channels | SMS/WhatsApp/mobile | Escalation operations |
| 15 | Public API | Demo endpoints | Authenticated pilot API | Partner APIs | Scaled external platform |
| 16 | Mobile App | Mobile-ready design only | Officer PWA | Offline workflows | Field operations network |
| 17 | Security | RBAC/API-key scaffold | SSO and encryption | Audit/compliance controls | HIPAA-like/ABDM governance |
| 18 | MLOps | Docs and tests | MLflow/Feast pilots | Drift/retraining | Full model lifecycle |
| 19 | Research Mode | Safe demo queries | Historical analyses | Epidemiologist workbench | Research data product |

## Future versions

### PathogenRadar 2.0 — Genomic surveillance

- Variant tracking.
- Mutation monitoring.
- Resistance markers.
- Wastewater and sequencing integration.

### PathogenRadar 3.0 — Global disease intelligence

- WHO, CDC, global news, flights, climate, and research-paper ingestion.
- Forecasting which global outbreaks may enter India next.

## Current implementation status

The current repository implements the contracts and demo behavior for all 19
modules, but production-grade data integrations, learned models, policy
optimization, compliance controls, and operational alerting are intentionally
deferred.
