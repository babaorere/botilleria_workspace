from __future__ import annotations

import uuid

from sqlalchemy.orm import Session
from models.kb_category import KBCategory


class KBCategoryRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def find_by_tenant_id(
        self,
        tenant_id: uuid.UUID,
        skip: int = 0,
        limit: int = 50,
    ) -> list[KBCategory]:
        return (
            self.db.query(KBCategory)
            .filter(KBCategory.tenant_id == tenant_id)
            .order_by(KBCategory.name)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def find_by_id_and_tenant(
        self,
        category_id: uuid.UUID,
        tenant_id: uuid.UUID,
    ) -> KBCategory | None:
        return (
            self.db.query(KBCategory)
            .filter(KBCategory.id == category_id, KBCategory.tenant_id == tenant_id)
            .first()
        )

    def find_by_name_and_tenant(
        self,
        name: str,
        tenant_id: uuid.UUID,
    ) -> KBCategory | None:
        return (
            self.db.query(KBCategory)
            .filter(KBCategory.name.ilike(name.strip()), KBCategory.tenant_id == tenant_id)
            .first()
        )

    def save(self, category: KBCategory) -> KBCategory:
        self.db.add(category)
        self.db.flush()
        return category

    def delete(self, category: KBCategory) -> None:
        self.db.delete(category)
        self.db.flush()
