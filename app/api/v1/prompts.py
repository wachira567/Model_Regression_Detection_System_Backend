from fastapi import APIRouter
from app.services.prompt_loader import PromptLoader, PromptConfigData
from app.config import settings

router = APIRouter()
prompt_loader = PromptLoader(settings.PROMPTS_DIR)

@router.get("/", response_model=list[PromptConfigData])
async def list_prompts():
    return prompt_loader.load_all()

@router.get("/{feature_id}", response_model=list[PromptConfigData])
async def get_prompts_for_feature(feature_id: str):
    prompts = prompt_loader.load_all()
    return [p for p in prompts if p.id == feature_id]
