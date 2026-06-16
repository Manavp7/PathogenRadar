import type { AppData } from "../App";
import AlertCard from "../components/AlertCard";
import AuditPanel from "../components/AuditPanel";
import BriefingPanel from "../components/BriefingPanel";
import ModelsPanel from "../components/ModelsPanel";
import RiskTable from "../components/RiskTable";
import SystemStatus from "../components/SystemStatus";
import { KpiCard } from "../components/common";
import { fmtPct } from "../lib/format";

export default function ExecutiveView({
  data,
  onSelect,
}: {
  data: AppData;
  onSelect: (id: string) => void;
}) {
  const onAlert = data.risk.filter((r) => r.level !== "Normal");
  const hotspots = new Set(onAlert.map((r) => r.district_id));
  const spreadOutlook = [...data.forecast]
    .filter((f) => !hotspots.has(f.district_id))
    .sort(
      (a, b) =>
        (b.points.at(-1)?.risk_probability ?? 0) - (a.points.at(-1)?.risk_probability ?? 0)
    )
    .slice(0, 5);

  const actionItems = Array.from(
    new Set(data.alerts.flatMap((a) => a.recommended_actions))
  ).slice(0, 6);

  return (
    <div className="grid" style={{ gap: 18 }}>
      <div className="section-title">
        <h2>Executive Situation Report</h2>
        <span className="sub">{data.meta.region} · as of {data.meta.as_of}</span>
      </div>

      <div className="grid cols-4">
        <KpiCard value={onAlert.length} label="Districts elevated" color={onAlert.length ? "#e8830c" : undefined} />
        <KpiCard
          value={data.risk.filter((r) => r.level === "Emergency").length}
          label="Emergencies"
          color="#e5184a"
        />
        <KpiCard value={data.alerts.length} label="Active alerts" />
        <KpiCard
          value={spreadOutlook.length ? spreadOutlook[0].district_name : "—"}
          label="Next at risk (30d)"
          hint={spreadOutlook.length ? fmtPct(spreadOutlook[0].points.at(-1)!.risk_probability) : ""}
        />
      </div>

      <div className="split">
        <div className="grid" style={{ gap: 18, alignContent: "start" }}>
          <div className="panel">
            <h3>Key Risks</h3>
            <RiskTable risk={onAlert.length ? onAlert : data.risk} onSelect={onSelect} limit={6} />
          </div>
          <div className="panel">
            <h3>30-Day Spread Outlook</h3>
            <div className="panel-sub">Districts likely to escalate from current hotspots.</div>
            {spreadOutlook.length === 0 && <div className="muted">No onward spread projected.</div>}
            {spreadOutlook.map((f) => (
              <div className="contrib" key={f.district_id}>
                <span className="name">{f.district_name}</span>
                <div className="riskbar" style={{ width: 160 }}>
                  <span
                    style={{
                      width: `${(f.points.at(-1)?.risk_probability ?? 0) * 100}%`,
                      background: "#2f81f7",
                    }}
                  />
                </div>
                <span className="val">{fmtPct(f.points.at(-1)?.risk_probability ?? 0)}</span>
              </div>
            ))}
          </div>
          {actionItems.length > 0 && (
            <div className="panel">
              <h3>Priority Action Items</h3>
              <ol style={{ margin: 0, paddingLeft: 18, lineHeight: 1.8, fontSize: 13.5 }}>
                {actionItems.map((x) => (
                  <li key={x}>{x}</li>
                ))}
              </ol>
            </div>
          )}
          {data.alerts.length > 0 && (
            <div className="panel">
              <h3>Alert Detail</h3>
              {data.alerts.map((a) => (
                <AlertCard key={a.id} alert={a} />
              ))}
            </div>
          )}
        </div>
        <div className="grid" style={{ gap: 18, alignContent: "start" }}>
          <BriefingPanel />
          <SystemStatus />
          <ModelsPanel />
          <AuditPanel />
        </div>
      </div>
    </div>
  );
}
