# Data contracts

All contracts are represented as Pydantic models in the backend and mirrored by
TypeScript interfaces in the dashboard.

## District

- `id`: stable slug.
- `name`: display name.
- `state`: Indian state/territory.
- `population`: total population used for demo rates.
- `latitude`, `longitude`: display coordinates.

## Signal observation

- `id`: stable observation id.
- `district_id`: linked district.
- `source`: hospital, search, social, weather, environmental, mobility, or
  wastewater.
- `timestamp`: ISO timestamp.
- `metric`: source-specific metric name.
- `value`: current value.
- `baseline`: expected baseline.
- `unit`: measurement unit.
- `metadata`: non-PII contextual fields such as symptoms or keywords.

## Source quality score

- `source`: signal source.
- `completeness`: missing-data score.
- `outlier_score`: confidence after outlier checks.
- `drift_score`: confidence after drift checks.
- `integrity_score`: schema/range consistency.
- `freshness_score`: recency score.
- `reliability`: aggregate reliability percentage.
- `issues`: human-readable caveats.

## Disease state

- `district`: district.
- `state_vector`: unified numeric disease-state vector.
- `source_contributions`: normalized contribution by signal source.
- `dominant_symptoms`: extracted symptom hints.
- `context`: weather/environment/mobility context.
- `confidence`: aggregate confidence from quality scoring.

## Risk assessment

- `district`: district.
- `risk_score`: 0-100 score.
- `alert_level`: normal, watch, warning, alert, or emergency.
- `category`: respiratory, vector, waterborne, foodborne, or unknown.
- `confidence`: data/model confidence.
- `novelty_score`: unknown-pattern score.
- `is_novel_anomaly`: true when high-risk signals do not match known patterns.

## Forecast

- `origin_district_id`: source district.
- `points`: 7, 14, 21, and 30 day horizons.
- Each point includes per-district spread probability and confidence.

## Simulation scenario

- `horizon_days`: scenario duration.
- `interventions`: school closure, masking, vaccination, travel restriction,
  vector control, or water sanitation.
- `compliance`: 0-1 expected compliance.

## Alert

- `id`: stable alert id.
- `district`: affected district.
- `level`: alert level.
- `title`: summary.
- `message`: operational text.
- `reasons`: explainability factors.
- `recommended_actions`: actions from the decision layer.
- `channels`: SMS, WhatsApp, Email, API, Mobile App readiness metadata.

## Report

- `title`: briefing title.
- `audience`: target reader.
- `summary`: situation summary.
- `risk_assessment`: referenced assessment.
- `key_drivers`: explanation factors.
- `recommended_actions`: recommended actions.
- `limitations`: caveats about demo data, uncertainty, and validation.
