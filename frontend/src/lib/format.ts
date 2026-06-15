import type { OutbreakLevel } from "../api/types";

export const LEVEL_COLORS: Record<OutbreakLevel, string> = {
  Normal: "#2ea043",
  Watch: "#d4a017",
  Warning: "#e8830c",
  Alert: "#f0502f",
  Emergency: "#e5184a",
};

/** Continuous colour ramp for a 0..100 risk score (green -> red). */
export function riskColor(risk: number): string {
  if (risk >= 75) return LEVEL_COLORS.Emergency;
  if (risk >= 55) return LEVEL_COLORS.Alert;
  if (risk >= 35) return LEVEL_COLORS.Warning;
  if (risk >= 15) return LEVEL_COLORS.Watch;
  return LEVEL_COLORS.Normal;
}

export function levelForRisk(risk: number): OutbreakLevel {
  if (risk >= 75) return "Emergency";
  if (risk >= 55) return "Alert";
  if (risk >= 35) return "Warning";
  if (risk >= 15) return "Watch";
  return "Normal";
}

export function fmtInt(n: number): string {
  return Math.round(n).toLocaleString("en-IN");
}

export function fmtPct(n: number, digits = 0): string {
  return `${(n * 100).toFixed(digits)}%`;
}

export function shortDate(iso: string): string {
  const d = new Date(iso);
  return d.toLocaleDateString("en-IN", { day: "2-digit", month: "short" });
}
