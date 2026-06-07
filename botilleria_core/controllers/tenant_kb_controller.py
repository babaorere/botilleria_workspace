from __future__ import annotations

import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from config.database import get_db, set_tenant_context, safe_transaction
from services import (
    KBService,
    KBCategoryService,
)
from dtos.request import (
    KBEntryCreateRequest,
    KBEntryUpdateRequest,
    KBSearchRequest,
    KBCategoryCreateRequest,
    KBCategoryUpdateRequest,
)
from dtos.response import (
    KBEntryResponse,
    KBSearchResponse,
    KBSearchResultItem,
    KBCategoryResponse,
)
from controllers.dependencies import get_current_tenant

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/tenants/me", tags=["tenant_kb_controller"])


@router.get("/kb", response_model=list[KBEntryResponse])
def list_kb_entries(
    category: str | None = None,
    active_only: bool = True,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    fastapi_request: Request = None,
) -> list[KBEntryResponse]:
    try:
        tenant = get_current_tenant(fastapi_request, db)
        set_tenant_context(db, str(tenant.id))

        kb_svc = KBService(db, tenant.id)
        entries = kb_svc.list_entries(
            category=category,
            active_only=active_only,
            skip=skip,
            limit=limit,
        )
        return [KBEntryResponse.model_validate(e) for e in entries]
    except HTTPException:
        raise
    except Exception as e:
        logger.error("list_kb_entries failed: %s", e)
        raise


@router.post("/kb", response_model=KBEntryResponse)
def create_kb_entry(
    data: KBEntryCreateRequest,
    db: Session = Depends(get_db),
    fastapi_request: Request = None,
) -> KBEntryResponse:
    try:
        tenant = get_current_tenant(fastapi_request, db)
        set_tenant_context(db, str(tenant.id))

        kb_svc = KBService(db, tenant.id)
        with safe_transaction(db):
            entry = kb_svc.create_entry(
                category=data.category,
                title=data.title,
                content=data.content,
            )
        return KBEntryResponse.model_validate(entry)
    except HTTPException:
        raise
    except Exception as e:
        logger.error("create_kb_entry failed: %s", e)
        raise


@router.put("/kb/{entry_id}", response_model=KBEntryResponse)
def update_kb_entry(
    entry_id: str,
    data: KBEntryUpdateRequest,
    db: Session = Depends(get_db),
    fastapi_request: Request = None,
) -> KBEntryResponse:
    try:
        tenant = get_current_tenant(fastapi_request, db)
        set_tenant_context(db, str(tenant.id))

        kb_svc = KBService(db, tenant.id)
        with safe_transaction(db):
            entry = kb_svc.update_entry(
                entry_id=uuid.UUID(entry_id),
                category=data.category,
                title=data.title,
                content=data.content,
                is_active=data.is_active,
            )
        return KBEntryResponse.model_validate(entry)
    except HTTPException:
        raise
    except Exception as e:
        logger.error("update_kb_entry failed: %s", e)
        raise


@router.delete("/kb/{entry_id}")
def delete_kb_entry(
    entry_id: str,
    db: Session = Depends(get_db),
    fastapi_request: Request = None,
) -> dict:
    try:
        tenant = get_current_tenant(fastapi_request, db)
        set_tenant_context(db, str(tenant.id))

        kb_svc = KBService(db, tenant.id)
        with safe_transaction(db):
            deleted = kb_svc.delete_entry(uuid.UUID(entry_id))
        if not deleted:
            raise HTTPException(404, "KB entry not found")
        return {"status": "deleted", "id": entry_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("delete_kb_entry failed: %s", e)
        raise


@router.post("/kb/search", response_model=KBSearchResponse)
def search_kb(
    data: KBSearchRequest,
    db: Session = Depends(get_db),
    fastapi_request: Request = None,
) -> KBSearchResponse:
    try:
        tenant = get_current_tenant(fastapi_request, db)
        set_tenant_context(db, str(tenant.id))

        kb_svc = KBService(db, tenant.id)
        results = kb_svc.search(
            query=data.query, top_k=data.top_k, category=data.category
        )
        return KBSearchResponse(
            query=data.query,
            results=[KBSearchResultItem(**r) for r in results],
            count=len(results),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("search_kb failed: %s", e)
        raise


@router.get("/kb/categories", response_model=list[str])
def get_kb_categories(
    db: Session = Depends(get_db),
    fastapi_request: Request = None,
) -> list[str]:
    try:
        tenant = get_current_tenant(fastapi_request, db)
        set_tenant_context(db, str(tenant.id))

        kb_svc = KBService(db, tenant.id)
        return kb_svc.get_categories()
    except HTTPException:
        raise
    except Exception as e:
        logger.error("get_kb_categories failed: %s", e)
        raise


# ── Users & Conversations (read-only) ────────────────────────────────────────


@router.get("/kb-categories", response_model=list[KBCategoryResponse])
def list_kb_categories(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    fastapi_request: Request = None,
) -> list[KBCategoryResponse]:
    try:
        tenant = get_current_tenant(fastapi_request, db)
        set_tenant_context(db, str(tenant.id))

        kb_category_svc = KBCategoryService(db, tenant.id)
        categories = kb_category_svc.list_categories(skip=skip, limit=limit)
        return [KBCategoryResponse.model_validate(c) for c in categories]
    except HTTPException:
        raise
    except Exception as e:
        logger.error("list_kb_categories failed: %s", e)
        raise


@router.post("/kb-categories", response_model=KBCategoryResponse)
def create_kb_category(
    data: KBCategoryCreateRequest,
    db: Session = Depends(get_db),
    fastapi_request: Request = None,
) -> KBCategoryResponse:
    try:
        tenant = get_current_tenant(fastapi_request, db)
        set_tenant_context(db, str(tenant.id))

        kb_category_svc = KBCategoryService(db, tenant.id)
        with safe_transaction(db):
            category = kb_category_svc.create_category(
                name=data.name,
                description=data.description,
            )
        return KBCategoryResponse.model_validate(category)
    except ValueError as e:
        raise HTTPException(400, str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error("create_kb_category failed: %s", e)
        raise


@router.put("/kb-categories/{category_id}", response_model=KBCategoryResponse)
def update_kb_category(
    category_id: str,
    data: KBCategoryUpdateRequest,
    db: Session = Depends(get_db),
    fastapi_request: Request = None,
) -> KBCategoryResponse:
    try:
        tenant = get_current_tenant(fastapi_request, db)
        set_tenant_context(db, str(tenant.id))

        kb_category_svc = KBCategoryService(db, tenant.id)
        with safe_transaction(db):
            category = kb_category_svc.update_category(
                category_id=uuid.UUID(category_id),
                name=data.name,
                description=data.description,
            )
        return KBCategoryResponse.model_validate(category)
    except ValueError as e:
        raise HTTPException(400, str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error("update_kb_category failed: %s", e)
        raise


@router.delete("/kb-categories/{category_id}")
def delete_kb_category(
    category_id: str,
    db: Session = Depends(get_db),
    fastapi_request: Request = None,
) -> dict:
    try:
        tenant = get_current_tenant(fastapi_request, db)
        set_tenant_context(db, str(tenant.id))

        kb_category_svc = KBCategoryService(db, tenant.id)
        with safe_transaction(db):
            deleted = kb_category_svc.delete_category(uuid.UUID(category_id))
        if not deleted:
            raise HTTPException(404, "KB Category not found")
        return {"status": "deleted", "id": category_id}
    except ValueError as e:
        raise HTTPException(400, str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error("delete_kb_category failed: %s", e)
        raise
