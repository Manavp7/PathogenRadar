import { useEffect, useState } from "react";
import { api } from "../api/client";
import { useRegion } from "../lib/region";

type Models = Awaited<ReturnType<typeof api.models>>;

export default function ModelsPanel() {
  const region = useRegion();
  const [data, setData] = useState<Models | null>(null);

  useEffect(() => {
    api.models(region).then(setData).catch(() => setData(null));
  }, [region]);

  if (!data) return null;

  return (
    <div className="panel">
      <h3>ML Models &amp; Drift</h3>
      <div className="panel-sub">Model registry + data-drift monitoring (MLOps).</div>
      {data.models.length === 0 && (
        <div className="muted">No models registered — run <code>make retrain</code>.</div>
      )}
      {data.models.map((m) => {
        const metric = Object.entries(m.metrics)[0];
        return (
          <div className="contrib" key={m.name}>
            <span className="name">
              {m.name} <span className="chip">{m.version}</span>
            </span>
            <span className="faint" style={{ fontSize: 11 }}>
              {m.framework}
            </span>
            <span className="val" style={{ width: 120, textAlign: "right" }}>
              {metric ? `${metric[0]} ${metric[1]}` : "—"}
            </span>
          </div>
        );
      })}
      <div
        style={{
          marginTop: 10,
          fontSize: 12,
          color: data.drift.retrain_recommended ? "var(--warning)" : "var(--text-dim)",
        }}
      >
        Drift: max PSI {data.drift.max_psi.toFixed(2)}{" "}
        {data.drift.retrain_recommended ? "· retraining recommended" : "· stable"}
        {data.drift.drifting_signals.length > 0 &&
          ` (${data.drift.drifting_signals.slice(0, 3).join(", ")})`}
      </div>
    </div>
  );
}
