import type {
  Alert,
  Briefing,
  DiseaseInfo,
  District,
  DistrictForecast,
  Intervention,
  Meta,
  RiskAssessment,
  RiskDetail,
  SeirResult,
  SignalSeries,
  SourceReliability,
} from "./types";

async function get<T>(path: string): Promise<T> {
  const res = await fetch(path);
  if (!res.ok) throw new Error(`${path} -> ${res.status}`);
  return res.json() as Promise<T>;
}

async function post<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(`${path} -> ${res.status}`);
  return res.json() as Promise<T>;
}

export const api = {
  meta: () => get<Meta>("/api/meta"),
  districts: () => get<District[]>("/api/districts"),
  geojson: () => get<GeoJSON.FeatureCollection>("/api/geojson"),
  risk: () => get<RiskAssessment[]>("/api/risk"),
  riskDetail: (id: string) => get<RiskDetail>(`/api/risk/${id}`),
  forecast: () => get<DistrictForecast[]>("/api/forecast"),
  alerts: () => get<Alert[]>("/api/alerts"),
  sources: () => get<Record<string, SourceReliability>>("/api/sources"),
  signals: (id: string) => get<SignalSeries>(`/api/signals/${id}`),
  diseases: () => get<DiseaseInfo[]>("/api/diseases"),
  briefing: () => get<Briefing>("/api/reports/briefing"),
  simulate: (body: {
    district_id: string;
    disease: string;
    days: number;
    intervention: Intervention;
  }) => post<SeirResult>("/api/simulation", body),
};
