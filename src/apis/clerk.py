from fastapi import APIRouter
import secrets
from ..config import db

router = APIRouter()


@router.post("/webhooks/clerk")
async def clerk_webhook(data: dict):
    if data.get("type") == "user.created":
        user_data = data["data"]
        
        # Create user
        user = await db.user.upsert(
            where={"clerkUserId": user_data["id"]},
            data={
                "create": {
                    "clerkUserId": user_data["id"],
                    "email": user_data["email_addresses"][0]["email_address"]
                },
                "update": {
                    "email": user_data["email_addresses"][0]["email_address"]
                }
            }
        )
        
        # Create default project with API key
        api_key = f"mk_proj_{secrets.token_urlsafe(32)}"
        await db.project.create(
            data={
                "userId": user_data["id"],
                "name": "My First Project",
                "description": "Your default project to get started with Monomind",
                "apiKey": api_key
            }
        )
    
    return {"status": "ok"}
