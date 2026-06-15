import type { OutbreakLevel } from "../api/types";
import { riskColor } from "../lib/format";

export function Badge({ level }: { level: OutbreakLevel }) {
  return <span className={`badge lvl-${level}`}>{level}</span>;
}

export function Spinner({ label }: { label?: string }) {
  return (
    <div className="center-msg">
      <div className="spinner" />
      {label && <div>{label}</div>}
    </div>
  );
}

export function KpiCard({
  value,
  label,
  hint,
  color,
}: {
  value: React.ReactNode;
  label: string;
  hint?: string;
  color?: string;
}) {
  return (
    <div className="panel kpi">
      <div className="value" style={color ? { color } : undefined}>
        {value}
      </div>
      <div className="label">{label}</div>
      {hint && <div className="hint">{hint}</div>}
    </div>
  );
}

export function RiskBar({ risk }: { risk: number }) {
  return (
    <div className="riskbar" title={`${risk.toFixed(0)}/100`}>
      <span style={{ width: `${Math.min(100, risk)}%`, background: riskColor(risk) }} />
    </div>
  );
}
