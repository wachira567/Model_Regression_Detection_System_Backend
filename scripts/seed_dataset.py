import asyncio
import logging
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import AsyncSessionLocal
from app.models.prompt_config import PromptConfig
from app.services.prompt_loader import PromptLoader
from app.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def seed_prompts():
    loader = PromptLoader(settings.PROMPTS_DIR)
    configs = loader.load_all()
    
    async with AsyncSessionLocal() as session:
        for config_data in configs:
            # Check if exists
            logger.info(f"Seeding prompt config for {config_data.id} (version: {config_data.version})")
            
            prompt_config = PromptConfig(
                feature_id=config_data.id,
                version=config_data.version,
                yaml_content=config_data.model_dump_json(), # Store full JSON dump or yaml content
                model=config_data.model,
                temperature=config_data.temperature,
                is_active=True
            )
            session.add(prompt_config)
            
        await session.commit()
        logger.info("Successfully seeded prompts.")

async def main():
    logger.info("Starting database seed...")
    await seed_prompts()
    logger.info("Database seeding complete.")

if __name__ == "__main__":
    asyncio.run(main())
