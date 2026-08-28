import json
import time
import asyncio
from typing import Any
import openai
from openai import AsyncOpenAI, RateLimitError, APIConnectionError, APIError
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from app.config import settings

client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY.get_secret_value())

class LLMRunner:
    def __init__(self, model: str, temperature: float = 0.0, max_tokens: int = 256, system_prompt: str = "", max_concurrent: int = 10):
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.system_prompt = system_prompt
        self.semaphore = asyncio.Semaphore(max_concurrent)

    async def run_single(self, input_data: dict, few_shot_examples: list = []) -> dict:
        async with self.semaphore:
            messages = []
            if self.system_prompt:
                messages.append({"role": "system", "content": self.system_prompt})
            
            for ex in few_shot_examples:
                messages.append({"role": "user", "content": json.dumps(ex.get("input", {}))})
                messages.append({"role": "assistant", "content": json.dumps(ex.get("output", {}))})
                
            messages.append({"role": "user", "content": json.dumps(input_data)})

            start_time = time.time()
            try:
                @retry(
                    stop=stop_after_attempt(settings.MAX_RETRIES),
                    wait=wait_exponential(multiplier=1, min=2, max=10),
                    retry=retry_if_exception_type((RateLimitError, APIConnectionError, APIError))
                )
                async def _call_openai():
                    return await client.chat.completions.create(
                        model=self.model,
                        messages=messages,
                        temperature=self.temperature,
                        max_tokens=self.max_tokens,
                        response_format={ "type": "json_object" }
                    )
                
                response = await _call_openai()
                
                content = response.choices[0].message.content
                latency_ms = (time.time() - start_time) * 1000
                prompt_tokens = response.usage.prompt_tokens if response.usage else 0
                completion_tokens = response.usage.completion_tokens if response.usage else 0
                
                try:
                    parsed_content = json.loads(content)
                except json.JSONDecodeError:
                    parsed_content = {"error": "Invalid JSON generated", "raw": content}

                return {
                    "status": "success",
                    "output": parsed_content,
                    "latency_ms": latency_ms,
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": completion_tokens
                }

            except Exception as e:
                latency_ms = (time.time() - start_time) * 1000
                return {
                    "status": "error",
                    "error_message": str(e),
                    "latency_ms": latency_ms,
                    "prompt_tokens": 0,
                    "completion_tokens": 0
                }

    async def run_batch(self, inputs: list[dict], few_shot_examples: list = []) -> list[dict]:
        tasks = [self.run_single(inp, few_shot_examples) for inp in inputs]
        return await asyncio.gather(*tasks)
