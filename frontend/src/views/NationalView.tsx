import { useEffect, useState } from "react";
import { api, type National } from "../api/client";
import { Badge, KpiCard, Spinner } from "../components/common";
import type { OutbreakLevel } from "../api/types";
import { riskColor } from "../lib/format";

export default function NationalView() {
  const [data, setData] = useState<National | null>(null);
  const [err, setErr] = useState(false);

  useEffect(() => {
    api.national().then(setData).catch(() => setErr(true));
  }, []);

  if (err) return <div className="center-msg">Unable to load national roll-up.</div>;
  if (!data) return <Spinner label="Aggregating national intelligence…" />;

  return (
    <div className="grid" style={{ gap: 18 }}>
      <div className="section-title">
        <h2>National Disease Intelligence</h2>
        <span className="sub">{data.totals.regions} regions monitored</span>
      </div>

      <div className="grid cols-4">
        <KpiCard value={data.totals.regions} label="Regions" />
        <KpiCard value={data.totals.districts} label="Districts monitored" />
        <KpiCard
          value={data.totals.elevated}
          label="Districts elevated"
          color={data.totals.elevated ? "#e8830c" : undefined}
        />
        <KpiCard
          value={data.totals.alerts}
          label="Active alerts"
          color={data.totals.alerts ? "#f0502f" : undefined}
        />
      </div>

      <div className="split">
        <div className="panel">
          <h3>Regions</h3>
          <table className="data">
            <thead>
              <tr>
                <th scope="col">Region</th>
                <th scope="col">Districts</th>
                <th scope="col">Elevated</th>
                <th scope="col">Top district</th>
                <th scope="col">Peak risk</th>
              </tr>
            </thead>
            <tbody>
              {data.regions.map((r) => (
                <tr key={r.key}>
                  <td>{r.name}</td>
                  <td>{r.districts}</td>
                  <td>{r.elevated}</td>
                  <td className="muted">{r.top_district ?? "—"}</td>
                  <td style={{ fontWeight: 700, color: riskColor(r.top_risk) }}>
                    {r.top_risk.toFixed(0)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <div className="panel">
          <h3>Top National Hotspots</h3>
          {data.hotspots.length === 0 && <div className="muted">No elevated districts.</div>}
          {data.hotspots.map((h, i) => (
            <div className="contrib" key={i}>
              <span className="name">
                {h.district_name} <span className="faint">· {h.region}</span>
              </span>
              <Badge level={h.level as OutbreakLevel} />
              <span className="val" style={{ width: 44, textAlign: "right" }}>
                {h.risk_score.toFixed(0)}
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
