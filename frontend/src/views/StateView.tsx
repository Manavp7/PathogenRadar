import type { AppData } from "../App";
import MapChoropleth from "../components/MapChoropleth";
import RiskTable from "../components/RiskTable";
import { fmtPct } from "../lib/format";

export default function StateView({
  data,
  onSelect,
}: {
  data: AppData;
  onSelect: (id: string) => void;
}) {
  const elevated = data.risk.filter((r) => r.level !== "Normal");
  const categories = elevated.reduce<Record<string, number>>((acc, r) => {
    acc[r.category] = (acc[r.category] ?? 0) + 1;
    return acc;
  }, {});

  return (
    <div className="grid" style={{ gap: 18 }}>
      <div className="section-title">
        <h2>{data.meta.region} — District Surveillance</h2>
        <span className="sub">{data.meta.districts} districts · click a district for detail</span>
      </div>

      <div className="split">
        <div className="panel">
          <h3>Risk Map</h3>
          <MapChoropleth geojson={data.geojson} risk={data.risk} onSelect={onSelect} />
        </div>
        <div className="panel">
          <h3>District Ranking</h3>
          <RiskTable risk={data.risk} onSelect={onSelect} />
        </div>
      </div>

      <div className="grid cols-2">
        <div className="panel">
          <h3>Disease Category Distribution</h3>
          {Object.keys(categories).length === 0 && (
            <div className="muted">No elevated districts — all categories nominal.</div>
          )}
          {Object.entries(categories).map(([cat, n]) => (
            <div className="contrib" key={cat}>
              <span className="name">{cat}</span>
              <div className="riskbar" style={{ width: 160 }}>
                <span
                  style={{
                    width: `${(n / Math.max(elevated.length, 1)) * 100}%`,
                    background: "#2f81f7",
                  }}
                />
              </div>
              <span className="val">{n}</span>
            </div>
          ))}
        </div>
        <div className="panel">
          <h3>Data Source Reliability</h3>
          {Object.values(data.sources).map((s) => (
            <div className="contrib" key={s.source_id}>
              <span className="name">{s.source_id}</span>
              <div className="riskbar" style={{ width: 160 }}>
                <span
                  style={{
                    width: `${s.reliability * 100}%`,
                    background: s.reliability > 0.85 ? "#2ea043" : "#d4a017",
                  }}
                />
              </div>
              <span className="val">{fmtPct(s.reliability)}</span>
            </div>
          ))}
          <div className="faint" style={{ fontSize: 12, marginTop: 8 }}>
            Sources: {Object.entries(data.meta.source_summary).map(([k, v]) => `${k} (${v})`).join(", ")}
          </div>
        </div>
      </div>
    </div>
  );
}
