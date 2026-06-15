import { useEffect, useState } from "react";
import type { AppData } from "../App";
import { api } from "../api/client";
import type { DistrictForecast, RiskDetail, SignalSeries } from "../api/types";
import { ForecastChart, RiskTimeseriesChart } from "../components/Charts";
import Contributions from "../components/Contributions";
import SeirSimulator from "../components/SeirSimulator";
import SignalBreakdown from "../components/SignalBreakdown";
import { Badge, Spinner } from "../components/common";
import { fmtPct, riskColor } from "../lib/format";

export default function DistrictView({
  data,
  districtId,
  onSelect,
}: {
  data: AppData;
  districtId: string;
  onSelect: (id: string) => void;
}) {
  const [detail, setDetail] = useState<RiskDetail | null>(null);
  const [forecast, setForecast] = useState<DistrictForecast | null>(null);
  const [signals, setSignals] = useState<SignalSeries | null>(null);

  useEffect(() => {
    setDetail(null);
    setSignals(null);
    api.riskDetail(districtId).then(setDetail).catch(() => setDetail(null));
    api.signals(districtId).then(setSignals).catch(() => setSignals(null));
    setForecast(data.forecast.find((f) => f.district_id === districtId) ?? null);
  }, [districtId, data.forecast]);

  if (!detail) return <Spinner label="Loading district intelligence…" />;
  const a = detail.latest;

  return (
    <div className="grid" style={{ gap: 18 }}>
      <div className="section-title">
        <div style={{ display: "flex", alignItems: "center", gap: 14 }}>
          <select
            value={districtId}
            onChange={(e) => onSelect(e.target.value)}
            style={{ width: 220 }}
          >
            {[...data.districts]
              .sort((x, y) => x.name.localeCompare(y.name))
              .map((d) => (
                <option key={d.id} value={d.id}>
                  {d.name}
                </option>
              ))}
          </select>
          <Badge level={a.level} />
          <span className="faint">{a.level === "Normal" ? "" : a.category}</span>
        </div>
        <div style={{ textAlign: "right" }}>
          <div style={{ fontSize: 26, fontWeight: 750, color: riskColor(a.risk_score) }}>
            {a.risk_score.toFixed(0)}<span className="faint" style={{ fontSize: 14 }}>/100</span>
          </div>
          <div className="faint" style={{ fontSize: 12 }}>
            confidence {fmtPct(a.confidence)}
          </div>
        </div>
      </div>

      {a.likely_diseases.length > 0 && (
        <div className="panel" style={{ padding: "12px 16px" }}>
          <span className="muted">Most likely: </span>
          <span className="pill-row" style={{ display: "inline-flex" }}>
            {a.likely_diseases.map((d) => (
              <span className="chip" key={d}>
                {d}
              </span>
            ))}
          </span>
        </div>
      )}

      <div className="split">
        <div className="panel">
          <h3>Risk Trajectory</h3>
          <RiskTimeseriesChart data={detail.timeseries} />
        </div>
        <div className="panel">
          <h3>Why This Risk Score</h3>
          <Contributions items={a.contributions} />
        </div>
      </div>

      <div className="split">
        <div className="panel">
          <h3>Spread Forecast (this district)</h3>
          {forecast ? (
            <ForecastChart forecast={forecast} />
          ) : (
            <div className="muted">No forecast available.</div>
          )}
        </div>
        <div className="panel">
          <h3>Recommended Posture</h3>
          <RecommendedPosture category={a.category} level={a.level} />
        </div>
      </div>

      <SeirSimulator
        districtId={districtId}
        diseases={data.diseases}
        defaultDisease={categoryToDisease(a.category)}
      />

      <div className="panel">
        <h3>Signal Breakdown</h3>
        <div className="panel-sub">Raw surveillance signals feeding the risk model.</div>
        {signals ? <SignalBreakdown signals={signals} /> : <div className="muted">Loading signals…</div>}
      </div>
    </div>
  );
}

function categoryToDisease(category: string): string {
  switch (category) {
    case "Vector":
      return "dengue";
    case "Respiratory":
      return "influenza_like";
    case "Waterborne":
      return "cholera";
    case "Foodborne":
      return "food_poisoning";
    default:
      return "dengue";
  }
}

const POSTURE: Record<string, string[]> = {
  Vector: [
    "Vector-control & fogging in affected wards",
    "Eliminate stagnant-water breeding sites",
    "Pre-position platelet stock & NS1/IgM test kits",
  ],
  Respiratory: [
    "Reinforce mask & respiratory-hygiene advisories",
    "Audit oxygen / ICU / ventilator capacity",
    "Expand respiratory-panel PCR at sentinel sites",
  ],
  Waterborne: [
    "Issue boil-water advisory; chlorinate supply",
    "Deploy ORS / IV-fluid stocks to PHCs",
    "Test drinking-water & sewage cross-contamination",
  ],
  Foodborne: ["Inspect food vendors & common-source events", "Stock ORS / antiemetics at PHCs"],
  Unknown: ["Dispatch rapid-response team for field investigation", "Collect samples for testing"],
};

function RecommendedPosture({ category, level }: { category: string; level: string }) {
  if (level === "Normal") return <div className="muted">Routine surveillance — no action required.</div>;
  const items = POSTURE[category] ?? POSTURE.Unknown;
  return (
    <ol style={{ margin: 0, paddingLeft: 18, lineHeight: 1.7, fontSize: 13.5 }}>
      {items.map((x) => (
        <li key={x}>{x}</li>
      ))}
    </ol>
  );
}
