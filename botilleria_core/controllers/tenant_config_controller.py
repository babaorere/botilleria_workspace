from __future__ import annotations

import logging
import uuid
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session

from config.database import get_db, set_tenant_context, safe_transaction
from models.tenant import Tenant
from services import (
    TenantService,
    KBService,
    ProductService,
    UserService,
    ConversationService,
    AuthService,
    AnalyticsService,
    CategoryService,
    KBCategoryService,
)
from dtos.request import (
    TenantProfileUpdateRequest,
    ProductCreateRequest,
    ProductUpdateRequest,
    KBEntryCreateRequest,
    KBEntryUpdateRequest,
    KBSearchRequest,
    CategoryCreateRequest,
    CategoryUpdateRequest,
    KBCategoryCreateRequest,
    KBCategoryUpdateRequest,
)
from dtos.response import (
    TenantProfileResponse,
    ProductResponse,
    KBEntryResponse,
    KBSearchResponse,
    KBSearchResultItem,
    ChannelRouteResponse,
    CategoryResponse,
    KBCategoryResponse,
)
from controllers.dependencies import get_current_tenant

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/tenants/me", tags=["tenant_config_controller"])

@router.get("/profile", response_model=TenantProfileResponse)
def get_profile(
    db: Session = Depends(get_db),
    fastapi_request: Request = None,
) -> TenantProfileResponse:
    try:
        tenant = get_current_tenant(fastapi_request, db)
        set_tenant_context(db, str(tenant.id))
        return TenantProfileResponse.model_validate(tenant)
    except HTTPException:
        raise
    except Exception as e:
        logger.error("get_profile failed: %s", e)
        raise



@router.put("/profile", response_model=TenantProfileResponse)
def update_profile(
    data: TenantProfileUpdateRequest,
    db: Session = Depends(get_db),
    fastapi_request: Request = None,
) -> TenantProfileResponse:
    try:
        tenant = get_current_tenant(fastapi_request, db)
        set_tenant_context(db, str(tenant.id))

        with safe_transaction(db):
            if data.name is not None:
                tenant.name = data.name
            if data.email is not None:
                tenant.email = data.email
            if data.phone is not None:
                tenant.phone = data.phone
            if data.address is not None:
                tenant.address = data.address
            if data.city is not None:
                tenant.city = data.city
            if data.website is not None:
                tenant.website = data.website
            if data.logo_url is not None:
                tenant.logo_url = data.logo_url
            if data.business_hours is not None:
                tenant.business_hours = data.business_hours

            db.flush()
            db.refresh(tenant)

        return TenantProfileResponse.model_validate(tenant)
    except HTTPException:
        raise
    except Exception as e:
        logger.error("update_profile failed: %s", e)
        raise


# ── Channels ─────────────────────────────────────────────────────────────────



@router.get("/channels", response_model=list[ChannelRouteResponse])
def list_channels(
    db: Session = Depends(get_db),
    fastapi_request: Request = None,
) -> list[ChannelRouteResponse]:
    try:
        tenant = get_current_tenant(fastapi_request, db)
        set_tenant_context(db, str(tenant.id))

        tenant_service = TenantService(db)
        routes = tenant_service.channel_repo.find_by_tenant_id(tenant.id)
        return [ChannelRouteResponse.model_validate(r) for r in routes]
    except HTTPException:
        raise
    except Exception as e:
        logger.error("list_channels failed: %s", e)
        raise


# ── Products ─────────────────────────────────────────────────────────────────



@router.get("/users/count")
def get_user_count(
    db: Session = Depends(get_db),
    fastapi_request: Request = None,
) -> dict:
    try:
        tenant = get_current_tenant(fastapi_request, db)
        set_tenant_context(db, str(tenant.id))

        user_svc = UserService(db, tenant.id)
        count = user_svc.repo.count_by_tenant(tenant.id)
        return {"count": count}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("get_user_count failed: %s", e)
        raise



@router.get("/conversations/count")
def get_conversation_count(
    db: Session = Depends(get_db),
    fastapi_request: Request = None,
) -> dict:
    try:
        tenant = get_current_tenant(fastapi_request, db)
        set_tenant_context(db, str(tenant.id))

        conv_svc = ConversationService(db, tenant.id)
        count = conv_svc.repo.count_by_tenant(tenant.id)
        return {"count": count}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("get_conversation_count failed: %s", e)
        raise



@router.get("/analytics")
def get_analytics(
    db: Session = Depends(get_db),
    fastapi_request: Request = None,
) -> dict:
    try:
        tenant = get_current_tenant(fastapi_request, db)
        set_tenant_context(db, str(tenant.id))

        analytics_svc = AnalyticsService(db, tenant.id)
        basic = analytics_svc.get_basic_metrics()
        sales = analytics_svc.get_sales_metrics()
        
        return {
            "basic": basic,
            "lost_sales": sales
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error("get_analytics failed: %s", e)
        raise


# ── Categories CRUD ──────────────────────────────────────────────────────────



