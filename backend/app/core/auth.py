"""Authentication dependencies – Clerk JWT verification via JWKS."""

from __future__ import annotations

import time
from typing import Any

import httpx
import jwt
from fastapi import Depends, Header, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.models.user import User

# ---------------------------------------------------------------------------
# JWKS cache – simple in-memory cache with TTL
# ---------------------------------------------------------------------------

_jwks_cache: dict[str, Any] = {"keys": [], "fetched_at": 0.0}
_JWKS_CACHE_TTL = 3600  # 1 hour


async def _get_jwks() -> list[dict[str, Any]]:
    """Fetch Clerk JWKS, with in-memory caching."""
    now = time.time()
    if _jwks_cache["keys"] and now - _jwks_cache["fetched_at"] < _JWKS_CACHE_TTL:
        return _jwks_cache["keys"]  # type: ignore[return-value]

    url = f"https://{settings.CLERK_DOMAIN}/.well-known/jwks.json"
    async with httpx.AsyncClient() as client:
        resp = await client.get(url, timeout=10)
        resp.raise_for_status()
        data = resp.json()

    _jwks_cache["keys"] = data["keys"]
    _jwks_cache["fetched_at"] = now
    return data["keys"]  # type: ignore[no-any-return]


def _build_rsa_key(jwk: dict[str, Any]) -> jwt.algorithms.RSAAlgorithm:
    """Convert a JWK dict to a public key usable by PyJWT."""
    return jwt.algorithms.RSAAlgorithm.from_jwk(jwk)  # type: ignore[return-value]


# ---------------------------------------------------------------------------
# FastAPI dependencies
# ---------------------------------------------------------------------------


async def get_current_user_id(
    authorization: str = Header(..., description="Bearer <token>"),
) -> str:
    """Extract and verify the Clerk JWT, returning the ``sub`` (clerk_id).

    Raises ``HTTPException 401`` on missing, malformed, or invalid tokens.
    """
    if not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header – expected 'Bearer <token>'",
        )

    token = authorization.removeprefix("Bearer ").strip()
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing token",
        )

    try:
        jwks = await _get_jwks()

        # Decode the token header to find the matching key
        unverified_header = jwt.get_unverified_header(token)
        kid = unverified_header.get("kid")

        matching_key = None
        for key in jwks:
            if key.get("kid") == kid:
                matching_key = key
                break

        if matching_key is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="No matching signing key found",
            )

        public_key = _build_rsa_key(matching_key)

        payload = jwt.decode(
            token,
            public_key,
            algorithms=["RS256"],
            options={"require": ["sub", "exp", "iat"]},
        )

        clerk_id: str | None = payload.get("sub")
        if not clerk_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Token missing 'sub' claim",
            )

        return clerk_id

    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
        )
    except jwt.InvalidTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid token: {exc}",
        )
    except httpx.HTTPError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Failed to fetch JWKS: {exc}",
        )


async def get_current_user(
    clerk_id: str = Depends(get_current_user_id),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Resolve the authenticated Clerk user to a local ``User`` record.

    Raises ``HTTPException 404`` when the user is not found in the database.
    """
    result = await db.execute(select(User).where(User.clerk_id == clerk_id))
    user = result.scalar_one_or_none()

    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found – ensure the Clerk webhook has synced this user",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is deactivated",
        )

    return user
