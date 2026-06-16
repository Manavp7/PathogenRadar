import { useEffect, useRef, useState } from "react";
import { api } from "../api/client";
import type { Timeline } from "../api/types";
import { riskColor, shortDate } from "../lib/format";
import { useRegion } from "../lib/region";

/**
 * Scrub / animate through historical risk snapshots. Emits the selected date, or null when
 * viewing the latest ("live") snapshot.
 */
export default function TimeMachine({ onChange }: { onChange: (date: string | null) => void }) {
  const region = useRegion();
  const [timeline, setTimeline] = useState<Timeline | null>(null);
  const [idx, setIdx] = useState(0);
  const [playing, setPlaying] = useState(false);
  const timer = useRef<number | null>(null);

  useEffect(() => {
    api
      .timeline(region)
      .then((t) => {
        setTimeline(t);
        setIdx(t.dates.length - 1);
      })
      .catch(() => setTimeline(null));
  }, [region]);

  useEffect(() => {
    if (!playing || !timeline) return;
    timer.current = window.setInterval(() => {
      setIdx((i) => {
        if (i >= timeline.dates.length - 1) {
          setPlaying(false);
          return i;
        }
        return i + 1;
      });
    }, 250);
    return () => {
      if (timer.current) window.clearInterval(timer.current);
    };
  }, [playing, timeline]);

  useEffect(() => {
    if (!timeline) return;
    const isLatest = idx >= timeline.dates.length - 1;
    onChange(isLatest ? null : timeline.dates[idx]);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [idx, timeline]);

  if (!timeline || timeline.dates.length === 0) return null;
  const isLatest = idx >= timeline.dates.length - 1;
  const point = timeline.series[idx];

  return (
    <div className="panel" aria-label="Time machine">
      <div style={{ display: "flex", alignItems: "center", gap: 14, flexWrap: "wrap" }}>
        <button
          className="btn"
          onClick={() => {
            if (idx >= timeline.dates.length - 1) setIdx(0);
            setPlaying((p) => !p);
          }}
          aria-label={playing ? "Pause animation" : "Play outbreak animation"}
        >
          {playing ? "❚❚ Pause" : "▶ Play"}
        </button>
        <div style={{ minWidth: 132 }}>
          <div style={{ fontSize: 18, fontWeight: 700 }}>
            {shortDate(timeline.dates[idx])}{" "}
            {isLatest && <span className="chip" style={{ marginLeft: 6 }}>LIVE</span>}
          </div>
          <div className="faint" style={{ fontSize: 11 }}>
            national peak risk{" "}
            <b style={{ color: riskColor(point?.max ?? 0) }}>{(point?.max ?? 0).toFixed(0)}</b>
          </div>
        </div>
        <input
          type="range"
          min={0}
          max={timeline.dates.length - 1}
          value={idx}
          onChange={(e) => {
            setPlaying(false);
            setIdx(parseInt(e.target.value, 10));
          }}
          style={{ flex: 1, minWidth: 200 }}
          aria-label="Select date"
        />
        {!isLatest && (
          <button className="btn secondary" onClick={() => setIdx(timeline.dates.length - 1)}>
            Jump to live
          </button>
        )}
      </div>
    </div>
  );
}
