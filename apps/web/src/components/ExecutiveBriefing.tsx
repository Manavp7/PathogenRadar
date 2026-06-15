import type { ExecutiveReport } from "../types";

export function ExecutiveBriefing({ report }: { report: ExecutiveReport }) {
  return (
    <section className="panel briefing">
      <div className="panel-heading">
        <span>Executive briefing</span>
        <small>{report.audience}</small>
      </div>
      <h3>{report.title}</h3>
      <p>{report.summary}</p>
      <ul>
        {report.limitations.map((limitation) => (
          <li key={limitation}>{limitation}</li>
        ))}
      </ul>
    </section>
  );
}
