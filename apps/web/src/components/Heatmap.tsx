import type { DistrictIntelligence } from "../types";

interface HeatmapProps {
  districts: DistrictIntelligence[];
  selectedDistrictId: string;
  onSelectDistrict: (districtId: string) => void;
}

export function Heatmap({ districts, selectedDistrictId, onSelectDistrict }: HeatmapProps) {
  return (
    <section className="panel">
      <div className="panel-heading">
        <span>National heatmap</span>
        <small>Synthetic district risk</small>
      </div>
      <div className="heatmap-grid">
        {districts.map((item) => (
          <button
            className={`risk-card level-${item.risk_assessment.alert_level} ${
              selectedDistrictId === item.district.id ? "selected" : ""
            }`}
            key={item.district.id}
            onClick={() => onSelectDistrict(item.district.id)}
          >
            <strong>{item.district.name}</strong>
            <span>{item.district.state}</span>
            <b>{item.risk_assessment.risk_score.toFixed(1)}</b>
            <em>{item.risk_assessment.alert_level}</em>
          </button>
        ))}
      </div>
    </section>
  );
}
