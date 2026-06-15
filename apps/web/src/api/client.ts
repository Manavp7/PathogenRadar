import type { NationalIntelligence } from "../types";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000";

export async function fetchNationalIntelligence(): Promise<NationalIntelligence> {
  try {
    const response = await fetch(`${API_BASE_URL}/intelligence/national`);
    if (!response.ok) {
      throw new Error(`API returned ${response.status}`);
    }
    return (await response.json()) as NationalIntelligence;
  } catch {
    return fallbackNationalIntelligence;
  }
}

export const fallbackNationalIntelligence: NationalIntelligence = {
  generated_at: new Date().toISOString(),
  national_summary:
    "Demo fallback: Ernakulam carries the highest synthetic vector-outbreak risk.",
  districts: [
    {
      district: {
        id: "kerala-ernakulam",
        name: "Ernakulam",
        state: "Kerala",
        population: 3420000,
        latitude: 9.9816,
        longitude: 76.2999
      },
      quality: {
        aggregate_confidence: 0.83,
        missing_sources: [],
        source_scores: [
          { source: "hospital", reliability: 0.86, issues: [] },
          { source: "search", reliability: 0.84, issues: [] },
          { source: "social", reliability: 0.81, issues: [] },
          { source: "weather", reliability: 0.88, issues: [] },
          { source: "environmental", reliability: 0.85, issues: [] },
          { source: "mobility", reliability: 0.9, issues: [] },
          { source: "wastewater", reliability: 0.79, issues: [] }
        ]
      },
      embeddings: [
        { source: "hospital", intensity: 0.78, confidence: 0.86, extracted_symptoms: ["fever", "rash"] },
        { source: "search", intensity: 0.64, confidence: 0.84, extracted_symptoms: ["fever", "rash"] },
        { source: "wastewater", intensity: 0.71, confidence: 0.79, extracted_symptoms: [] },
        { source: "environmental", intensity: 0.55, confidence: 0.85, extracted_symptoms: [] }
      ],
      risk_assessment: {
        district: {
          id: "kerala-ernakulam",
          name: "Ernakulam",
          state: "Kerala",
          population: 3420000,
          latitude: 9.9816,
          longitude: 76.2999
        },
        risk_score: 74,
        alert_level: "alert",
        category: "vector",
        confidence: 0.83,
        novelty_score: 0.12,
        is_novel_anomaly: false,
        matched_diseases: ["Dengue-like vector outbreak"]
      },
      forecast: {
        origin_district_id: "kerala-ernakulam",
        points: [
          { horizon_days: 7, district_probabilities: { "kerala-ernakulam": 0.74 }, confidence: 0.78 },
          { horizon_days: 14, district_probabilities: { "kerala-ernakulam": 0.82 }, confidence: 0.72 },
          { horizon_days: 21, district_probabilities: { "kerala-ernakulam": 0.88 }, confidence: 0.66 },
          { horizon_days: 30, district_probabilities: { "kerala-ernakulam": 0.9 }, confidence: 0.61 }
        ]
      },
      recommendations: [
        {
          intervention: "vector_control",
          priority: "high",
          rationale: "Vector-like symptoms plus rainfall/environment risk are elevated.",
          expected_effect: "Reduces vector density.",
          burden: "medium"
        }
      ],
      explanations: [
        {
          label: "Hospital pressure",
          source: "hospital",
          contribution: 0.78,
          detail: "ICU and lab-order signals are elevated in synthetic fixtures."
        }
      ],
      report: {
        title: "PathogenRadar briefing: Ernakulam",
        audience: "Health Minister",
        summary:
          "Ernakulam is at ALERT level in fallback demo data with vector-pattern indicators.",
        limitations: ["Fallback demo data only; backend API was unavailable."]
      },
      alert: {
        id: "alert-kerala-ernakulam-alert",
        level: "alert",
        title: "Alert for Ernakulam",
        message: "Synthetic vector outbreak intelligence indicates elevated risk."
      }
    }
  ]
};
