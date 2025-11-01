from fastapi import FastAPI, Body
from fastapi.middleware.cors import CORSMiddleware
from prisma import Prisma
import secrets
import os

app = FastAPI()
db = Prisma()

# Update CORS for production
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "https://*.vercel.app",
        "https://monomind-frontend-gli94a20t-anirame128s-projects.vercel.app",
        "https://monomind-frontend.vercel.app",  # Add your production domain
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
async def generate_api_key(payload: dict = Body(...)):
    clerk_user_id = payload.get("clerk_user_id")
    name = payload.get("name")
    
    key = f"mk_live_{secrets.token_urlsafe(32)}"
    await db.apikey.create(
        data={"key": key, "userId": clerk_user_id, "name": name}
    )
    return {"api_key": key}

@app.get("/api-keys/{clerk_user_id}")
async def list_api_keys(clerk_user_id: str):
    keys = await db.apikey.find_many(where={"userId": clerk_user_id})
    return keys

@app.delete("/api-keys/{key}")
async def delete_api_key(key: str):
    await db.apikey.delete(where={"key": key})
    return {"status": "deleted"}

@app.get("/")
async def root():
    return {"status": "ok", "message": "Monomind API"}