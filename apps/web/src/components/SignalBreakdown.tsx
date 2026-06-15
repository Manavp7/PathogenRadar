import type { DistrictIntelligence } from "../types";

export function SignalBreakdown({ intelligence }: { intelligence: DistrictIntelligence }) {
  return (
    <section className="panel">
      <div className="panel-heading">
        <span>Signal breakdown</span>
        <small>Source intensity and reliability</small>
      </div>
      <div className="signal-list">
        {intelligence.embeddings.map((embedding) => {
          const quality = intelligence.quality.source_scores.find(
            (score) => score.source === embedding.source
          );
          return (
            <div className="signal-row" key={embedding.source}>
              <div>
                <strong>{embedding.source}</strong>
                <small>{embedding.extracted_symptoms.join(", ") || "context signal"}</small>
              </div>
              <div className="bar">
                <span style={{ width: `${Math.round(embedding.intensity * 100)}%` }} />
              </div>
              <b>{Math.round((quality?.reliability ?? 0) * 100)}%</b>
            </div>
          );
        })}
      </div>
      <p className="confidence">
        Aggregate confidence: {Math.round(intelligence.quality.aggregate_confidence * 100)}%
      </p>
    </section>
  );
}
