import { useEffect, useRef } from "react";
import maplibregl from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";
import type { RiskAssessment } from "../api/types";
import { riskColor } from "../lib/format";

interface Props {
  geojson: GeoJSON.FeatureCollection;
  risk: RiskAssessment[];
  selected?: string | null;
  onSelect?: (districtId: string) => void;
}

const EMPTY_STYLE: maplibregl.StyleSpecification = {
  version: 8,
  sources: {},
  layers: [{ id: "bg", type: "background", paint: { "background-color": "#0a0e17" } }],
  glyphs: "https://demotiles.maplibre.org/font/{fontstack}/{range}.pbf",
};

export default function MapChoropleth({ geojson, risk, selected, onSelect }: Props) {
  const container = useRef<HTMLDivElement>(null);
  const map = useRef<maplibregl.Map | null>(null);
  const riskRef = useRef(risk);
  riskRef.current = risk;

  // Merge risk into geojson features for data-driven styling.
  const enriched: GeoJSON.FeatureCollection = {
    type: "FeatureCollection",
    features: geojson.features.map((f) => {
      const id = (f.properties?.district_id as string) ?? "";
      const r = risk.find((x) => x.district_id === id);
      return {
        ...f,
        properties: {
          ...f.properties,
          risk: r?.risk_score ?? 0,
          level: r?.level ?? "Normal",
          color: riskColor(r?.risk_score ?? 0),
          category: r?.category ?? "—",
        },
      };
    }),
  };

  useEffect(() => {
    if (!container.current || map.current) return;
    const m = new maplibregl.Map({
      container: container.current,
      style: EMPTY_STYLE,
      center: [76.2, 10.4],
      zoom: 6.4,
      attributionControl: false,
    });
    map.current = m;
    m.addControl(new maplibregl.NavigationControl({ showCompass: false }), "top-right");

    m.on("load", () => {
      m.addSource("districts", { type: "geojson", data: enriched });
      m.addLayer({
        id: "fill",
        type: "fill",
        source: "districts",
        paint: { "fill-color": ["get", "color"], "fill-opacity": 0.72 },
      });
      m.addLayer({
        id: "outline",
        type: "line",
        source: "districts",
        paint: { "line-color": "#0a0e17", "line-width": 1.2 },
      });
      m.addLayer({
        id: "highlight",
        type: "line",
        source: "districts",
        paint: { "line-color": "#ffffff", "line-width": 2.4 },
        filter: ["==", ["get", "district_id"], selected ?? "___none___"],
      });
      m.addLayer({
        id: "labels",
        type: "symbol",
        source: "districts",
        layout: {
          "text-field": ["get", "DISTRICT"],
          "text-size": 11,
          "text-font": ["Open Sans Regular"],
        },
        paint: {
          "text-color": "#e7edf7",
          "text-halo-color": "#0a0e17",
          "text-halo-width": 1.3,
        },
      });

      const popup = new maplibregl.Popup({ closeButton: false, closeOnClick: false });
      m.on("mousemove", "fill", (e) => {
        m.getCanvas().style.cursor = "pointer";
        const f = e.features?.[0];
        if (!f) return;
        const p = f.properties as Record<string, unknown>;
        popup
          .setLngLat(e.lngLat)
          .setHTML(
            `<b>${p.DISTRICT}</b><br/>Risk ${Number(p.risk).toFixed(0)}/100 · ${p.level}<br/>` +
              `<span style="color:#93a2bd">${p.category}</span>`
          )
          .addTo(m);
      });
      m.on("mouseleave", "fill", () => {
        m.getCanvas().style.cursor = "";
        popup.remove();
      });
      m.on("click", "fill", (e) => {
        const id = e.features?.[0]?.properties?.district_id as string | undefined;
        if (id && onSelect) onSelect(id);
      });

      try {
        const b = new maplibregl.LngLatBounds();
        enriched.features.forEach((feat) => addBounds(b, feat.geometry));
        m.fitBounds(b, { padding: 40, duration: 0 });
      } catch {
        /* ignore */
      }
    });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Update data when risk changes.
  useEffect(() => {
    const m = map.current;
    if (!m || !m.isStyleLoaded()) return;
    const src = m.getSource("districts") as maplibregl.GeoJSONSource | undefined;
    if (src) src.setData(enriched);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [risk]);

  // Update highlight when selection changes.
  useEffect(() => {
    const m = map.current;
    if (!m || !m.getLayer("highlight")) return;
    m.setFilter("highlight", ["==", ["get", "district_id"], selected ?? "___none___"]);
  }, [selected]);

  return (
    <div className="map-wrap">
      <div ref={container} style={{ width: "100%", height: "100%" }} />
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

function addBounds(b: maplibregl.LngLatBounds, geom: GeoJSON.Geometry) {
  const each = (coords: GeoJSON.Position[]) => coords.forEach((c) => b.extend(c as [number, number]));
  if (geom.type === "Polygon") geom.coordinates.forEach(each);
  else if (geom.type === "MultiPolygon") geom.coordinates.forEach((p) => p.forEach(each));
}
