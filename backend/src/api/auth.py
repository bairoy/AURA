from fastapi import APIRouter, HTTPException, Header
from pydantic import BaseModel
from typing import Optional

from src.db.users import create_user, get_user_by_username, create_thread, get_user_threads
from src.auth.jwt import hash_password, verify_password, create_access_token, decode_token

router = APIRouter(prefix="/auth", tags=["auth"])


# ── Request schemas ────────────────────────────────────────────────────────────

class RegisterRequest(BaseModel):
    username: str
    password: str

class LoginRequest(BaseModel):
    username: str
    password: str

class CreateThreadRequest(BaseModel):
    label: Optional[str] = None


# ── Helper ─────────────────────────────────────────────────────────────────────

def _get_current_user(authorization: str) -> dict:
    """Extract and validate user from Authorization: Bearer <token> header."""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid token")
    token = authorization.removeprefix("Bearer ").strip()
    user = decode_token(token)
    if not user:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return user


# ── Endpoints ──────────────────────────────────────────────────────────────────

@router.post("/register")
async def register(body: RegisterRequest):
    if len(body.username.strip()) < 2:
        raise HTTPException(status_code=400, detail="Username too short")
    if len(body.password) < 6:
        raise HTTPException(status_code=400, detail="Password must be at least 6 characters")

    existing = await get_user_by_username(body.username.strip())
    if existing:
        raise HTTPException(status_code=409, detail="Username already taken")

    user = await create_user(body.username.strip(), hash_password(body.password))
    token = create_access_token(user["id"], user["username"])
    return {"token": token, "username": user["username"], "user_id": user["id"]}


@router.post("/login")
async def login(body: LoginRequest):
    user = await get_user_by_username(body.username.strip())
    if not user or not verify_password(body.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid username or password")

    token = create_access_token(user["id"], user["username"])
    return {"token": token, "username": user["username"], "user_id": user["id"]}


@router.get("/threads")
async def list_threads(authorization: str = Header(...)):
    user = _get_current_user(authorization)
    threads = await get_user_threads(user["user_id"])
    return {"threads": threads}


@router.post("/threads")
async def new_thread(body: CreateThreadRequest, authorization: str = Header(...)):
    user = _get_current_user(authorization)
    thread = await create_thread(user["user_id"], body.label)
    return thread
