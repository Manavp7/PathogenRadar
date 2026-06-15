# Security and privacy

PathogenRadar must be designed for sensitive public-health operations. This
repository includes only a lightweight scaffold; production deployments require
formal security architecture, legal review, penetration testing, and compliance
programs.

## Principles

- Collect the minimum data required for public-health intelligence.
- Prefer aggregated district-level signals over individual records.
- Avoid PII in analytics and model-training paths unless a governed use case
  requires it.
- Separate identity, authorization, audit, and analytics concerns.
- Make every alert and data access auditable.

## Access control

The demo API includes role names for future RBAC:

- `national_admin`
- `state_officer`
- `district_officer`
- `researcher`
- `public_consumer`

Production RBAC should enforce:

- Jurisdiction boundaries.
- Purpose-based access.
- Least privilege.
- Break-glass workflows.
- Periodic access review.

## Audit logs

Audit events should capture:

- Actor and role.
- Action and endpoint.
- District/state scope.
- Timestamp.
- Decision/report/alert identifiers.
- Data export events.

## PII protection

Future real integrations should include:

- Tokenization or pseudonymization before analytics.
- Encryption in transit and at rest.
- Separate key management.
- Retention and deletion policies.
- Data sharing agreements.
- Differential privacy or aggregation where appropriate.

## ABDM and healthcare integration considerations

For India healthcare integrations, production design should account for:

- ABDM consent and data exchange requirements.
- Hospital onboarding and source reliability contracts.
- Clinical coding standards.
- Strict boundaries between public-health intelligence and clinical care.

## Demo limitations

The current repository:

- Uses synthetic non-PII fixtures only.
- Allows local demo access without a secret by default.
- Does not implement production SSO, encryption, or compliance controls.
