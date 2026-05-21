"""JWT Bearer token authentication."""

from __future__ import annotations
from datetime import datetime, timedelta
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


def create_access_token(subject: str, role: str = "clinician") -> str:
    """Create a signed JWT — call from /token endpoint or CLI."""
    expire = datetime.utcnow() + timedelta(minutes=settings.jwt_expire_minutes)
    payload = {"sub": subject, "role": role, "exp": expire}
    return jwt.encode(payload, settings.jwt_secret, algorithm=settings.jwt_algorithm)


async def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(security)],
) -> TokenData:
    """FastAPI dependency — validates Bearer JWT, returns token payload."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid or expired token",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            credentials.credentials,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
        )
        sub: str = payload.get("sub", "")
        role: str = payload.get("role", "clinician")
        if not sub:
            raise credentials_exception
        return TokenData(sub=sub, role=role)
    except JWTError:
        raise credentials_exception
