from __future__ import annotations

import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session

from config.database import get_db, set_tenant_context, safe_transaction
from services import (
    ProductService,
    CategoryService,
)
from dtos.request import (
    ProductCreateRequest,
    ProductUpdateRequest,
    CategoryCreateRequest,
    CategoryUpdateRequest,
)
from dtos.response import (
    ProductResponse,
    CategoryResponse,
)
from controllers.dependencies import get_current_tenant

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/tenants/me", tags=["tenant_products_controller"])

@router.get("/products", response_model=list[ProductResponse])
def list_products(
    category: str | None = None,
    available_only: bool = False,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    fastapi_request: Request = None,
) -> list[ProductResponse]:
    try:
        tenant = get_current_tenant(fastapi_request, db)
        set_tenant_context(db, str(tenant.id))

        product_svc = ProductService(db, tenant.id)
        products = product_svc.list_products(
            category=category,
            available_only=available_only,
            skip=skip,
            limit=limit,
        )
        return [ProductResponse.model_validate(p) for p in products]
    except HTTPException:
        raise
    except Exception as e:
        logger.error("list_products failed: %s", e)
        raise



@router.post("/products", response_model=ProductResponse)
def create_product(
    data: ProductCreateRequest,
    db: Session = Depends(get_db),
    fastapi_request: Request = None,
) -> ProductResponse:
    try:
        tenant = get_current_tenant(fastapi_request, db)
        set_tenant_context(db, str(tenant.id))

        product_svc = ProductService(db, tenant.id)
        with safe_transaction(db):
            product = product_svc.create_product(
                name=data.name,
                description=data.description,
                price=data.price,
                stock=data.stock,
                category=data.category,
                is_available=data.is_available,
            )
        return ProductResponse.model_validate(product)
    except HTTPException:
        raise
    except Exception as e:
        logger.error("create_product failed: %s", e)
        raise



@router.put("/products/{product_id}", response_model=ProductResponse)
def update_product(
    product_id: str,
    data: ProductUpdateRequest,
    db: Session = Depends(get_db),
    fastapi_request: Request = None,
) -> ProductResponse:
    try:
        tenant = get_current_tenant(fastapi_request, db)
        set_tenant_context(db, str(tenant.id))

        product_svc = ProductService(db, tenant.id)
        with safe_transaction(db):
            product = product_svc.update_product(
                product_id=uuid.UUID(product_id),
                name=data.name,
                description=data.description,
                price=data.price,
                stock=data.stock,
                category=data.category,
                is_available=data.is_available,
            )
        return ProductResponse.model_validate(product)
    except HTTPException:
        raise
    except Exception as e:
        logger.error("update_product failed: %s", e)
        raise



@router.delete("/products/{product_id}")
def delete_product(
    product_id: str,
    db: Session = Depends(get_db),
    fastapi_request: Request = None,
) -> dict:
    try:
        tenant = get_current_tenant(fastapi_request, db)
        set_tenant_context(db, str(tenant.id))

        product_svc = ProductService(db, tenant.id)
        with safe_transaction(db):
            deleted = product_svc.delete_product(uuid.UUID(product_id))
        if not deleted:
            raise HTTPException(404, "Product not found")
        return {"status": "deleted", "id": product_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("delete_product failed: %s", e)
        raise



@router.get("/products/categories", response_model=list[str])
def get_product_categories(
    db: Session = Depends(get_db),
    fastapi_request: Request = None,
) -> list[str]:
    try:
        tenant = get_current_tenant(fastapi_request, db)
        set_tenant_context(db, str(tenant.id))

        product_svc = ProductService(db, tenant.id)
        return product_svc.get_categories()
    except HTTPException:
        raise
    except Exception as e:
        logger.error("get_product_categories failed: %s", e)
        raise


# ── Knowledge Base ───────────────────────────────────────────────────────────



@router.get("/categories", response_model=list[CategoryResponse])
def list_categories(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    fastapi_request: Request = None,
) -> list[CategoryResponse]:
    try:
        tenant = get_current_tenant(fastapi_request, db)
        set_tenant_context(db, str(tenant.id))

        category_svc = CategoryService(db, tenant.id)
        categories = category_svc.list_categories(skip=skip, limit=limit)
        return [CategoryResponse.model_validate(c) for c in categories]
    except HTTPException:
        raise
    except Exception as e:
        logger.error("list_categories failed: %s", e)
        raise



@router.post("/categories", response_model=CategoryResponse)
def create_category(
    data: CategoryCreateRequest,
    db: Session = Depends(get_db),
    fastapi_request: Request = None,
) -> CategoryResponse:
    try:
        tenant = get_current_tenant(fastapi_request, db)
        set_tenant_context(db, str(tenant.id))

        category_svc = CategoryService(db, tenant.id)
        with safe_transaction(db):
            category = category_svc.create_category(
                name=data.name,
                description=data.description,
            )
        return CategoryResponse.model_validate(category)
    except ValueError as e:
        raise HTTPException(400, str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error("create_category failed: %s", e)
        raise



@router.put("/categories/{category_id}", response_model=CategoryResponse)
def update_category(
    category_id: str,
    data: CategoryUpdateRequest,
    db: Session = Depends(get_db),
    fastapi_request: Request = None,
) -> CategoryResponse:
    try:
        tenant = get_current_tenant(fastapi_request, db)
        set_tenant_context(db, str(tenant.id))

        category_svc = CategoryService(db, tenant.id)
        with safe_transaction(db):
            category = category_svc.update_category(
                category_id=uuid.UUID(category_id),
                name=data.name,
                description=data.description,
            )
        return CategoryResponse.model_validate(category)
    except ValueError as e:
        raise HTTPException(400, str(e))
    except HTTPException:
        raise
    except Exception as e:
        logger.error("update_category failed: %s", e)
        raise



@router.delete("/categories/{category_id}")
def delete_category(
    category_id: str,
    db: Session = Depends(get_db),
    fastapi_request: Request = None,
) -> dict:
    try:
        tenant = get_current_tenant(fastapi_request, db)
        set_tenant_context(db, str(tenant.id))

        category_svc = CategoryService(db, tenant.id)
        with safe_transaction(db):
            deleted = category_svc.delete_category(uuid.UUID(category_id))
        if not deleted:
            raise HTTPException(404, "Category not found")
        return {"status": "deleted", "id": category_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("delete_category failed: %s", e)
        raise


# ── KB Categories CRUD ────────────────────────────────────────────────────────



