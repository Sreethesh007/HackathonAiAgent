"""
POST /auth/login — dev-mode login endpoint for the Angular frontend.

In production, replace the credential check with your identity provider
(LDAP, database lookup, SSO, etc.).

Dev credentials:
  username=patient   → role=patient
  username=clinician → role=clinician
  username=admin     → role=admin
  (any password accepted in dev mode)
"""

from __future__ import annotations
from datetime import datetime, timedelta
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from src.api.auth import create_access_token
from src.config import settings

router = APIRouter(prefix="/auth", tags=["Auth"])

# ── Dev role map ──────────────────────────────────────────────────────────────
_DEV_ROLES: dict[str, str] = {
    "patient":   "patient",
    "clinician": "clinician",
    "admin":     "admin",
    # Additional dev users
    "doctor":    "clinician",
    "nurse":     "clinician",
    "p001":      "patient",
}


class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str
    username: str
    expires_in: int  # seconds


@router.post("/login", response_model=LoginResponse, summary="Obtain JWT for Angular frontend")
async def login(body: LoginRequest) -> LoginResponse:
    """
    Dev-mode login — accepts any password.
    Role is determined by username.

    Replace `_DEV_ROLES` lookup with real auth in production.
    """
    username = body.username.strip().lower()
    role = _DEV_ROLES.get(username)

    if role is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Unknown user '{username}'. Use 'patient', 'clinician', or 'admin'.",
        )

    token = create_access_token(subject=username, role=role)
    expires_seconds = settings.jwt_expire_minutes * 60

    return LoginResponse(
        access_token=token,
        role=role,
        username=username,
        expires_in=expires_seconds,
    )
