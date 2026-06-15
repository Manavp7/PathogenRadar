import type { Recommendation } from "../types";

export function RecommendationPanel({ recommendations }: { recommendations: Recommendation[] }) {
  return (
    <section className="panel">
      <div className="panel-heading">
        <span>Intervention recommendations</span>
        <small>Rule-policy placeholder for future RL</small>
      </div>
      <div className="recommendations">
        {recommendations.map((recommendation) => (
          <article key={`${recommendation.intervention}-${recommendation.priority}`}>
            <span className="pill">{recommendation.priority}</span>
            <h4>{recommendation.intervention.replaceAll("_", " ")}</h4>
            <p>{recommendation.rationale}</p>
            <small>
              Effect: {recommendation.expected_effect} · Burden: {recommendation.burden}
            </small>
          </article>
        ))}
      </div>
    </section>
  );
}
