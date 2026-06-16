import { useEffect, useState } from "react";
import { api, type Genomics } from "../api/client";
import { useRegion } from "../lib/region";

const COLORS = ["#2f81f7", "#2ea043", "#d4a017", "#e5184a", "#8957e5", "#3aa0ff"];

export default function GenomicsPanel() {
  const region = useRegion();
  const [g, setG] = useState<Genomics | null>(null);

  useEffect(() => {
    api.genomics(region).then(setG).catch(() => setG(null));
  }, [region]);

  if (!g) return null;

  return (
    <div className="panel">
      <h3>Genomic Surveillance</h3>
      <div className="panel-sub">{g.note}</div>

      {g.emerging.length > 0 && (
        <div
          className="alert-card"
          style={{ borderLeftColor: "var(--emergency)", background: "#e5184a14" }}
        >
          <b style={{ color: "var(--emergency)" }}>⚠ Emerging variant: {g.emerging[0].name}</b>
          <div className="faint" style={{ fontSize: 12 }}>
            now {Math.round(g.emerging[0].current_share * 100)}% of sequences (rising) ·
            projected R₀ ×{g.r0_multiplier.toFixed(2)}, severity ×{g.severity_multiplier.toFixed(2)}
          </div>
        </div>
      )}

      <div style={{ marginTop: 10 }}>
        <div className="faint" style={{ fontSize: 11, marginBottom: 6 }}>
          CURRENT LINEAGE MIX
        </div>
        {/* Stacked composition bar */}
        <div style={{ display: "flex", height: 16, borderRadius: 6, overflow: "hidden" }}>
          {g.current_mix.map((m, i) => (
            <div
              key={m.id}
              title={`${m.name} ${Math.round(m.share * 100)}%`}
              style={{ width: `${m.share * 100}%`, background: COLORS[i % COLORS.length] }}
            />
          ))}
        </div>
        <div className="pill-row" style={{ marginTop: 8 }}>
          {g.current_mix.map((m, i) => (
            <span className="chip" key={m.id}>
              <span
                style={{
                  display: "inline-block",
                  width: 8,
                  height: 8,
                  borderRadius: 2,
                  background: COLORS[i % COLORS.length],
                  marginRight: 6,
                }}
              />
              {m.name} {Math.round(m.share * 100)}%
            </span>
          ))}
        </div>
      </div>
    </div>
  );
}
