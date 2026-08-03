import httpx
import logging
from app.config import settings
from app.services.diff_engine import DiffReport

logger = logging.getLogger(__name__)

class GitHubCommenter:
    def __init__(self):
        self.github_token = settings.GITHUB_TOKEN.get_secret_value() if settings.GITHUB_TOKEN else None
        
    async def post_pr_comment(self, repo_full_name: str, pr_number: int, report: DiffReport):
        if not self.github_token:
            logger.info("GitHub token not configured. Skipping PR comment.")
            return

        url = f"https://api.github.com/repos/{repo_full_name}/issues/{pr_number}/comments"
        headers = {
            "Authorization": f"token {self.github_token}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        emoji = "🔴" if report.severity == "critical" else "🟠" if report.severity == "warning" else "🟢"
        body = f"### {emoji} Model Eval Run Complete\n\n"
        body += f"**Severity**: {report.severity.upper()}\n"
        body += f"**Summary**: {report.summary_text}\n\n"
        
        body += "#### Overall Deltas\n"
        body += f"- **Accuracy**: {(report.overall_delta.accuracy_delta * 100):.2f}%\n"
        body += f"- **Relevance**: {report.overall_delta.relevance_delta:.2f}\n"
        body += f"- **Latency**: {report.overall_delta.latency_delta:.0f} ms\n\n"
        
        if report.regressions:
            body += "#### 🚨 Top Regressions\n"
            for r in report.regressions[:5]:
                body += f"- `{r.test_case_id}`: {r.reason}\n"
                
            if len(report.regressions) > 5:
                body += f"\n*...and {len(report.regressions) - 5} more regressions.*\n"
                
        body += "\n[View Full Report in Dashboard](https://mr-detection.example.com/eval-runs/" + report.current_run_id + ")"
        
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.post(url, headers=headers, json={"body": body})
                resp.raise_for_status()
                logger.info(f"Posted comment to PR #{pr_number} in {repo_full_name}")
        except Exception as e:
            logger.error(f"Failed to post GitHub PR comment: {e}")
