import os
from prisma import Prisma

# Database instance
db = Prisma()

# GitHub OAuth Configuration
GITHUB_CLIENT_ID = os.getenv("GITHUB_CLIENT_ID")
GITHUB_CLIENT_SECRET = os.getenv("GITHUB_CLIENT_SECRET")

# Frontend Configuration
FRONTEND_URL = os.getenv("FRONTEND_URL")
REDIRECT_URL = os.getenv("REDIRECT_URL")

# CORS Origins
CORS_ORIGINS = [
    "http://localhost:3000",
    "https://*.vercel.app",
    "https://monomind-frontend-gli94a20t-anirame128s-projects.vercel.app",
    "https://monomind-frontend.vercel.app",
]

