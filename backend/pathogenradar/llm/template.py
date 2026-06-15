"""Deterministic, offline briefing provider (the default).

Produces a clean 1-page Markdown briefing with zero external dependencies.
"""

from __future__ import annotations

from .base import BriefingContext, BriefingProvider


class TemplateBriefingProvider(BriefingProvider):
    name = "template"

    def render(self, context: BriefingContext) -> str:
        lines: list[str] = []
        lines.append(f"# {context.region} Health Intelligence Briefing")
        lines.append(f"_As of {context.as_of.isoformat()} • prepared by PathogenRadar_")
        lines.append("")

        # Executive summary
        if context.districts_on_alert == 0:
            lines.append(
                "## Executive Summary\n"
                f"No districts currently exceed alert thresholds across {context.total_districts} "
                "monitored districts. Surveillance signals are within expected ranges."
            )
        else:
            top = context.top_districts[0] if context.top_districts else None
            lead = ""
            if top:
                lead = (
                    f" The highest concern is **{top['name']}** "
                    f"({top['level']}, risk {top['risk']:.0f}/100"
                    + (f", likely {top['category'].lower()}" if top.get("category") else "")
                    + ")."
                )
            lines.append(
                "## Executive Summary\n"
                f"**{context.districts_on_alert}** of {context.total_districts} districts are "
                f"showing elevated outbreak risk.{lead}"
            )
        lines.append("")

        # Districts of concern
        if context.top_districts:
            lines.append("## Districts of Concern")
            for d in context.top_districts:
                diseases = ", ".join(d.get("diseases", [])[:3])
                disease_str = f" — likely: {diseases}" if diseases else ""
                lines.append(
                    f"- **{d['name']}** — {d['level']}, risk {d['risk']:.0f}/100"
                    f"{(' (' + d['category'] + ')') if d.get('category') else ''}{disease_str}"
                )
            lines.append("")

        # Spread outlook
        if context.forecast_highlights:
            lines.append("## 30-Day Spread Outlook")
            lines.append(
                "Districts most likely to see rising risk from current hotspots "
                "(network-diffusion forecast):"
            )
            for f in context.forecast_highlights:
                lines.append(
                    f"- **{f['name']}** — {f['prob_30d'] * 100:.0f}% probability by day 30"
                )
            lines.append("")

        # Recommended actions
        if context.recommended_actions:
            lines.append("## Recommended Actions")
            for i, action in enumerate(context.recommended_actions, 1):
                lines.append(f"{i}. {action}")
            lines.append("")

        # Data provenance
        if context.data_sources:
            srcs = ", ".join(f"{k} ({v})" for k, v in context.data_sources.items())
            lines.append(f"## Data Sources\n{srcs}")
            lines.append("")

        lines.append(
            "_This briefing is generated from statistical/ML surveillance models. "
            "It supports — and does not replace — expert epidemiological judgement._"
        )
        return "\n".join(lines)
