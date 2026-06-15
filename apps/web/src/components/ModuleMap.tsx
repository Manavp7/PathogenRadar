const modules = [
  ["Data Acquisition", "demo connectors"],
  ["Data Quality", "implemented"],
  ["Disease Knowledge Graph", "JSON graph"],
  ["Signal Intelligence", "baseline encoders"],
  ["Fusion Transformer", "weighted fusion placeholder"],
  ["Outbreak Detection", "threshold classifier"],
  ["Novel Pathogen", "novelty placeholder"],
  ["Spread Forecast", "mobility graph"],
  ["Simulator", "SEIR-style"],
  ["RL Decision", "rule policy"],
  ["Explainability", "source drivers"],
  ["LLM Intelligence", "reports only"],
  ["Dashboard", "prototype"],
  ["Alerts", "payloads"],
  ["Public API", "FastAPI"],
  ["Mobile App", "roadmap"],
  ["Security", "RBAC scaffold"],
  ["MLOps", "roadmap"],
  ["Research Mode", "safe demo queries"]
];

export function ModuleMap() {
  return (
    <section className="panel module-map">
      <div className="panel-heading">
        <span>19-module company roadmap</span>
        <small>What exists vs. what plugs in later</small>
      </div>
      <div className="module-grid">
        {modules.map(([name, status], index) => (
          <div className="module-card" key={name}>
            <b>{index + 1}</b>
            <strong>{name}</strong>
            <span>{status}</span>
          </div>
        ))}
      </div>
    </section>
  );
}
