import { useEffect, useMemo, useState } from "react";
import { api } from "./api/client";
import type {
  Alert,
  DiseaseInfo,
  District,
  DistrictForecast,
  Meta,
  RiskAssessment,
  SourceReliability,
} from "./api/types";
import { Spinner } from "./components/common";
import Overview from "./views/Overview";
import StateView from "./views/StateView";
import DistrictView from "./views/DistrictView";
import ExecutiveView from "./views/ExecutiveView";

type View = "overview" | "state" | "district" | "executive";

const TABS: { id: View; label: string }[] = [
  { id: "overview", label: "Overview" },
  { id: "state", label: "Kerala" },
  { id: "district", label: "District" },
  { id: "executive", label: "Executive" },
];

export interface AppData {
  meta: Meta;
  risk: RiskAssessment[];
  forecast: DistrictForecast[];
  alerts: Alert[];
  districts: District[];
  diseases: DiseaseInfo[];
  sources: Record<string, SourceReliability>;
  geojson: GeoJSON.FeatureCollection;
}

export default function App() {
  const [view, setView] = useState<View>("overview");
  const [data, setData] = useState<AppData | null>(null);
  const [selected, setSelected] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([
      api.meta(),
      api.risk(),
      api.forecast(),
      api.alerts(),
      api.districts(),
      api.diseases(),
      api.sources(),
      api.geojson(),
    ])
      .then(([meta, risk, forecast, alerts, districts, diseases, sources, geojson]) => {
        setData({ meta, risk, forecast, alerts, districts, diseases, sources, geojson });
        const top = [...risk].sort((a, b) => b.risk_score - a.risk_score)[0];
        setSelected(top?.district_id ?? districts[0]?.id ?? null);
      })
      .catch((e) => setError(String(e)));
  }, []);

  const goDistrict = (id: string) => {
    setSelected(id);
    setView("district");
  };

  const connected = !!data && !error;
  const headerDate = useMemo(() => {
    if (!data) return "";
    return new Date(data.meta.as_of).toLocaleDateString("en-IN", {
      day: "2-digit",
      month: "long",
      year: "numeric",
    });
  }, [data]);

  return (
    <div className="app">
      <a className="skip-link" href="#main">
        Skip to content
      </a>
      <header className="topbar">
        <div className="brand">
          <div className="logo" aria-hidden="true" />
          <div>
            <div className="title">PathogenRadar</div>
            <div className="subtitle">Disease Intelligence Platform</div>
          </div>
        </div>
        <nav className="nav" aria-label="Primary views">
          {TABS.map((t) => (
            <button
              key={t.id}
              className={view === t.id ? "active" : ""}
              aria-current={view === t.id ? "page" : undefined}
              onClick={() => setView(t.id)}
            >
              {t.label}
            </button>
          ))}
        </nav>
        <div className="spacer" />
        <div className="status" role="status">
          {data && <span>{data.meta.region}</span>}
          {headerDate && <span>· as of {headerDate}</span>}
          <span className={`dot ${connected ? "" : "off"}`} aria-hidden="true" />
          {connected ? "Live" : "Offline"}
        </div>
      </header>

      <main className="content" id="main">
        {error && (
          <div className="center-msg">
            <div>⚠ Cannot reach the PathogenRadar API.</div>
            <div className="faint">Start the backend with <code>make api</code>. ({error})</div>
          </div>
        )}
        {!data && !error && <Spinner label="Loading intelligence feed…" />}
        {data && view === "overview" && <Overview data={data} onSelect={goDistrict} />}
        {data && view === "state" && <StateView data={data} onSelect={goDistrict} />}
        {data && view === "district" && selected && (
          <DistrictView data={data} districtId={selected} onSelect={setSelected} />
        )}
        {data && view === "executive" && <ExecutiveView data={data} onSelect={goDistrict} />}
      </main>
    </div>
  );
}
