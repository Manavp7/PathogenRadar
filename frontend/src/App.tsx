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
import { RegionContext } from "./lib/region";
import Overview from "./views/Overview";
import StateView from "./views/StateView";
import DistrictView from "./views/DistrictView";
import ExecutiveView from "./views/ExecutiveView";
import NationalView from "./views/NationalView";

type View = "national" | "overview" | "state" | "district" | "executive";

const TABS: { id: View; label: string }[] = [
  { id: "national", label: "National" },
  { id: "overview", label: "Overview" },
  { id: "state", label: "State" },
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
  const [regions, setRegions] = useState<{ key: string; name: string }[]>([]);
  const [region, setRegion] = useState<string | undefined>(undefined);
  const [diseases, setDiseases] = useState<DiseaseInfo[]>([]);
  const [data, setData] = useState<AppData | null>(null);
  const [selected, setSelected] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Bootstrap: region list + diseases (global).
  useEffect(() => {
    Promise.all([api.regions(), api.diseases()])
      .then(([r, d]) => {
        setRegions(r.regions.map((x) => ({ key: x.key, name: x.name })));
        setRegion(r.default);
        setDiseases(d);
      })
      .catch((e) => setError(String(e)));
  }, []);

  // Region-scoped data; refetch when region changes.
  useEffect(() => {
    if (!region) return;
    setData(null);
    Promise.all([
      api.meta(region),
      api.risk(region),
      api.forecast(region),
      api.alerts(region),
      api.districts(region),
      api.sources(region),
      api.geojson(region),
    ])
      .then(([meta, risk, forecast, alerts, districts, sources, geojson]) => {
        setData({ meta, risk, forecast, alerts, districts, diseases, sources, geojson });
        const top = [...risk].sort((a, b) => b.risk_score - a.risk_score)[0];
        setSelected(top?.district_id ?? districts[0]?.id ?? null);
      })
      .catch((e) => setError(String(e)));
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [region, diseases]);

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
    <RegionContext.Provider value={region}>
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
          {regions.length > 1 && view !== "national" && (
            <select
              aria-label="Region"
              value={region ?? ""}
              onChange={(e) => setRegion(e.target.value)}
              style={{ width: 150 }}
            >
              {regions.map((r) => (
                <option key={r.key} value={r.key}>
                  {r.name}
                </option>
              ))}
            </select>
          )}
          <div className="status" role="status">
            {headerDate && <span>as of {headerDate}</span>}
            <span className={`dot ${connected ? "" : "off"}`} aria-hidden="true" />
            {connected ? "Live" : "Offline"}
          </div>
        </header>

        <main className="content" id="main">
          {error && (
            <div className="center-msg">
              <div>⚠ Cannot reach the PathogenRadar API.</div>
              <div className="faint">
                Start the backend with <code>make api</code>. ({error})
              </div>
            </div>
          )}
          {view === "national" && !error && <NationalView />}
          {view !== "national" && !data && !error && <Spinner label="Loading intelligence feed…" />}
          {view !== "national" && data && view === "overview" && (
            <Overview data={data} onSelect={goDistrict} />
          )}
          {view !== "national" && data && view === "state" && (
            <StateView data={data} onSelect={goDistrict} />
          )}
          {view !== "national" && data && view === "district" && selected && (
            <DistrictView data={data} districtId={selected} onSelect={setSelected} />
          )}
          {view !== "national" && data && view === "executive" && (
            <ExecutiveView data={data} onSelect={goDistrict} />
          )}
        </main>
      </div>
    </RegionContext.Provider>
  );
}
