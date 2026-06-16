export type OutbreakLevel = "Normal" | "Watch" | "Warning" | "Alert" | "Emergency";

export interface Contribution {
  label: string;
  value: number;
  detail: string;
}

export interface RiskAssessment {
  district_id: string;
  district_name: string;
  date: string;
  risk_score: number;
  level: OutbreakLevel;
  category: string;
  likely_diseases: string[];
  confidence: number;
  signal_scores: Record<string, number>;
  contributions: Contribution[];
}

export interface ForecastPoint {
  horizon_days: number;
  risk_probability: number;
}

export interface DistrictForecast {
  district_id: string;
  district_name: string;
  current_risk: number;
  points: ForecastPoint[];
}

export interface Alert {
  id: string;
  district_id: string;
  district_name: string;
  date: string;
  level: OutbreakLevel;
  category: string;
  risk_score: number;
  headline: string;
  reasons: string[];
  recommended_actions: string[];
  channels: string[];
}

export interface District {
  id: string;
  name: string;
  population: number;
  lat: number;
  lon: number;
  neighbors: string[];
}

export interface Meta {
  region: string;
  start: string;
  end: string;
  as_of: string;
  source_summary: Record<string, string>;
  districts: number;
  active_alerts: number;
}

export interface SourceReliability {
  source_id: string;
  reliability: number;
  completeness: number;
  stability: number;
  notes: string[];
}

export interface RiskDetail {
  latest: RiskAssessment;
  timeseries: { date: string; risk_score: number; level: OutbreakLevel }[];
  detectors: Record<string, number | string | null>[];
}

export interface SignalSeries {
  district_id: string;
  series: Record<string, { date: string; value: number }[]>;
}

export interface SeirCurve {
  days: number[];
  susceptible: number[];
  exposed: number[];
  infected: number[];
  recovered: number[];
}

export interface SeirResult {
  district_id: string;
  disease: string;
  population: number;
  r0: number;
  effective_r: number;
  baseline: SeirCurve;
  intervention: SeirCurve | null;
  peak_infected_baseline: number;
  peak_day_baseline: number;
  peak_infected_intervention: number | null;
  peak_day_intervention: number | null;
  cases_averted: number | null;
}

export interface Intervention {
  school_closure: number;
  masking: number;
  vaccination_rate: number;
  travel_restriction: number;
}

export interface Briefing {
  region: string;
  date: string;
  provider: string;
  title: string;
  body: string;
}

export interface DiseaseInfo {
  id: string;
  name: string;
  category: string;
}

export interface TimelinePoint {
  date: string;
  mean: number;
  max: number;
}

export interface Timeline {
  dates: string[];
  series: TimelinePoint[];
}

export interface SystemStatus {
  version: string;
  region: string;
  offline_mode: boolean;
  connectors: Record<string, { enabled: boolean; live: boolean }>;
  llm: { provider: string; key_present: boolean; required: boolean };
  security: { api_key_required: boolean };
  data: { as_of: string | null; source_summary: Record<string, string> };
  warnings: string[];
}
