import {
  Area,
  AreaChart,
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import type { DistrictForecast, RiskDetail, SeirResult } from "../api/types";
import { fmtInt, shortDate } from "../lib/format";

const AXIS = { stroke: "#5d6b85", fontSize: 11 };
const GRID = "#1b2740";
const TOOLTIP_STYLE = {
  background: "#0e1626",
  border: "1px solid #233149",
  borderRadius: 8,
  fontSize: 12,
};

export function RiskTimeseriesChart({ data }: { data: RiskDetail["timeseries"] }) {
  const series = data.map((d) => ({ date: shortDate(d.date), risk: d.risk_score }));
  return (
    <ResponsiveContainer width="100%" height={220}>
      <AreaChart data={series} margin={{ top: 6, right: 12, left: -18, bottom: 0 }}>
        <defs>
          <linearGradient id="riskFill" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#f0502f" stopOpacity={0.55} />
            <stop offset="100%" stopColor="#f0502f" stopOpacity={0.03} />
          </linearGradient>
        </defs>
        <CartesianGrid stroke={GRID} vertical={false} />
        <XAxis dataKey="date" tick={AXIS} interval={Math.ceil(series.length / 8)} />
        <YAxis tick={AXIS} domain={[0, 100]} />
        <Tooltip contentStyle={TOOLTIP_STYLE} />
        <Area type="monotone" dataKey="risk" stroke="#f0502f" strokeWidth={2} fill="url(#riskFill)" />
      </AreaChart>
    </ResponsiveContainer>
  );
}

export function ForecastChart({ forecast }: { forecast: DistrictForecast }) {
  const data = [
    { h: "Now", p: forecast.current_risk },
    ...forecast.points.map((pt) => ({
      h: `${pt.horizon_days}d`,
      p: Math.round(pt.risk_probability * 100),
    })),
  ];
  return (
    <ResponsiveContainer width="100%" height={220}>
      <LineChart data={data} margin={{ top: 6, right: 12, left: -18, bottom: 0 }}>
        <CartesianGrid stroke={GRID} vertical={false} />
        <XAxis dataKey="h" tick={AXIS} />
        <YAxis tick={AXIS} domain={[0, 100]} unit="%" />
        <Tooltip contentStyle={TOOLTIP_STYLE} formatter={(v) => `${v}%`} />
        <Line type="monotone" dataKey="p" stroke="#2f81f7" strokeWidth={2.5} dot={{ r: 3 }} />
      </LineChart>
    </ResponsiveContainer>
  );
}

export function SeirChart({ result }: { result: SeirResult }) {
  const data = result.baseline.days.map((d, i) => ({
    day: d,
    baseline: result.baseline.infected[i],
    intervention: result.intervention?.infected[i] ?? null,
  }));
  return (
    <ResponsiveContainer width="100%" height={260}>
      <LineChart data={data} margin={{ top: 6, right: 12, left: 6, bottom: 0 }}>
        <CartesianGrid stroke={GRID} vertical={false} />
        <XAxis dataKey="day" tick={AXIS} unit="d" />
        <YAxis tick={AXIS} tickFormatter={(v) => fmtInt(v as number)} width={60} />
        <Tooltip contentStyle={TOOLTIP_STYLE} formatter={(v) => fmtInt(v as number)} />
        <Legend wrapperStyle={{ fontSize: 12 }} />
        <Line
          type="monotone"
          dataKey="baseline"
          name="No action"
          stroke="#f0502f"
          strokeWidth={2}
          dot={false}
        />
        {result.intervention && (
          <Line
            type="monotone"
            dataKey="intervention"
            name="With interventions"
            stroke="#2ea043"
            strokeWidth={2}
            dot={false}
          />
        )}
      </LineChart>
    </ResponsiveContainer>
  );
}

export function SignalSparkline({
  points,
  color = "#2f81f7",
}: {
  points: { date: string; value: number }[];
  color?: string;
}) {
  return (
    <ResponsiveContainer width="100%" height={70}>
      <AreaChart data={points} margin={{ top: 4, right: 0, left: 0, bottom: 0 }}>
        <Area type="monotone" dataKey="value" stroke={color} strokeWidth={1.6} fill={`${color}22`} />
        <Tooltip contentStyle={TOOLTIP_STYLE} labelFormatter={(l) => shortDate(l as string)} />
      </AreaChart>
    </ResponsiveContainer>
  );
}
