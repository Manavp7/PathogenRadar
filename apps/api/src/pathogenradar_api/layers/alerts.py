from datetime import UTC, datetime

from pathogenradar_api.domain.models import (
    Alert,
    AlertLevel,
    Channel,
    ChannelStatus,
    ExplanationFactor,
    Recommendation,
    RiskAssessment,
)


class AlertingSystem:
    def build_alert(
        self,
        risk_assessment: RiskAssessment,
        reasons: list[ExplanationFactor],
        recommendations: list[Recommendation],
    ) -> Alert | None:
        if risk_assessment.alert_level in {AlertLevel.NORMAL, AlertLevel.WATCH}:
            return None
        return Alert(
            id=f"alert-{risk_assessment.district.id}-{risk_assessment.alert_level.value}",
            district=risk_assessment.district,
            level=risk_assessment.alert_level,
            title=(
                f"{risk_assessment.alert_level.value.title()} for "
                f"{risk_assessment.district.name}"
            ),
            message=(
                f"Demo {risk_assessment.category.value} outbreak intelligence indicates "
                f"{risk_assessment.risk_score:.1f}/100 risk with "
                f"{risk_assessment.confidence:.0%} data confidence."
            ),
            reasons=reasons[:5],
            recommended_actions=recommendations,
            channels=self._channels(risk_assessment.alert_level),
            created_at=datetime.now(UTC),
        )

    def _channels(self, level: AlertLevel) -> list[ChannelStatus]:
        active = level in {AlertLevel.ALERT, AlertLevel.EMERGENCY}
        return [
            ChannelStatus(channel=Channel.API, ready=True, note="Available in demo API"),
            ChannelStatus(channel=Channel.EMAIL, ready=active, note="Production integration required"),
            ChannelStatus(channel=Channel.SMS, ready=False, note="Twilio/telecom integration not configured"),
            ChannelStatus(channel=Channel.WHATSAPP, ready=False, note="WhatsApp Business integration not configured"),
            ChannelStatus(channel=Channel.MOBILE_APP, ready=False, note="Mobile app planned for later roadmap"),
        ]
