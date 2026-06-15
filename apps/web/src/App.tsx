import { useEffect, useMemo, useState } from "react";

import { fetchNationalIntelligence } from "./api/client";
import { AlertPanel } from "./components/AlertPanel";
import { DistrictRanking } from "./components/DistrictRanking";
import { ExecutiveBriefing } from "./components/ExecutiveBriefing";
import { ForecastTimeline } from "./components/ForecastTimeline";
import { Heatmap } from "./components/Heatmap";
import { ModuleMap } from "./components/ModuleMap";
import { RecommendationPanel } from "./components/RecommendationPanel";
import { SignalBreakdown } from "./components/SignalBreakdown";
import type { NationalIntelligence } from "./types";

export default function App() {
  const [data, setData] = useState<NationalIntelligence | null>(null);
  const [selectedDistrictId, setSelectedDistrictId] = useState("kerala-ernakulam");

  useEffect(() => {
    fetchNationalIntelligence().then((payload) => {
      setData(payload);
      setSelectedDistrictId(payload.districts[0]?.district.id ?? "kerala-ernakulam");
    });
  }, []);

  const selected = useMemo(() => {
    return data?.districts.find((item) => item.district.id === selectedDistrictId) ?? data?.districts[0];
  }, [data, selectedDistrictId]);

  if (!data || !selected) {
    return <main className="loading">Loading PathogenRadar intelligence...</main>;
  }

  return (
    <main>
      <header className="hero">
        <div>
          <span className="eyebrow">National disease intelligence operating system</span>
          <h1>PathogenRadar</h1>
          <p>{data.national_summary}</p>
        </div>
        <div className={`hero-risk level-${selected.risk_assessment.alert_level}`}>
          <small>{selected.district.name}</small>
          <strong>{selected.risk_assessment.risk_score.toFixed(1)}</strong>
          <span>{selected.risk_assessment.alert_level}</span>
        </div>
      </header>

      <div className="disclaimer">
        Demo/synthetic intelligence only. Not for clinical diagnosis or emergency action.
      </div>

      <section className="dashboard-grid">
        <Heatmap
          districts={data.districts}
          selectedDistrictId={selectedDistrictId}
          onSelectDistrict={setSelectedDistrictId}
        />
        <DistrictRanking
          districts={data.districts}
          selectedDistrictId={selectedDistrictId}
          onSelectDistrict={setSelectedDistrictId}
        />
      </section>

      <section className="district-header panel">
        <div>
          <span className="eyebrow">District view</span>
          <h2>
            {selected.district.name}, {selected.district.state}
          </h2>
          <p>
            Category: <b>{selected.risk_assessment.category}</b> · Confidence:{" "}
            <b>{Math.round(selected.risk_assessment.confidence * 100)}%</b> · Novelty:{" "}
            <b>{Math.round(selected.risk_assessment.novelty_score * 100)}%</b>
          </p>
        </div>
        <div className="matched">
          {selected.risk_assessment.matched_diseases.map((disease) => (
            <span key={disease}>{disease}</span>
          ))}
        </div>
      </section>

      <section className="dashboard-grid three">
        <SignalBreakdown intelligence={selected} />
        <ForecastTimeline forecast={selected.forecast} />
        <AlertPanel alert={selected.alert} />
      </section>

      <section className="dashboard-grid">
        <RecommendationPanel recommendations={selected.recommendations} />
        <ExecutiveBriefing report={selected.report} />
      </section>

      <ModuleMap />
    </main>
  );
}
