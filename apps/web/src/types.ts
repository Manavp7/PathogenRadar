export type AlertLevel = "normal" | "watch" | "warning" | "alert" | "emergency";

export type SignalSource =
  | "hospital"
  | "search"
  | "social"
  | "weather"
  | "environmental"
  | "mobility"
  | "wastewater";

export interface District {
  id: string;
  name: string;
  state: string;
  population: number;
  latitude: number;
  longitude: number;
}

export interface SourceQualityScore {
  source: SignalSource;
  reliability: number;
  issues: string[];
}

export interface QualityReport {
  aggregate_confidence: number;
  source_scores: SourceQualityScore[];
  missing_sources: SignalSource[];
}

export interface SignalEmbedding {
  source: SignalSource;
  intensity: number;
  confidence: number;
  extracted_symptoms: string[];
}

export interface RiskAssessment {
  district: District;
  risk_score: number;
  alert_level: AlertLevel;
  category: string;
  confidence: number;
  novelty_score: number;
  is_novel_anomaly: boolean;
  matched_diseases: string[];
}

export interface ForecastPoint {
  horizon_days: number;
  district_probabilities: Record<string, number>;
  confidence: number;
}

export interface SpreadForecast {
  origin_district_id: string;
  points: ForecastPoint[];
}

export interface Recommendation {
  intervention: string;
  priority: string;
  rationale: string;
  expected_effect: string;
  burden: string;
}

export interface ExplanationFactor {
  label: string;
  source: SignalSource | null;
  contribution: number;
  detail: string;
}

export interface Alert {
  id: string;
  level: AlertLevel;
  title: string;
  message: string;
}

export interface ExecutiveReport {
  title: string;
  audience: string;
  summary: string;
  limitations: string[];
}

export interface DistrictIntelligence {
  district: District;
  quality: QualityReport;
  embeddings: SignalEmbedding[];
  risk_assessment: RiskAssessment;
  forecast: SpreadForecast;
  recommendations: Recommendation[];
  explanations: ExplanationFactor[];
  report: ExecutiveReport;
  alert: Alert | null;
}

export interface NationalIntelligence {
  generated_at: string;
  districts: DistrictIntelligence[];
  national_summary: string;
}
