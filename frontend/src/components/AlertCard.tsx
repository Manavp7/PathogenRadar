import type { Alert } from "../api/types";
import { LEVEL_COLORS, shortDate } from "../lib/format";
import { Badge } from "./common";

export default function AlertCard({ alert, compact }: { alert: Alert; compact?: boolean }) {
  return (
    <div className="alert-card" style={{ borderLeftColor: LEVEL_COLORS[alert.level] }}>
      <div className="head">
        <span className="headline">{alert.headline}</span>
        <Badge level={alert.level} />
      </div>
      <div className="faint" style={{ fontSize: 12 }}>
        {alert.district_name} · {shortDate(alert.date)} · risk {alert.risk_score.toFixed(0)}/100
      </div>
      {!compact && (
        <>
          {alert.reasons.length > 0 && (
            <ul>
              {alert.reasons.slice(0, 4).map((r, i) => (
                <li key={i}>{r}</li>
              ))}
            </ul>
          )}
          <div className="channels">
            {alert.channels.map((c) => (
              <span className="chip" key={c}>
                {c}
              </span>
            ))}
          </div>
        </>
      )}
    </div>
  );
}
