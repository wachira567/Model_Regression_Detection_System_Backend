import random
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
import uuid

from app.db.session import get_db
from app.models.feature_flag import FeatureFlag
from app.dependencies import get_current_org

router = APIRouter(prefix="/flags", tags=["Feature Flags"])

class FlagCreate(BaseModel):
    name: str
    feature_id: str
    baseline_config_id: str
    experimental_config_id: str
    rollout_percentage: int = 0

class FlagUpdate(BaseModel):
    is_enabled: bool = None
    rollout_percentage: int = None

@router.get("/")
async def list_flags(db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(FeatureFlag))
    flags = result.scalars().all()
    return flags

@router.post("/")
async def create_flag(flag: FlagCreate, db: AsyncSession = Depends(get_db)):
    new_flag = FeatureFlag(
        organization_id="default_org",
        name=flag.name,
        feature_id=flag.feature_id,
        baseline_config_id=uuid.UUID(flag.baseline_config_id),
        experimental_config_id=uuid.UUID(flag.experimental_config_id),
        rollout_percentage=flag.rollout_percentage
    )
    db.add(new_flag)
    await db.commit()
    return {"status": "success", "flag_id": str(new_flag.id)}

@router.put("/{flag_id}")
async def update_flag(flag_id: str, flag_update: FlagUpdate, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(FeatureFlag).where(FeatureFlag.id == uuid.UUID(flag_id)))
    flag = result.scalar_one_or_none()
    
    if not flag:
        raise HTTPException(status_code=404, detail="Flag not found")
        
    if flag_update.is_enabled is not None:
        flag.is_enabled = flag_update.is_enabled
        
    if flag_update.rollout_percentage is not None:
        if 0 <= flag_update.rollout_percentage <= 100:
            flag.rollout_percentage = flag_update.rollout_percentage
        else:
            raise HTTPException(status_code=400, detail="Percentage must be between 0 and 100")
            
    await db.commit()
    return {"status": "success"}

@router.get("/evaluate/{feature_id}")
async def evaluate_flag(feature_id: str, db: AsyncSession = Depends(get_db)):
    """
    Called by SDK to determine which prompt config to use for a given feature.
    """
    result = await db.execute(select(FeatureFlag).where(FeatureFlag.feature_id == feature_id))
    flag = result.scalar_one_or_none()
    
    if not flag or not flag.is_enabled:
        return {"status": "default", "message": "No active flag found"}
        
    # Gradual rollout logic
    rand_val = random.randint(1, 100)
    if rand_val <= flag.rollout_percentage:
        return {"status": "experimental", "config_id": str(flag.experimental_config_id)}
    else:
        return {"status": "baseline", "config_id": str(flag.baseline_config_id)}
