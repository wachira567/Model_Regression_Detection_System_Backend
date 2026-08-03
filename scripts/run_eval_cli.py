import asyncio
import argparse
import sys
import os
import httpx
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def run_eval(api_url: str, feature_id: str, api_key: str):
    logger.info(f"Triggering eval run for {feature_id} at {api_url}")
    
    headers = {"Authorization": f"Bearer {api_key}"} if api_key else {}
    
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(f"{api_url}/api/v1/eval/run/{feature_id}", headers=headers)
            resp.raise_for_status()
            data = resp.json()
            run_id = data.get("eval_run_id")
            logger.info(f"Successfully triggered eval run: {run_id}")
            
            # Poll for completion
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
                    
        except Exception as e:
            logger.error(f"Failed to execute eval: {e}")
            sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="Trigger an eval run from CLI")
    parser.add_argument("--api-url", default="http://localhost:8000", help="Base URL of the Eval API")
    parser.add_argument("--feature-id", required=True, help="Feature ID to evaluate")
    parser.add_argument("--api-key", default=os.getenv("EVAL_API_KEY", ""), help="API Key for authentication")
    
    args = parser.parse_args()
    
    asyncio.run(run_eval(args.api_url, args.feature_id, args.api_key))

if __name__ == "__main__":
    main()
