import json
import asyncio
from openai import AsyncOpenAI, RateLimitError, APIConnectionError, APIError
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from app.config import settings

client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY.get_secret_value())

class JudgeScorer:
    def __init__(self, judge_model: str = settings.JUDGE_MODEL):
        self.model = judge_model
        self.semaphore = asyncio.Semaphore(settings.MAX_CONCURRENT_REQUESTS)

    async def score_single(self, input_data: dict, expected_output: dict, actual_output: dict) -> dict:
        async with self.semaphore:
            prompt = (
                f"You are an impartial expert judge.\n"
                f"Input Data: {json.dumps(input_data)}\n"
                f"Expected Output: {json.dumps(expected_output)}\n"
                f"Actual Output: {json.dumps(actual_output)}\n\n"
                f"Please evaluate the actual output against the expected output.\n"
                f"Return a JSON object with exactly two keys:\n"
                f"- 'relevance_score': an integer from 1 to 5 indicating how well the actual output matches the semantic intent of the expected output (5 is perfect match).\n"
                f"- 'reasoning': a brief sentence explaining the score.\n"
            )

            try:
                @retry(
                    stop=stop_after_attempt(settings.MAX_RETRIES),
                    wait=wait_exponential(multiplier=1, min=2, max=10),
                    retry=retry_if_exception_type((RateLimitError, APIConnectionError, APIError))
                )
                async def _call_judge():
                    return await client.chat.completions.create(
                        model=self.model,
                        messages=[{"role": "user", "content": prompt}],
                        temperature=0.0,
                        response_format={ "type": "json_object" }
                    )
                
                response = await _call_judge()
                
                content = response.choices[0].message.content
                parsed = json.loads(content)
                return {
                    "relevance_score": parsed.get("relevance_score", 1),
                    "reasoning": parsed.get("reasoning", "No reasoning provided")
                }
            except Exception as e:
                return {
                    "relevance_score": 1,
                    "reasoning": f"Judge error: {str(e)}"
                }

    async def score_batch(self, cases: list[dict]) -> list[dict]:
        """
        cases is a list of dicts: {"input": ..., "expected_output": ..., "actual_output": ...}
        """
        tasks = [
            self.score_single(case["input"], case["expected_output"], case["actual_output"])
            for case in cases
        ]
        return await asyncio.gather(*tasks)
