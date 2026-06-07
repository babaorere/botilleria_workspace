from __future__ import annotations

import logging
import uuid

from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session

from config.database import get_db
from models.tenant import Tenant
from services import TenantService, AuthService

logger = logging.getLogger(__name__)


def get_current_tenant(request: Request, db: Session = Depends(get_db)) -> Tenant:
    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        token = auth_header.split(" ")[1]
        payload = AuthService.decode_access_token(token)
        if payload and payload.get("role") == "tenant":
            tenant_service = TenantService(db)
            tenant = tenant_service.get_tenant_by_id(uuid.UUID(payload.get("sub")))
            if tenant:
                return tenant
        raise HTTPException(401, "Invalid or expired JWT token")
    raise HTTPException(401, "Missing or invalid Authorization header")
