from __future__ import annotations

import uuid

from sqlalchemy.orm import Session
from models.category import Category


class CategoryRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def find_by_tenant_id(
        self,
        tenant_id: uuid.UUID,
        skip: int = 0,
        limit: int = 50,
    ) -> list[Category]:
        return (
            self.db.query(Category)
            .filter(Category.tenant_id == tenant_id)
            .order_by(Category.name)
            .offset(skip)
            .limit(limit)
            .all()
        )

    def find_by_id_and_tenant(
        self,
        category_id: uuid.UUID,
        tenant_id: uuid.UUID,
    ) -> Category | None:
        return (
            self.db.query(Category)
            .filter(Category.id == category_id, Category.tenant_id == tenant_id)
            .first()
        )

    def find_by_name_and_tenant(
        self,
        name: str,
        tenant_id: uuid.UUID,
    ) -> Category | None:
        return (
            self.db.query(Category)
            .filter(Category.name.ilike(name.strip()), Category.tenant_id == tenant_id)
            .first()
        )

    def save(self, category: Category) -> Category:
        self.db.add(category)
        self.db.flush()
        return category

    def delete(self, category: Category) -> None:
        self.db.delete(category)
        self.db.flush()
