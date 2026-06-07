import re

source = "/home/manager/Sync/python_proyects/botilleria_workspace/botilleria_core/controllers/tenant_portal_controller.py"

with open(source, "r") as f:
    content = f.read()

# Shared imports header
imports = """from __future__ import annotations

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
"""

# Extract the endpoints using regex matching
# An endpoint typically looks like @router.get(...)
# We can find all chunks starting with @router. and ending before the next @router. (or end of file)
chunks = re.split(r"(?=@router\.)", content)

config_endpoints = []
products_endpoints = []
kb_endpoints = []

for chunk in chunks:
    if not chunk.startswith("@router."):
        continue

    first_line = chunk.split("\\n")[0]
    if (
        "/profile" in first_line
        or "/channels" in first_line
        or "/users/count" in first_line
        or "/conversations/count" in first_line
        or "/analytics" in first_line
    ):
        config_endpoints.append(chunk)
    elif "/products" in first_line or "/categories" in first_line:
        if "kb-categories" in first_line or "/kb/" in first_line:
            kb_endpoints.append(chunk)
        else:
            products_endpoints.append(chunk)
    elif "/kb" in first_line:
        kb_endpoints.append(chunk)
    else:
        # fallback
        config_endpoints.append(chunk)


def write_controller(name, endpoints):
    path = f"/home/manager/Sync/python_proyects/botilleria_workspace/botilleria_core/controllers/{name}.py"
    with open(path, "w") as f:
        f.write(imports)
        f.write(f'\nrouter = APIRouter(prefix="/tenants/me", tags=["{name}"])\n\n')
        for ep in endpoints:
            f.write(ep)
            f.write("\n")


write_controller("tenant_config_controller", config_endpoints)
write_controller("tenant_products_controller", products_endpoints)
write_controller("tenant_kb_controller", kb_endpoints)

print("Split successful.")
