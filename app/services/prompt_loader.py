import yaml
from pathlib import Path
from pydantic import BaseModel, Field

class PromptExample(BaseModel):
    input: str | dict
    output: str | dict

class PromptSchema(BaseModel):
    type: str
    properties: dict
    required: list[str] = []

class PromptConfigData(BaseModel):
    id: str
    version: str
    created_at: str
    author: str
    description: str
    model: str
    temperature: float = 0.0
    max_tokens: int = 256
    system_prompt: str
    few_shot_examples: list[PromptExample] = []
    input_schema: PromptSchema | None = None
    output_schema: PromptSchema | None = None

class PromptLoader:
    def __init__(self, prompts_dir: str):
        self.prompts_dir = Path(prompts_dir)

    def load_all(self) -> list[PromptConfigData]:
        configs = []
        if not self.prompts_dir.exists():
            return configs
        
        for file in self.prompts_dir.glob("*.yaml"):
            with open(file, "r") as f:
                data = yaml.safe_load(f)
                configs.append(PromptConfigData(**data))
        return configs
