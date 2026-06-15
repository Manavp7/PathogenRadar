import type { SpreadForecast } from "../types";

export function ForecastTimeline({ forecast }: { forecast: SpreadForecast }) {
  return (
    <section className="panel">
      <div className="panel-heading">
        <span>Spread forecast</span>
        <small>Mobility-graph propagation</small>
      </div>
      <div className="timeline">
        {forecast.points.map((point) => {
          const top = Object.entries(point.district_probabilities).sort((a, b) => b[1] - a[1])[0];
          return (
            <div className="timeline-card" key={point.horizon_days}>
              <strong>{point.horizon_days} days</strong>
              <b>{Math.round(top[1] * 100)}%</b>
              <span>{top[0]}</span>
              <em>{Math.round(point.confidence * 100)}% confidence</em>
            </div>
          );
        })}
      </div>
    </section>
  );
}
