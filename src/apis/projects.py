from fastapi import APIRouter, Body, HTTPException
import secrets
from ..config import db

router = APIRouter()


@router.post("/projects")
async def create_project(payload: dict = Body(...)):
    """Create a new project with an API key."""
    clerk_user_id = payload.get("clerk_user_id")
    name = payload.get("name", "Untitled Project")
    description = payload.get("description")
    
    # Check if user exists, create if not (webhook may not have fired yet)
    user = await db.user.upsert(
        where={"clerkUserId": clerk_user_id},
        data={
            "create": {
                "clerkUserId": clerk_user_id,
                "email": f"{clerk_user_id}@temp.monomind"  # Temporary, webhook will update
            },
            "update": {}
        }
    )
    
    # Generate API key
    api_key = f"mk_proj_{secrets.token_urlsafe(32)}"
    
    # Create project
    project = await db.project.create(
        data={
            "userId": clerk_user_id,
            "name": name,
            "description": description,
            "apiKey": api_key
        }
    )
    
    return project


@router.get("/projects/{clerk_user_id}")
async def list_projects(clerk_user_id: str):
    """List all projects for a user."""
    projects = await db.project.find_many(
        where={"userId": clerk_user_id},
        include={"repositories": True}
    )
    return projects


@router.get("/projects/detail/{project_id}")
async def get_project(project_id: str):
    """Get a single project with its repositories."""
    project = await db.project.find_unique(
        where={"id": project_id},
        include={"repositories": True}
    )
    
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    
    return project


@router.patch("/projects/{project_id}")
async def update_project(project_id: str, payload: dict = Body(...)):
    """Update project name/description."""
    name = payload.get("name")
    description = payload.get("description")
    
    update_data = {}
    if name is not None:
        update_data["name"] = name
    if description is not None:
        update_data["description"] = description
    
    project = await db.project.update(
        where={"id": project_id},
        data=update_data
    )
    
    return project


@router.delete("/projects/{project_id}")
async def delete_project(project_id: str):
    """Delete a project and all its repositories."""
    await db.project.delete(where={"id": project_id})
    return {"status": "deleted"}


@router.post("/projects/{project_id}/regenerate-key")
async def regenerate_api_key(project_id: str):
    """Regenerate the API key for a project."""
    new_key = f"mk_proj_{secrets.token_urlsafe(32)}"
    
    project = await db.project.update(
        where={"id": project_id},
        data={"apiKey": new_key}
    )
    
    return {"api_key": new_key}
