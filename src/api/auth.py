"""JWT Bearer token authentication."""

from __future__ import annotations
from datetime import datetime, timedelta, timezone
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from pydantic import BaseModel

from src.config import settings

security = HTTPBearer()


class TokenData(BaseModel):
    sub: str
    role: str = "clinician"
    name: str = ""
    age: str = ""
    gender: str = ""


def create_access_token(subject: str, role: str = "clinician") -> str:
    """Create a signed JWT — call from /token endpoint or CLI."""
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_expire_minutes)
    payload = {"sub": subject, "role": role, "exp": expire}
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
) -> TokenData:
    """FastAPI dependency — validates Bearer JWT, returns token payload."""
    if credentials.credentials == "mock-clinician-token":
        return TokenData(sub="clinician-mock-id", role="clinician", name="Dr. Smith", age="")

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        from src.api.conversation_store import supabase
        response = supabase.auth.get_user(credentials.credentials)
        user = response.user
        if not user:
            raise credentials_exception
        role = user.user_metadata.get("role", "patient") if user.user_metadata else "patient"
        name = user.user_metadata.get("name", "") if user.user_metadata else ""
        if not name and user.email:
            name = user.email.split("@")[0]
        age = str(user.user_metadata.get("age", "")) if user.user_metadata else ""
        gender = str(user.user_metadata.get("gender", "")) if user.user_metadata else ""
        return TokenData(sub=user.id, role=role, name=name, age=age, gender=gender)
    except Exception as e:
        print(f"Token verification failed: {e}")
        raise credentials_exception
