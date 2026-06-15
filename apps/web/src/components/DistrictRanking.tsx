import type { DistrictIntelligence } from "../types";

interface DistrictRankingProps {
  districts: DistrictIntelligence[];
  selectedDistrictId: string;
  onSelectDistrict: (districtId: string) => void;
}

export function DistrictRanking({
  districts,
  selectedDistrictId,
  onSelectDistrict
}: DistrictRankingProps) {
  return (
    <section className="panel">
      <div className="panel-heading">
        <span>District ranking</span>
        <small>Risk, category, confidence</small>
      </div>
      <div className="ranking">
        {districts.map((item, index) => (
          <button
            key={item.district.id}
            className={selectedDistrictId === item.district.id ? "ranking-row selected" : "ranking-row"}
            onClick={() => onSelectDistrict(item.district.id)}
          >
            <span>#{index + 1}</span>
            <strong>{item.district.name}</strong>
            <em>{item.risk_assessment.category}</em>
            <b>{item.risk_assessment.confidence.toLocaleString(undefined, { style: "percent" })}</b>
          </button>
        ))}
      </div>
    </section>
  );
}
