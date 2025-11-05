from fastapi import APIRouter, HTTPException, Body
from fastapi.responses import RedirectResponse
import httpx
from ..config import db, GITHUB_CLIENT_ID, GITHUB_CLIENT_SECRET, FRONTEND_URL, REDIRECT_URL

router = APIRouter()


@router.get("/auth/github")
async def github_oauth_start(user_id: str):
    """
    Initiate GitHub OAuth flow.
    Frontend calls this with Clerk user ID in query param.
    
    Uses prompt=select_account to force GitHub to show account picker,
    allowing users to choose which GitHub account to link.
    """
    state = user_id  # In production, encrypt this
    
    github_auth_url = (
        f"https://github.com/login/oauth/authorize"
        f"?client_id={GITHUB_CLIENT_ID}"
        f"&redirect_uri={REDIRECT_URL}"
        f"&scope=repo,write:repo_hook"
        f"&state={state}"
        f"&prompt=select_account"
    )
    
    return RedirectResponse(github_auth_url)


@router.get("/auth/github/callback")
async def github_oauth_callback(code: str, state: str):
    """
    GitHub redirects here after user authorizes.
    Exchange code for access token and save to database.
    """
    try:
        # Exchange code for access token
        async with httpx.AsyncClient() as client:
            token_response = await client.post(
                "https://github.com/login/oauth/access_token",
                json={
                    "client_id": GITHUB_CLIENT_ID,
                    "client_secret": GITHUB_CLIENT_SECRET,
                    "code": code
                },
                headers={"Accept": "application/json"}
            )
            
            token_data = token_response.json()
            access_token = token_data.get("access_token")
            
            if not access_token:
                return RedirectResponse(f"{FRONTEND_URL}/dashboard?error=auth_failed")
            
            # Get GitHub user info
            user_response = await client.get(
                "https://api.github.com/user",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Accept": "application/vnd.github.v3+json"
                }
            )
            
            if user_response.status_code != 200:
                print(f"Failed to fetch GitHub user info: {user_response.status_code}")
                return RedirectResponse(f"{FRONTEND_URL}/dashboard?error=auth_failed")
            
            github_user = user_response.json()
            github_user_id = github_user["id"]
            clerk_user_id = state
            
            # Check if this GitHub account is already linked to a different Clerk user
            existing_user_with_github = await db.user.find_unique(
                where={"githubId": github_user_id}
            )
            
            # If GitHub account is linked to another user, reject the connection
            if existing_user_with_github and existing_user_with_github.clerkUserId != clerk_user_id:
                print(f"GitHub account {github_user_id} ({github_user['login']}) is already linked to user {existing_user_with_github.clerkUserId}")
                return RedirectResponse(
                    f"{FRONTEND_URL}/dashboard?error=github_already_linked&message=This GitHub account is already connected to another account. Please log out of GitHub or use a different GitHub account."
                )
            
            # Update user in database (will create if doesn't exist)
            await db.user.upsert(
                where={"clerkUserId": clerk_user_id},
                data={
                    "create": {
                        "clerkUserId": clerk_user_id,
                        "email": f"{clerk_user_id}@temp.monomind",  # Temporary, webhook will update
                        "githubId": github_user_id,
                        "githubUsername": github_user["login"],
                        "githubAccessToken": access_token
                    },
                    "update": {
                        "githubId": github_user_id,
                        "githubUsername": github_user["login"],
                        "githubAccessToken": access_token
                    }
                }
            )
        
        # Redirect back to dashboard with success
        return RedirectResponse(f"{FRONTEND_URL}/dashboard?github_connected=true")
        
    except Exception as e:
        print(f"GitHub OAuth error: {e}")
        return RedirectResponse(f"{FRONTEND_URL}/dashboard?error=auth_failed")


@router.get("/user/{clerk_user_id}/github-status")
async def get_github_status(clerk_user_id: str):
    """Check if user has GitHub connected."""
    user = await db.user.find_unique(
        where={"clerkUserId": clerk_user_id}
    )
    
    if not user:
        return {"connected": False}
    
    return {
        "connected": user.githubId is not None,
        "username": user.githubUsername
    }


@router.get("/github/repositories")
async def list_github_repos(clerk_user_id: str):
    """
    Fetch all repos the user has access to on GitHub.
    Shows which are already indexed vs. available to add.
    """
    user = await db.user.find_unique(
        where={"clerkUserId": clerk_user_id}
    )
    
    if not user or not user.githubAccessToken:
        raise HTTPException(status_code=400, detail="GitHub not connected")
    
    try:
        # Fetch repos from GitHub API
        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://api.github.com/user/repos",
                headers={
                    "Authorization": f"Bearer {user.githubAccessToken}",
                    "Accept": "application/vnd.github.v3+json"
                },
                params={
                    "per_page": 100,
                    "sort": "updated",
                    "affiliation": "owner,collaborator,organization_member"
                }
            )
            
            if response.status_code != 200:
                raise HTTPException(status_code=500, detail="Failed to fetch repositories")
            
            github_repos = response.json()
        
        # Check which are already indexed
        indexed_repos = await db.repository.find_many(
            where={"userId": user.clerkUserId}
        )
        indexed_ids = {r.githubId for r in indexed_repos}
        
        # Format response
        repos = []
        for repo in github_repos:
            repos.append({
                "githubId": repo["id"],
                "fullName": repo["full_name"],
                "name": repo["name"],
                "private": repo["private"],
                "description": repo["description"],
                "defaultBranch": repo["default_branch"],
                "url": repo["html_url"],
                "isIndexed": repo["id"] in indexed_ids
            })
        
        return repos
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error fetching GitHub repos: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/repositories/add")
async def add_repository(payload: dict = Body(...)):
    """
    Add a GitHub repo to Monomind for indexing.
    For now, just creates the record. We'll add actual indexing next.
    """
    clerk_user_id = payload.get("clerk_user_id")
    github_repo_id = payload.get("github_repo_id")
    
    user = await db.user.find_unique(
        where={"clerkUserId": clerk_user_id}
    )
    
    if not user or not user.githubAccessToken:
        raise HTTPException(status_code=400, detail="GitHub not connected")
    
    try:
        # Get repo details from GitHub
        async with httpx.AsyncClient() as client:
            repo_response = await client.get(
                f"https://api.github.com/repositories/{github_repo_id}",
                headers={
                    "Authorization": f"Bearer {user.githubAccessToken}",
                    "Accept": "application/vnd.github.v3+json"
                }
            )
            
            if repo_response.status_code != 200:
                raise HTTPException(status_code=404, detail="Repository not found")
            
            github_repo = repo_response.json()
        
        # Create repository record
        repo = await db.repository.create(
            data={
                "userId": user.clerkUserId,
                "githubId": github_repo["id"],
                "githubUrl": github_repo["html_url"],
                "fullName": github_repo["full_name"],
                "defaultBranch": github_repo["default_branch"],
                "isPrivate": github_repo["private"],
                "description": github_repo.get("description"),
                "status": "PENDING"
            }
        )
        
        return repo
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Error adding repository: {e}")
        raise HTTPException(status_code=500, detail=str(e))

