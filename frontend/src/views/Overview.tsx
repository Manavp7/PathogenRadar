import { useEffect, useState } from "react";
import type { AppData } from "../App";
import { api } from "../api/client";
import type { RiskAssessment } from "../api/types";
import AlertCard from "../components/AlertCard";
import MapChoropleth from "../components/MapChoropleth";
import RiskTable from "../components/RiskTable";
import TimeMachine from "../components/TimeMachine";
import { KpiCard } from "../components/common";
import { riskColor, shortDate } from "../lib/format";
import { useRegion } from "../lib/region";

export default function Overview({
  data,
  onSelect,
}: {
  data: AppData;
  onSelect: (id: string) => void;
}) {
  const region = useRegion();
  const [histDate, setHistDate] = useState<string | null>(null);
  const [histRisk, setHistRisk] = useState<RiskAssessment[] | null>(null);

  useEffect(() => {
    if (!histDate) {
      setHistRisk(null);
      return;
    }
    let cancelled = false;
    api.riskAt(histDate, region).then((r) => !cancelled && setHistRisk(r)).catch(() => {});
    return () => {
      cancelled = true;
    };
  }, [histDate, region]);

  const mapRisk = histRisk ?? data.risk;
  const onAlert = data.risk.filter((r) => r.level !== "Normal");
  const emergencies = data.risk.filter((r) => r.level === "Emergency" || r.level === "Alert");
  const top = [...data.risk].sort((a, b) => b.risk_score - a.risk_score)[0];

  return (
    <div className="grid" style={{ gap: 18 }}>
      <TimeMachine onChange={setHistDate} />
      <div className="grid cols-4">
        <KpiCard value={data.meta.districts} label="Districts monitored" hint={data.meta.region} />
        <KpiCard
          value={onAlert.length}
          label="Districts elevated"
          hint={`${emergencies.length} alert/emergency`}
          color={onAlert.length ? "#e8830c" : undefined}
        />
        <KpiCard
          value={top ? `${top.risk_score.toFixed(0)}` : "—"}
          label="Highest risk score"
          hint={top?.district_name}
          color={top ? riskColor(top.risk_score) : undefined}
        />
        <KpiCard
          value={data.alerts.length}
          label="Active alerts"
          hint="across all channels"
          color={data.alerts.length ? "#f0502f" : undefined}
        />
      </div>

      <div className="split">
        <div className="panel">
          <h3>
            Outbreak Risk Heatmap
            {histDate && (
              <span className="chip" style={{ marginLeft: 10 }}>
                historical · {shortDate(histDate)}
              </span>
            )}
          </h3>
          <MapChoropleth geojson={data.geojson} risk={mapRisk} onSelect={onSelect} />
        </div>
        <div className="grid" style={{ gap: 18, alignContent: "start" }}>
          <div className="panel">
            <h3>Highest-Risk Districts{histDate ? ` · ${shortDate(histDate)}` : ""}</h3>
            <RiskTable risk={mapRisk} onSelect={onSelect} limit={6} />
          </div>
          <div className="panel">
            <h3>Active Alerts</h3>
            {data.alerts.length === 0 && <div className="muted">No active alerts.</div>}
            {data.alerts.slice(0, 3).map((a) => (
              <AlertCard key={a.id} alert={a} compact />
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
