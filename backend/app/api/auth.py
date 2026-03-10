"""
Authentication endpoints.
POST /api/auth/login — returns a JWT access token.
"""

from fastapi import APIRouter, HTTPException, status
from app.core.database import get_database
from app.core.security import verify_password, create_access_token
from app.models.schemas import LoginRequest, TokenResponse

router = APIRouter(prefix="/api/auth", tags=["Authentication"])


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
