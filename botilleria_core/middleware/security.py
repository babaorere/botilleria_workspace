from __future__ import annotations

import logging
import hmac
from fastapi import Header, HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer
from config.settings import settings
from services.auth_service import AuthService
from services.tenant_service import TenantService
from config.database import get_db
from sqlalchemy.orm import Session
import uuid

logger = logging.getLogger(__name__)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


async def verify_admin_key(
    x_admin_api_key: str | None = Header(None, alias="X-Admin-API-Key"),
) -> str:
    """Validate the X-Admin-API-Key header against the server configuration.

    Args:
        x_admin_api_key: The admin API key provided in request headers.

    Returns:
        str: The validated API key.

    Raises:
        HTTPException: If the key is missing, invalid, or server is misconfigured.
    """
    if not settings.admin_api_key:
        logger.error("Admin API key is not configured in settings")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Admin API key is not configured on the server",
        )

    if not x_admin_api_key:
        logger.warning("Missing X-Admin-API-Key header in request")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing X-Admin-API-Key header",
        )

    if not hmac.compare_digest(
        x_admin_api_key.encode("utf-8"), settings.admin_api_key.encode("utf-8")
    ):
        logger.warning("Invalid Admin API key attempt")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Admin API Key",
        )

    return x_admin_api_key


async def get_current_admin(token: str = Depends(oauth2_scheme)) -> str:
    """Validate JWT token and ensure it belongs to an admin."""
    payload = AuthService.decode_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if payload.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions",
        )
    return "admin"


async def get_current_tenant(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
):
    """Validate JWT token and return the associated Tenant."""
    payload = AuthService.decode_access_token(token)
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if payload.get("role") != "tenant":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions",
        )

    tenant_id = payload.get("sub")
    tenant_service = TenantService(db)
    tenant = tenant_service.get_tenant_by_id(uuid.UUID(tenant_id))
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found",
        )
    return tenant
