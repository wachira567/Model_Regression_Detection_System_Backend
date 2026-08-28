from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
from typing import List
from datetime import datetime

from app.db.session import get_db
from app.dependencies import require_role
from app.models.project import Project

router = APIRouter()

class ProjectCreate(BaseModel):
    name: str

class ProjectResponse(BaseModel):
    id: str
    name: str
    created_at: datetime

@router.post("/", response_model=ProjectResponse)
async def create_project(
    request: ProjectCreate,
    user_info = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db)
):
    _, org_id, _ = user_info
    
    project = Project(
        name=request.name,
        organization_id=org_id
    )
    db.add(project)
    await db.commit()
    await db.refresh(project)
    
    return ProjectResponse(
        id=project.id,
        name=project.name,
        created_at=project.created_at
    )

@router.get("/", response_model=List[ProjectResponse])
async def list_projects(
    user_info = Depends(require_role("member")),
    db: AsyncSession = Depends(get_db)
):
    _, org_id, _ = user_info
    
    stmt = select(Project).where(Project.organization_id == org_id).order_by(Project.created_at.desc())
    result = await db.execute(stmt)
    projects = result.scalars().all()
    
    return [
        ProjectResponse(
            id=p.id,
            name=p.name,
            created_at=p.created_at
        ) for p in projects
    ]

@router.delete("/{project_id}")
async def delete_project(
    project_id: str,
    user_info = Depends(require_role("admin")),
    db: AsyncSession = Depends(get_db)
):
    _, org_id, _ = user_info
    
    stmt = select(Project).where(
        Project.id == project_id,
        Project.organization_id == org_id
    )
    res = await db.execute(stmt)
    project = res.scalars().first()
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
        
    await db.delete(project)
    await db.commit()
    
    return {"message": "Project deleted successfully"}
