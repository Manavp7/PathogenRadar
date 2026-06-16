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
  SystemStatus,
  Timeline,
} from "./types";

function qs(params: Record<string, string | undefined>): string {
  const entries = Object.entries(params).filter(([, v]) => v != null && v !== "");
  return entries.length ? "?" + entries.map(([k, v]) => `${k}=${encodeURIComponent(v!)}`).join("&") : "";
}

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

export interface RegionInfo {
  default: string;
  regions: { key: string; name: string; districts: number }[];
}

export interface National {
  regions: {
    key: string;
    name: string;
    districts: number;
    elevated: number;
    alerts: number;
    top_district: string | null;
    top_risk: number;
    as_of: string | null;
  }[];
  totals: { regions: number; districts: number; alerts: number; elevated: number };
  hotspots: {
    region: string;
    district_name: string;
    risk_score: number;
    level: string;
    category: string;
  }[];
}

export const api = {
  regions: () => get<RegionInfo>("/api/regions"),
  national: () => get<National>("/api/national"),
  system: () => get<SystemStatus>("/api/system"),
  diseases: () => get<DiseaseInfo[]>("/api/diseases"),

  meta: (region?: string) => get<Meta>(`/api/meta${qs({ region })}`),
  districts: (region?: string) => get<District[]>(`/api/districts${qs({ region })}`),
  geojson: (region?: string) => get<GeoJSON.FeatureCollection>(`/api/geojson${qs({ region })}`),
  risk: (region?: string) => get<RiskAssessment[]>(`/api/risk${qs({ region })}`),
  riskAt: (date: string, region?: string) =>
    get<RiskAssessment[]>(`/api/risk${qs({ as_of: date, region })}`),
  timeline: (region?: string) => get<Timeline>(`/api/timeline${qs({ region })}`),
  riskDetail: (id: string, region?: string) => get<RiskDetail>(`/api/risk/${id}${qs({ region })}`),
  forecast: (region?: string) => get<DistrictForecast[]>(`/api/forecast${qs({ region })}`),
  alerts: (region?: string) => get<Alert[]>(`/api/alerts${qs({ region })}`),
  sources: (region?: string) =>
    get<Record<string, SourceReliability>>(`/api/sources${qs({ region })}`),
  signals: (id: string, region?: string) => get<SignalSeries>(`/api/signals/${id}${qs({ region })}`),
  briefing: (region?: string) => get<Briefing>(`/api/reports/briefing${qs({ region })}`),
  simulate: (
    body: { district_id: string; disease: string; days: number; intervention: Intervention },
    region?: string
  ) => post<SeirResult>(`/api/simulation${qs({ region })}`, body),
};
