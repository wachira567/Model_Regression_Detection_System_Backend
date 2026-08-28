import asyncio
import argparse
import sys
import os
import httpx
import logging

# Ensure we can import from app
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.services.diff_engine import DiffReport, OverallDelta, CaseDiff
from app.services.github_commenter import GitHubCommenter

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def run_eval(api_url: str, feature_id: str, api_key: str, repo: str, pr_number: int):
    logger.info(f"Triggering eval run for {feature_id} at {api_url}")
    
    headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}
    baseline_id = None
    
    async with httpx.AsyncClient() as client:
        try:
            # 1. Fetch latest completed run for baseline
            runs_resp = await client.get(f"{api_url}/api/v1/eval-runs?size=10", headers=headers)
            if runs_resp.status_code == 200:
                runs_data = runs_resp.json().get("items", [])
                completed_runs = [r for r in runs_data if r.get("status") == "completed"]
                if completed_runs:
                    baseline_id = completed_runs[0].get("id")
                    logger.info(f"Found baseline run: {baseline_id}")
            
            # 2. Trigger new run
            resp = await client.post(f"{api_url}/api/v1/eval/run/{feature_id}", headers=headers)
            resp.raise_for_status()
            data = resp.json()
            run_id = data.get("eval_run_id")
            logger.info(f"Successfully triggered eval run: {run_id}")
            
            # 3. Poll for completion
            while True:
                await asyncio.sleep(5)
                status_resp = await client.get(f"{api_url}/api/v1/eval-runs/{run_id}", headers=headers)
                status_resp.raise_for_status()
                status_data = status_resp.json()
                
                status = status_data.get("status")
                logger.info(f"Eval run {run_id} status: {status}")
                
                if status == "completed":
                    logger.info("Eval run finished successfully.")
                    break
                elif status == "failed":
                    logger.error(f"Eval run failed: {status_data.get('error_message')}")
                    sys.exit(1)
            
            # 4. Fetch diff if baseline exists
            if baseline_id:
                logger.info(f"Fetching diff between {run_id} and {baseline_id}")
                diff_resp = await client.get(f"{api_url}/api/v1/eval-runs/{run_id}/diff/{baseline_id}", headers=headers)
                diff_resp.raise_for_status()
                diff_json = diff_resp.json()
                
                # Reconstruct DiffReport
                overall = OverallDelta(**diff_json.get("overall_delta", {}))
                
                regressions = [CaseDiff(**c) for c in diff_json.get("regressions", [])]
                improvements = [CaseDiff(**c) for c in diff_json.get("improvements", [])]
                new_failures = [CaseDiff(**c) for c in diff_json.get("new_failures", [])]
                
                report = DiffReport(
                    current_run_id=diff_json.get("current_run_id", run_id),
                    baseline_run_id=diff_json.get("baseline_run_id", baseline_id),
                    overall_delta=overall,
                    regressions=regressions,
                    improvements=improvements,
                    new_failures=new_failures,
                    stable_passes=diff_json.get("stable_passes", []),
                    stable_failures=diff_json.get("stable_failures", []),
                    severity=diff_json.get("severity", "pass"),
                    summary_text=diff_json.get("summary_text", "")
                )
                
                # 5. Run GitHubCommenter
                if repo and pr_number:
                    commenter = GitHubCommenter()
                    await commenter.post_pr_comment(repo, pr_number, report)
                else:
                    logger.info("Skipping GitHub PR comment (repo or pr_number missing).")
                
                # 6. Exit code
                if report.severity == "critical":
                    logger.error("Critical regressions detected. Blocking PR.")
                    sys.exit(1)
            else:
                logger.info("No baseline found. Cannot compute diff or regressions.")
                    
        except Exception as e:
            logger.error(f"Failed to execute eval: {e}")
            sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="Trigger an eval run from CLI")
    parser.add_argument("--api-url", default="http://localhost:8000", help="Base URL of the Eval API")
    parser.add_argument("--feature-id", required=True, help="Feature ID to evaluate")
    parser.add_argument("--api-key", default=os.getenv("EVAL_API_KEY", ""), help="API Key for authentication")
    parser.add_argument("--repo", default=os.getenv("GITHUB_REPOSITORY", ""), help="GitHub Repo (e.g. owner/repo)")
    parser.add_argument("--pr-number", type=int, default=int(os.getenv("PR_NUMBER", "0") or 0), help="Pull Request Number")
    
    args = parser.parse_args()
    
    asyncio.run(run_eval(args.api_url, args.feature_id, args.api_key, args.repo, args.pr_number))

if __name__ == "__main__":
    main()
