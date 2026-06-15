import type { SignalSeries } from "../api/types";
import { SignalSparkline } from "./Charts";

const SIGNAL_LABELS: Record<string, string> = {
  hospital_admissions: "Hospital admissions",
  icu_occupancy: "ICU occupancy",
  ventilator_usage: "Ventilator usage",
  mortality: "Mortality",
  lab_pcr_requests: "PCR test requests",
  search_fever: "Fever searches",
  search_cough: "Cough searches",
  search_rash: "Rash searches",
  search_vomiting: "Vomiting searches",
  search_diarrhea: "Diarrhea searches",
  social_mentions: "Social mentions",
  wastewater_viral_load: "Wastewater viral load",
  weather_rainfall: "Rainfall",
  weather_humidity: "Humidity",
  weather_temp: "Temperature",
};

const ORDER = [
  "hospital_admissions",
  "icu_occupancy",
  "lab_pcr_requests",
  "search_fever",
  "search_rash",
  "social_mentions",
  "wastewater_viral_load",
  "weather_rainfall",
];

export default function SignalBreakdown({ signals }: { signals: SignalSeries }) {
  const keys = ORDER.filter((k) => signals.series[k]?.length);
  return (
    <div className="grid cols-2">
      {keys.map((k) => (
        <div key={k} className="panel" style={{ padding: 12 }}>
          <div style={{ fontSize: 12, color: "var(--text-dim)", marginBottom: 2 }}>
            {SIGNAL_LABELS[k] ?? k}
          </div>
          <SignalSparkline
            points={signals.series[k]}
            color={k.startsWith("weather") ? "#5aa9e6" : k.startsWith("search") ? "#d4a017" : "#f0502f"}
          />
        </div>
      ))}
    </div>
  );
}
