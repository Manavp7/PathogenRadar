import { useEffect, useState } from "react";
import { api } from "../api/client";
import type { SystemStatus as Status } from "../api/types";

export default function SystemStatus() {
  const [s, setS] = useState<Status | null>(null);
  useEffect(() => {
    api.system().then(setS).catch(() => setS(null));
  }, []);
  if (!s) return null;

  return (
    <div className="panel">
      <h3>Platform Status</h3>
      <div className="contrib">
        <span className="name">Mode</span>
        <span className="val">
          <span className="chip">{s.offline_mode ? "offline" : "connected"}</span>
        </span>
      </div>
      <div className="contrib">
        <span className="name">Data connectors</span>
        <span className="pill-row" style={{ justifyContent: "flex-end" }}>
          {Object.entries(s.connectors).map(([id, c]) => (
            <span
              key={id}
              className="chip"
              title={c.live ? "live" : c.enabled ? "enabled" : "inactive"}
              style={{ opacity: c.enabled ? 1 : 0.45 }}
            >
              {id}
              {c.live ? " ●" : ""}
            </span>
          ))}
        </span>
      </div>
      <div className="contrib">
        <span className="name">Briefing provider</span>
        <span className="val">
          <span className="chip">{s.llm.provider}</span>
        </span>
      </div>
      <div className="contrib">
        <span className="name">API key required</span>
        <span className="val">{s.security.api_key_required ? "yes" : "no (dev)"}</span>
      </div>
      {s.warnings.length > 0 && (
        <ul style={{ margin: "8px 0 0", paddingLeft: 18, fontSize: 12, color: "var(--watch)" }}>
          {s.warnings.map((w) => (
            <li key={w}>{w}</li>
          ))}
        </ul>
      )}
      <div className="faint" style={{ fontSize: 11, marginTop: 8 }}>
        v{s.version} · zero external AI dependencies required
      </div>
    </div>
  );
}
