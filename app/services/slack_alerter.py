import httpx
import logging
from app.config import settings
from app.services.diff_engine import DiffReport

logger = logging.getLogger(__name__)

class SlackAlerter:
    def __init__(self):
        self.webhook_url = settings.SLACK_WEBHOOK_URL.get_secret_value() if settings.SLACK_WEBHOOK_URL else None

    async def send_diff_alert(self, diff_report: DiffReport, feature_id: str):
        if not self.webhook_url:
            logger.info("Slack webhook URL not configured. Skipping alert.")
            return

        # Build Slack Block Kit message
        emoji = "🚨" if diff_report.severity == "critical" else "⚠️" if diff_report.severity == "warning" else "✅"
        
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"{emoji} Eval Run Complete: {feature_id}"
                }
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Severity:* {diff_report.severity.upper()}\n*Summary:* {diff_report.summary_text}"
                }
            },
            {
                "type": "section",
                "fields": [
                    {
                        "type": "mrkdwn",
                        "text": f"*Accuracy Delta:*\n{diff_report.overall_delta.accuracy_delta * 100:.2f}%"
                    },
                    {
                        "type": "mrkdwn",
                        "text": f"*Relevance Delta:*\n{diff_report.overall_delta.relevance_delta:.2f}"
                    }
                ]
            }
        ]
        
        if diff_report.regressions:
            reg_text = "\n".join([f"• {r.test_case_id}: {r.reason}" for r in diff_report.regressions[:5]])
            if len(diff_report.regressions) > 5:
                reg_text += f"\n...and {len(diff_report.regressions) - 5} more."
                
            blocks.append({
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": f"*Top Regressions:*\n{reg_text}"
                }
            })

        payload = {"blocks": blocks}
        
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(self.webhook_url, json=payload)
                resp.raise_for_status()
                logger.info(f"Slack alert sent for {feature_id}")
        except Exception as e:
            logger.error(f"Failed to send Slack alert: {e}")
