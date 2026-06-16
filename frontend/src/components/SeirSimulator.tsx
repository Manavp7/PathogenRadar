import { useEffect, useState } from "react";
import { api } from "../api/client";
import type { DiseaseInfo, Intervention, SeirResult } from "../api/types";
import { fmtInt } from "../lib/format";
import { useRegion } from "../lib/region";
import { SeirChart } from "./Charts";

const LEVERS: { key: keyof Intervention; label: string }[] = [
  { key: "school_closure", label: "School closure" },
  { key: "masking", label: "Masking" },
  { key: "vaccination_rate", label: "Vaccination" },
  { key: "travel_restriction", label: "Travel restriction" },
];

export default function SeirSimulator({
  districtId,
  diseases,
  defaultDisease,
}: {
  districtId: string;
  diseases: DiseaseInfo[];
  defaultDisease?: string;
}) {
  const region = useRegion();
  const [disease, setDisease] = useState(defaultDisease ?? "dengue");
  const [iv, setIv] = useState<Intervention>({
    school_closure: 0.5,
    masking: 0.5,
    vaccination_rate: 0.2,
    travel_restriction: 0.3,
  });
  const [result, setResult] = useState<SeirResult | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    const t = setTimeout(() => {
      api
        .simulate({ district_id: districtId, disease, days: 160, intervention: iv }, region)
        .then((r) => !cancelled && setResult(r))
        .catch(() => !cancelled && setResult(null))
        .finally(() => !cancelled && setLoading(false));
    }, 180);
    return () => {
      cancelled = true;
      clearTimeout(t);
    };
  }, [districtId, disease, iv, region]);

  return (
    <div className="panel">
      <h3>Intervention Simulator (SEIR)</h3>
      <div className="panel-sub">
        Project the epidemic curve and test "what if we act now?" — deterministic compartmental model.
      </div>
      <div className="split" style={{ gridTemplateColumns: "1fr 1.4fr", alignItems: "start" }}>
        <div>
          <div className="control">
            <label>Disease</label>
            <select value={disease} onChange={(e) => setDisease(e.target.value)}>
              {diseases.map((d) => (
                <option key={d.id} value={d.id}>
                  {d.name}
                </option>
              ))}
            </select>
          </div>
          {LEVERS.map((l) => (
            <div className="control" key={l.key}>
              <label>
                {l.label} <b>{Math.round(iv[l.key] * 100)}%</b>
              </label>
              <input
                type="range"
                min={0}
                max={1}
                step={0.05}
                value={iv[l.key]}
                onChange={(e) => setIv({ ...iv, [l.key]: parseFloat(e.target.value) })}
              />
            </div>
          ))}
        </div>
        <div>
          {result ? (
            <>
              <SeirChart result={result} />
              <div className="grid cols-3" style={{ marginTop: 10 }}>
                <Stat label="Peak (no action)" value={fmtInt(result.peak_infected_baseline)} c="#f0502f" />
                <Stat
                  label="Peak (intervened)"
                  value={result.peak_infected_intervention != null ? fmtInt(result.peak_infected_intervention) : "—"}
                  c="#2ea043"
                />
                <Stat
                  label="Cases averted"
                  value={result.cases_averted != null ? fmtInt(result.cases_averted) : "—"}
                  c="#2f81f7"
                />
              </div>
              <div className="faint" style={{ fontSize: 12, marginTop: 8 }}>
                R₀ {result.r0} · effective R {result.effective_r} {loading ? "· updating…" : ""}
              </div>
            </>
          ) : (
            <div className="muted" style={{ padding: 30 }}>
              {loading ? "Simulating…" : "No result"}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function Stat({ label, value, c }: { label: string; value: string; c: string }) {
  return (
    <div>
      <div style={{ fontSize: 18, fontWeight: 700, color: c }}>{value}</div>
      <div className="faint" style={{ fontSize: 11 }}>
        {label}
      </div>
    </div>
  );
}
