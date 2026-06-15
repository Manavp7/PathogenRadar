import type { Alert } from "../types";

export function AlertPanel({ alert }: { alert: Alert | null }) {
  return (
    <section className="panel alert-panel">
      <div className="panel-heading">
        <span>Alerting system</span>
        <small>Escalation-ready payload</small>
      </div>
      {alert ? (
        <div className={`alert-banner level-${alert.level}`}>
          <strong>{alert.title}</strong>
          <p>{alert.message}</p>
          <small>Channels: API ready now; SMS, WhatsApp, Email, Mobile App are roadmap integrations.</small>
        </div>
      ) : (
        <p>No alert is active for this district. Continue routine monitoring.</p>
      )}
    </section>
  );
}
