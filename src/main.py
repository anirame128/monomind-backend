from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .config import db, CORS_ORIGINS
from .apis import github, clerk, api_keys

app = FastAPI()

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database lifecycle
@app.on_event("startup")
async def startup():
    await db.connect()

@app.on_event("shutdown")
async def shutdown():
    await db.disconnect()

# Include routers
app.include_router(github.router)
app.include_router(clerk.router)
app.include_router(api_keys.router)


@app.get("/")
async def root():
    return {"status": "ok", "message": "Monomind API"}
