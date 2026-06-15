# MLOps and research mode

Production PathogenRadar depends on continuously improving models, reliable
features, and a research environment for epidemiologists.

## Future MLOps platform

### Feature store

- Store validated district-time features.
- Preserve source reliability and lineage.
- Support offline training and online inference parity.
- Candidate tool: Feast.

### Model registry

- Register detector, fusion, forecast, simulator-calibration, and decision
  policy versions.
- Track approval status and deployment scope.
- Candidate tool: MLflow.

### Experiment tracking

- Track datasets, feature versions, hyperparameters, metrics, and validation
  cohorts.
- Compare models by disease category and geography.

### Monitoring

- Data drift.
- Concept drift.
- Missing data and source outages.
- Calibration drift.
- False alarms and missed detections.
- Intervention outcome impact.

### Retraining

- Scheduled retraining for stable sources.
- Event-triggered retraining after major outbreaks.
- Human approval before policy-affecting deployment.
- Rollback strategy for degraded models.

## Research mode

Research mode should let epidemiologists:

- Query historical outbreaks and synthetic/demo scenarios.
- Run custom simulations.
- Compare forecasts.
- Study source reliability over time.
- Export governed aggregate datasets.

The demo implementation provides safe predefined queries only. It does not
allow arbitrary database access or unreviewed data export.

## Research safeguards

- Use aggregate/de-identified data.
- Require project approvals for sensitive analyses.
- Track exports in audit logs.
- Separate exploratory notebooks from production model deployment.
- Version every dataset used for research claims.
