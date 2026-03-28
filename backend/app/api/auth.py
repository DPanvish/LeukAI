"""
Authentication endpoints.
POST /api/auth/login — returns a JWT access token.
POST /api/auth/register — creates a new user and returns a JWT access token.
"""

from fastapi import APIRouter, HTTPException, status
from app.core.database import get_database
from app.core.security import verify_password, create_access_token, hash_password
from app.models.schemas import LoginRequest, TokenResponse, RegisterRequest

router = APIRouter(prefix="/api/auth", tags=["Authentication"])

@router.post("/register", response_model=TokenResponse)
async def register(payload: RegisterRequest):
    db = get_database()
    existing_user = await db["users"].find_one({"username": payload.username})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered",
        )
    
    hashed_pwd = hash_password(payload.password)
    new_user = {
        "username": payload.username,
        "password": hashed_pwd,
        "full_name": payload.full_name,
        "role": "doctor"
    }
    await db["users"].insert_one(new_user)
    
    token = create_access_token(
        data={"sub": new_user["username"], "role": new_user["role"]}
    )

    return TokenResponse(
        access_token=token,
        user={
            "username": new_user["username"],
            "full_name": new_user["full_name"],
            "role": new_user["role"],
        },
    )

@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest):
    db = get_database()
    user = await db["users"].find_one({"username": payload.username})

    if not user or not verify_password(payload.password, user["password"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
        )

    token = create_access_token(
        data={"sub": user["username"], "role": user.get("role", "doctor")}
    )

    return TokenResponse(
        access_token=token,
        user={
            "username": user["username"],
            "full_name": user.get("full_name", ""),
            "role": user.get("role", "doctor"),
        },
    )
