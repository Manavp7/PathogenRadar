import type { RiskAssessment } from "../api/types";
import { Badge, RiskBar } from "./common";

interface Props {
  risk: RiskAssessment[];
  selected?: string | null;
  onSelect?: (id: string) => void;
  limit?: number;
}

export default function RiskTable({ risk, selected, onSelect, limit }: Props) {
  const rows = [...risk].sort((a, b) => b.risk_score - a.risk_score).slice(0, limit ?? risk.length);
  return (
    <table className="data">
      <thead>
        <tr>
          <th scope="col">District</th>
          <th scope="col">Risk</th>
          <th scope="col" aria-label="Risk bar"></th>
          <th scope="col">Level</th>
          <th scope="col">Category</th>
        </tr>
      </thead>
      <tbody>
        {rows.map((r) => (
          <tr
            key={r.district_id}
            className={selected === r.district_id ? "selected" : ""}
            onClick={() => onSelect?.(r.district_id)}
            tabIndex={onSelect ? 0 : undefined}
            aria-label={
              onSelect
                ? `${r.district_name}, risk ${r.risk_score.toFixed(0)}, ${r.level}`
                : undefined
            }
            onKeyDown={(e) => {
              if (onSelect && (e.key === "Enter" || e.key === " ")) {
                e.preventDefault();
                onSelect(r.district_id);
              }
            }}
          >
            <td>{r.district_name}</td>
            <td style={{ fontVariantNumeric: "tabular-nums", fontWeight: 600 }}>
              {r.risk_score.toFixed(0)}
            </td>
            <td style={{ width: 90 }}>
              <RiskBar risk={r.risk_score} />
            </td>
            <td>
              <Badge level={r.level} />
            </td>
            <td className="muted">{r.level === "Normal" ? "—" : r.category}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
}
