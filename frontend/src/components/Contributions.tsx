import type { Contribution } from "../api/types";

export default function Contributions({ items }: { items: Contribution[] }) {
  if (!items.length) return <div className="muted">No significant drivers.</div>;
  const max = Math.max(...items.map((i) => Math.abs(i.value)), 1);
  return (
    <div>
      {items.map((c, i) => (
        <div className="contrib" key={i}>
          <span className="name">{c.label}</span>
          <div className="riskbar" style={{ width: 110 }}>
            <span
              style={{
                width: `${(Math.abs(c.value) / max) * 100}%`,
                background: c.value >= 0 ? "#f0502f" : "#2ea043",
              }}
            />
          </div>
          <span className="val" style={{ width: 64, textAlign: "right" }}>
            {c.detail || (c.value >= 0 ? `+${c.value}` : c.value)}
          </span>
        </div>
      ))}
    </div>
  );
}
