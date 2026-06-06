from __future__ import annotations

import logging
import uuid

from sqlalchemy.orm import Session
from config.database import safe_transaction
from models.kb_category import KBCategory
from models.knowledge_base import KnowledgeBase
from repositories.kb_category_repository import KBCategoryRepository
from .spell_corrector import KBSpellCorrector

logger = logging.getLogger(__name__)


class KBCategoryService:
    def __init__(self, db: Session, tenant_id: uuid.UUID) -> None:
        self.db = db
        self.tenant_id = tenant_id
        self.repo = KBCategoryRepository(db)

    def list_categories(self, skip: int = 0, limit: int = 50) -> list[KBCategory]:
        try:
            cats = self.repo.find_by_tenant_id(self.tenant_id, skip=skip, limit=limit)
            if not cats and skip == 0:
                try:
                    with safe_transaction(self.db):
                        existing_general = self.repo.find_by_name_and_tenant("General", self.tenant_id)
                        if not existing_general:
                            general_cat = KBCategory(
                                tenant_id=self.tenant_id,
                                name="General",
                                description="Categoría de respuestas general por defecto",
                            )
                            self.repo.save(general_cat)
                            cats = [general_cat]
                        else:
                            cats = [existing_general]
                except Exception as e:
                    logger.error("Failed to auto-create 'General' KB category: %s", e)
            return cats
        except Exception as e:
            logger.error("KBCategoryService.list_categories failed: %s", e)
            raise

    def get_category(self, category_id: uuid.UUID) -> KBCategory | None:
        try:
            return self.repo.find_by_id_and_tenant(category_id, self.tenant_id)
        except Exception as e:
            logger.error("KBCategoryService.get_category failed: %s", e)
            raise

    def create_category(self, name: str, description: str | None = None) -> KBCategory:
        try:
            corrected_name = KBSpellCorrector.correct(name)

            existing = self.repo.find_by_name_and_tenant(corrected_name, self.tenant_id)
            if existing:
                raise ValueError(f"La categoría de respuesta '{corrected_name}' ya existe.")

            category = KBCategory(
                tenant_id=self.tenant_id,
                name=corrected_name,
                description=description,
            )
            return self.repo.save(category)
        except Exception as e:
            logger.error("KBCategoryService.create_category failed: %s", e)
            raise

    def update_category(
        self,
        category_id: uuid.UUID,
        name: str | None = None,
        description: str | None = None,
    ) -> KBCategory:
        try:
            category = self.repo.find_by_id_and_tenant(category_id, self.tenant_id)
            if not category:
                raise ValueError("Categoría de respuesta no encontrada.")

            if category.name == "General":
                raise ValueError("La categoría 'General' es del sistema y no se puede editar.")

            if name is not None:
                corrected_name = KBSpellCorrector.correct(name)
                if corrected_name == "General" and category.name != "General":
                    raise ValueError("No se puede renombrar una categoría de respuesta a 'General'.")
                existing = self.repo.find_by_name_and_tenant(corrected_name, self.tenant_id)
                if existing and existing.id != category_id:
                    raise ValueError(f"La categoría de respuesta '{corrected_name}' ya existe.")
                category.name = corrected_name

            if description is not None:
                category.description = description

            self.db.flush()
            self.db.refresh(category)
            return category
        except Exception as e:
            logger.error("KBCategoryService.update_category failed: %s", e)
            raise

    def delete_category(self, category_id: uuid.UUID) -> bool:
        try:
            category = self.repo.find_by_id_and_tenant(category_id, self.tenant_id)
            if not category:
                return False

            if category.name == "General":
                raise ValueError("La categoría 'General' es del sistema y no se puede eliminar.")

            category_name = category.name
            self.repo.delete(category)

            # Reassign all KB entries (KnowledgeBase) with this category name to "General"
            self.db.query(KnowledgeBase).filter(
                KnowledgeBase.tenant_id == self.tenant_id,
                KnowledgeBase.category == category_name
            ).update({"category": "General"}, synchronize_session=False)

            self.db.flush()
            return True
        except Exception as e:
            logger.error("KBCategoryService.delete_category failed: %s", e)
            raise
