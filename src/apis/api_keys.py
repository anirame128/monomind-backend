from fastapi import APIRouter, Body
import secrets
from ..config import db

router = APIRouter()


@router.post("/api-keys/generate")
async def generate_api_key(payload: dict = Body(...)):
    clerk_user_id = payload.get("clerk_user_id")
    name = payload.get("name")
    key = f"mk_live_{secrets.token_urlsafe(32)}"
    await db.apikey.create(
        data={"key": key, "userId": clerk_user_id, "name": name}
    )
    return {"api_key": key}


@router.get("/api-keys/{clerk_user_id}")
async def list_api_keys(clerk_user_id: str):
    keys = await db.apikey.find_many(where={"userId": clerk_user_id})
    return keys


@router.delete("/api-keys/{key}")
async def delete_api_key(key: str):
    await db.apikey.delete(where={"key": key})
    return {"status": "deleted"}

