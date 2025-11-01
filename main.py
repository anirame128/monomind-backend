from fastapi import FastAPI
from prisma import Prisma
import secrets

app = FastAPI()
db = Prisma()

@app.on_event("startup")
async def startup():
    await db.connect()

@app.on_event("shutdown")
async def shutdown():
    await db.disconnect()

@app.post("/webhooks/clerk")
async def clerk_webhook(data: dict):
    if data.get("type") == "user.created":
        user_data = data["data"]
        await db.user.upsert(
            where={"clerkUserId": user_data["id"]},
            data={
                "create": {
                    "clerkUserId": user_data["id"],
                    "email": user_data["email_addresses"][0]["email_address"]
                },
                "update": {}
            }
        )
    return {"status": "ok"}

@app.post("/api-keys/generate")
async def generate_api_key(clerk_user_id: str, name: str):
    key = f"mk_live_{secrets.token_urlsafe(32)}"
    await db.apikey.create(
        data={"key": key, "userId": clerk_user_id, "name": name}
    )
    return {"api_key": key}

@app.get("/api-keys/{clerk_user_id}")
async def list_api_keys(clerk_user_id: str):
    keys = await db.apikey.find_many(where={"userId": clerk_user_id})
    return keys