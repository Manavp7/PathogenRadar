import { useMemo, useState } from "react";
import type { RiskAssessment } from "../api/types";
import { riskColor } from "../lib/format";

interface Props {
  geojson: GeoJSON.FeatureCollection;
  risk: RiskAssessment[];
  selected?: string | null;
  onSelect?: (districtId: string) => void;
}

const VB_W = 560;
const VB_H = 620;
const PAD = 36;

type Ring = [number, number][];

interface Shape {
  id: string;
  name: string;
  rings: Ring[];
  centroid: [number, number];
  risk: number;
  level: string;
  category: string;
}

/**
 * Dependency-free SVG choropleth. No external map tiles, no WebGL — fully offline and
 * deterministic, which suits a government-grade, data-sovereign deployment.
 */
export default function MapChoropleth({ geojson, risk, selected, onSelect }: Props) {
  const [hover, setHover] = useState<{ s: Shape; x: number; y: number } | null>(null);

  const { shapes } = useMemo(() => buildShapes(geojson, risk), [geojson, risk]);

  return (
    <div className="map-wrap" style={{ background: "#0a0e17" }}>
      <svg
        viewBox={`0 0 ${VB_W} ${VB_H}`}
        width="100%"
        height="100%"
        style={{ display: "block" }}
        onMouseLeave={() => setHover(null)}
      >
        {shapes.map((s) => {
          const d = s.rings.map(ringToPath).join(" ");
          const isSel = selected === s.id;
          return (
            <path
              key={s.id}
              d={d}
              fill={riskColor(s.risk)}
              fillOpacity={0.82}
              stroke={isSel ? "#ffffff" : "#0a0e17"}
              strokeWidth={isSel ? 2.2 : 0.9}
              style={{ cursor: "pointer", transition: "fill 0.3s" }}
              onMouseMove={(e) => {
                const rect = (e.currentTarget.ownerSVGElement as SVGSVGElement).getBoundingClientRect();
                setHover({
                  s,
                  x: ((e.clientX - rect.left) / rect.width) * VB_W,
                  y: ((e.clientY - rect.top) / rect.height) * VB_H,
                });
              }}
              onClick={() => onSelect?.(s.id)}
            />
          );
        })}
        {shapes.map((s) => (
          <text
            key={`l-${s.id}`}
            x={s.centroid[0]}
            y={s.centroid[1]}
            fontSize={9}
            fill="#e7edf7"
            stroke="#0a0e17"
            strokeWidth={2}
            paintOrder="stroke"
            textAnchor="middle"
            style={{ pointerEvents: "none", fontWeight: 600 }}
          >
            {s.name}
          </text>
        ))}
        {hover && (
          <g pointerEvents="none">
            <rect
              x={Math.min(hover.x + 8, VB_W - 168)}
              y={Math.max(hover.y - 46, 4)}
              width={160}
              height={42}
              rx={6}
              fill="#0e1626"
              stroke="#233149"
            />
            <text x={Math.min(hover.x + 16, VB_W - 160)} y={Math.max(hover.y - 30, 20)} fontSize={11} fill="#e7edf7" fontWeight={700}>
              {hover.s.name}
            </text>
            <text x={Math.min(hover.x + 16, VB_W - 160)} y={Math.max(hover.y - 16, 34)} fontSize={10} fill="#93a2bd">
              Risk {hover.s.risk.toFixed(0)}/100 · {hover.s.level}
              {hover.s.level !== "Normal" ? ` · ${hover.s.category}` : ""}
            </text>
          </g>
        )}
      </svg>
      <div className="legend">
        <div style={{ marginBottom: 6, color: "#93a2bd" }}>Outbreak risk</div>
        {[
          ["Emergency", "#e5184a"],
          ["Alert", "#f0502f"],
          ["Warning", "#e8830c"],
          ["Watch", "#d4a017"],
          ["Normal", "#2ea043"],
        ].map(([label, color]) => (
          <div className="row" key={label}>
            <span className="sw" style={{ background: color }} />
            {label}
          </div>
        ))}
      </div>
    </div>
  );
}

function ringToPath(ring: Ring): string {
  return ring.map((p, i) => `${i === 0 ? "M" : "L"}${p[0].toFixed(1)} ${p[1].toFixed(1)}`).join(" ") + "Z";
}

function buildShapes(geojson: GeoJSON.FeatureCollection, risk: RiskAssessment[]) {
  // Bounding box in lon/lat.
  let minLon = Infinity,
    maxLon = -Infinity,
    minLat = Infinity,
    maxLat = -Infinity;
  const eachCoord = (coords: GeoJSON.Position[]) =>
    coords.forEach(([lon, lat]) => {
      minLon = Math.min(minLon, lon);
      maxLon = Math.max(maxLon, lon);
      minLat = Math.min(minLat, lat);
      maxLat = Math.max(maxLat, lat);
    });
  for (const f of geojson.features) forEachRing(f.geometry, eachCoord);

  const midLat = ((minLat + maxLat) / 2) * (Math.PI / 180);
  const cosLat = Math.cos(midLat);
  const spanLon = (maxLon - minLon) * cosLat;
  const spanLat = maxLat - minLat;
  const scale = Math.min((VB_W - 2 * PAD) / spanLon, (VB_H - 2 * PAD) / spanLat);
  const drawnW = spanLon * scale;
  const drawnH = spanLat * scale;
  const offX = (VB_W - drawnW) / 2;
  const offY = (VB_H - drawnH) / 2;

  const project = ([lon, lat]: GeoJSON.Position): [number, number] => [
    offX + (lon - minLon) * cosLat * scale,
    offY + (maxLat - lat) * scale,
  ];

  const riskById = new Map(risk.map((r) => [r.district_id, r]));
  const shapes: Shape[] = geojson.features.map((f) => {
    const id = (f.properties?.district_id as string) ?? "";
    const r = riskById.get(id);
    const rings: Ring[] = [];
    forEachRing(f.geometry, (coords) => rings.push(coords.map(project)));
    // Centroid from the largest ring.
    const largest = rings.reduce((a, b) => (b.length > a.length ? b : a), rings[0] ?? []);
    const cx = largest.reduce((s, p) => s + p[0], 0) / Math.max(largest.length, 1);
    const cy = largest.reduce((s, p) => s + p[1], 0) / Math.max(largest.length, 1);
    return {
      id,
      name: (f.properties?.DISTRICT as string) ?? id,
      rings,
      centroid: [cx, cy],
      risk: r?.risk_score ?? 0,
      level: r?.level ?? "Normal",
      category: r?.category ?? "—",
    };
  });
  return { shapes };
}

function forEachRing(geom: GeoJSON.Geometry, cb: (ring: GeoJSON.Position[]) => void) {
  if (geom.type === "Polygon") geom.coordinates.forEach(cb);
  else if (geom.type === "MultiPolygon") geom.coordinates.forEach((poly) => poly.forEach(cb));
}
