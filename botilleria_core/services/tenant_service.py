from __future__ import annotations

import logging
import uuid
from typing import Any

from sqlalchemy.orm import Session

from models.tenant import Tenant
from models.channel_route import ChannelRoute
from repositories.tenant_repository import TenantRepository
from repositories.channel_route_repository import ChannelRouteRepository
from exceptions.tenant_exceptions import TenantNotFoundError

logger = logging.getLogger(__name__)

def get_levenshtein_distance(s1: str, s2: str) -> int:
    if len(s1) < len(s2):
        return get_levenshtein_distance(s2, s1)
    if len(s2) == 0:
        return len(s1)
    
    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row
        
    return previous_row[-1]


class TenantService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.tenant_repo = TenantRepository(db)
        self.channel_repo = ChannelRouteRepository(db)

    def resolve_tenant(
        self,
        platform: str,
        channel_identifier: str,
    ) -> Tenant | None:
        try:
            route = self.channel_repo.find_by_platform_and_channel(
                platform, channel_identifier
            )
            if not route:
                return None

            tenant = self.tenant_repo.find_by_id_and_active(route.tenant_id)
            return tenant
        except Exception as e:
            logger.error(
                "TenantService.resolve_tenant failed [platform=%s, channel=%s]: %s",
                platform,
                channel_identifier,
                e,
            )
            raise

    def get_tenant_by_id(self, tenant_id: uuid.UUID) -> Tenant | None:
        try:
            return self.tenant_repo.find_by_id_and_active(tenant_id)
        except Exception as e:
            logger.error(
                "TenantService.get_tenant_by_id failed [tenant_id=%s]: %s", tenant_id, e
            )
            raise

    def get_tenant_by_slug(self, slug: str) -> Tenant | None:
        try:
            return self.tenant_repo.find_by_slug(slug)
        except Exception as e:
            logger.error(
                "TenantService.get_tenant_by_slug failed [slug=%s]: %s", slug, e
            )
            raise

    def validate_slug(self, slug: str, exclude_id: uuid.UUID | None = None) -> str:
        slug_clean = slug.strip().lower()
        
        # Check exact match
        existing = self.get_tenant_by_slug(slug_clean)
        if existing and (exclude_id is None or existing.id != exclude_id):
            raise ValueError(f"Ya existe un tenant con el slug '{slug_clean}'")

        # Check similarity (Levenshtein distance <= 1)
        existing_tenants = self.tenant_repo.find_all(limit=1000)
        for t in existing_tenants:
            if exclude_id and t.id == exclude_id:
                continue
            if get_levenshtein_distance(slug_clean, t.slug.lower()) <= 1:
                raise ValueError(
                    f"El slug '{slug_clean}' es extremadamente similar al slug existente '{t.slug}'. "
                    "Elige un slug más diferente para evitar confusiones."
                )
        return slug_clean

    def create_tenant(
        self,
        slug: str,
        name: str,
        config: dict[str, Any],
    ) -> Tenant:
        try:
            slug_clean = self.validate_slug(slug)
            tenant = Tenant(slug=slug_clean, name=name, config=config)
            return self.tenant_repo.save(tenant)
        except Exception as e:
            logger.error("TenantService.create_tenant failed [slug=%s]: %s", slug, e)
            raise

    def add_channel_route(
        self,
        tenant_id: uuid.UUID,
        platform: str,
        channel_identifier: str,
    ) -> ChannelRoute:
        try:
            tenant = self.tenant_repo.find_by_id_and_active(tenant_id)
            if not tenant:
                raise TenantNotFoundError(tenant_id)

            route = ChannelRoute(
                tenant_id=tenant_id,
                platform=platform,
                channel_identifier=channel_identifier,
            )
            return self.channel_repo.save(route)
        except Exception as e:
            logger.error(
                "TenantService.add_channel_route failed [tenant_id=%s, platform=%s]: %s",
                tenant_id,
                platform,
                e,
            )
            raise

    def list_active_tenants(self) -> list[Tenant]:
        try:
            return self.tenant_repo.find_all_active()
        except Exception as e:
            logger.error("TenantService.list_active_tenants failed: %s", e)
            raise
