import { useEffect, useState } from "react";
import { api } from "../api/client";
import type { AuditEntry } from "../api/types";

const STATUS_COLOR = (s: number) =>
  s >= 500 ? "#e5184a" : s >= 400 ? "#e8830c" : "#2ea043";

export default function AuditPanel() {
  const [entries, setEntries] = useState<AuditEntry[] | null>(null);
  const [restricted, setRestricted] = useState(false);

  useEffect(() => {
    api
      .audit()
      .then((e) => setEntries(e.slice(0, 12)))
      .catch(() => setRestricted(true));
  }, []);

  if (restricted) return null; // admin-only; hidden for non-admins

  return (
    <div className="panel">
      <h3>Audit Trail</h3>
      <div className="panel-sub">Recent API access (admin) — RBAC + audit governance.</div>
      {!entries && <div className="muted">Loading…</div>}
      {entries && entries.length === 0 && <div className="muted">No activity yet.</div>}
      {entries && entries.length > 0 && (
        <table className="data">
          <thead>
            <tr>
              <th scope="col">Time</th>
              <th scope="col">Method</th>
              <th scope="col">Path</th>
              <th scope="col">Role</th>
              <th scope="col">Status</th>
            </tr>
          </thead>
          <tbody>
            {entries.map((e, i) => (
              <tr key={i} style={{ cursor: "default" }}>
                <td className="faint">{e.ts.slice(11, 19)}</td>
                <td>{e.method}</td>
                <td className="muted" style={{ maxWidth: 220, overflow: "hidden", textOverflow: "ellipsis" }}>
                  {e.path}
                </td>
                <td>{e.role}</td>
                <td style={{ color: STATUS_COLOR(e.status), fontWeight: 600 }}>{e.status}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
