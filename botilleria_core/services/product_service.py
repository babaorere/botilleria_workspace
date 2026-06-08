from __future__ import annotations

import logging
import re
import uuid

from sqlalchemy.orm import Session

from models.product import Product
from repositories.product_repository import ProductRepository

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


def parse_presentation(name: str) -> str | None:
    # Patrón para volumen/formato (ej. 500cc, 1L, botella, lata)
    pattern = r'\b\d+(?:\.\d+)?\s*(?:ml|cc|cl|l|gr|g|kg|oz|lt|lts)\b|\b(?:lata|botella|pack|caja|retornable|desechable|lts?|grs?|kgs?)\b'
    matches = re.findall(pattern, name, re.IGNORECASE)
    if matches:
        return " ".join(matches).lower()
    return None


def check_product_name_policy(new_name: str, existing_products: list[Product], exclude_id: uuid.UUID | None = None) -> None:
    new_name_clean = new_name.strip()
    new_name_lower = new_name_clean.lower()
    new_pres = parse_presentation(new_name_clean)
    
    # 1. Validación de duplicado exacto
    for p in existing_products:
        if exclude_id and p.id == exclude_id:
            continue
        if p.name.strip().lower() == new_name_lower:
            raise ValueError(
                f"Ya existe un producto con el nombre exacto '{p.name}'. "
                "Si se trata de otra presentación, incluye el formato o volumen "
                "(ej. 'Cristal 500cc' en lugar de sólo 'Cristal')."
            )
            
    # 2. Validación de similitud y desambiguación de presentación
    # Limpiamos los patrones de presentación para extraer el nombre base
    def get_base_name(name: str) -> str:
        pattern = r'\b\d+(?:\.\d+)?\s*(?:ml|cc|cl|l|gr|g|kg|oz|lt|lts)\b|\b(?:lata|botella|pack|caja|retornable|desechable|lts?|grs?|kgs?)\b'
        base = re.sub(pattern, '', name, flags=re.IGNORECASE)
        base = re.sub(r'[^\w\s]', ' ', base)
        base = re.sub(r'\s+', ' ', base).strip().lower()
        return base

    new_base = get_base_name(new_name_clean)
    
    for p in existing_products:
        if exclude_id and p.id == exclude_id:
            continue
        p_name_clean = p.name.strip()
        p_base = get_base_name(p_name_clean)
        
        # Si los nombres base son idénticos o extremadamente similares (distancia <= 1)
        if new_base == p_base or get_levenshtein_distance(new_base, p_base) <= 1:
            p_pres = parse_presentation(p_name_clean)
            
            # Ambos deben tener especificadores de presentación para diferenciarse
            if not new_pres or not p_pres:
                raise ValueError(
                    f"El nombre '{new_name_clean}' es ambiguo con el producto existente '{p.name}'. "
                    "Ambos deben especificar explícitamente su formato/presentación "
                    "para diferenciarse (ej. 'Cristal 500cc' y 'Cristal 1L')."
                )
            if new_pres == p_pres:
                raise ValueError(
                    f"El producto '{new_name_clean}' tiene el mismo formato/presentación "
                    f"('{new_pres}') que el producto existente '{p.name}'."
                )


class ProductService:
    def __init__(self, db: Session, tenant_id: uuid.UUID) -> None:
        self.db = db
        self.tenant_id = tenant_id
        self.repo = ProductRepository(db)

    def list_products(
        self,
        category: str | None = None,
        available_only: bool = False,
        skip: int = 0,
        limit: int = 50,
    ) -> list[Product]:
        try:
            return self.repo.find_by_tenant_id(
                self.tenant_id,
                category=category,
                available_only=available_only,
                skip=skip,
                limit=limit,
            )
        except Exception as e:
            logger.error(
                "ProductService.list_products failed [tenant=%s]: %s", self.tenant_id, e
            )
            raise

    def get_product(self, product_id: uuid.UUID) -> Product | None:
        try:
            return self.repo.find_by_id_and_tenant(product_id, self.tenant_id)
        except Exception as e:
            logger.error(
                "ProductService.get_product failed [id=%s, tenant=%s]: %s",
                product_id,
                self.tenant_id,
                e,
            )
            raise

    def create_product(
        self,
        name: str,
        description: str | None = None,
        price: float | None = None,
        stock: int = 0,
        category: str | None = None,
        is_available: bool = True,
    ) -> Product:
        try:
            # Validar la política de nombre del producto
            existing_products = self.repo.find_by_tenant_id(self.tenant_id, limit=1000)
            check_product_name_policy(name, existing_products)

            product = Product(
                tenant_id=self.tenant_id,
                name=name,
                description=description,
                price=price,
                stock=stock,
                category=category,
                is_available=is_available,
            )
            return self.repo.save(product)
        except Exception as e:
            logger.error(
                "ProductService.create_product failed [tenant=%s, name=%s]: %s",
                self.tenant_id,
                name,
                e,
            )
            raise

    def update_product(
        self,
        product_id: uuid.UUID,
        name: str | None = None,
        description: str | None = None,
        price: float | None = None,
        stock: int | None = None,
        category: str | None = None,
        is_available: bool | None = None,
    ) -> Product:
        try:
            product = self.repo.find_by_id_and_tenant(product_id, self.tenant_id)
            if not product:
                raise ValueError(
                    f"Product {product_id} not found for tenant {self.tenant_id}"
                )

            if name is not None:
                # Validar la política de nombre del producto excluyendo el producto actual
                existing_products = self.repo.find_by_tenant_id(self.tenant_id, limit=1000)
                check_product_name_policy(name, existing_products, exclude_id=product_id)
                product.name = name
            if description is not None:
                product.description = description
            if price is not None:
                product.price = price
            if stock is not None:
                product.stock = stock
            if category is not None:
                product.category = category
            if is_available is not None:
                product.is_available = is_available

            self.db.flush()
            self.db.refresh(product)
            return product
        except Exception as e:
            logger.error(
                "ProductService.update_product failed [id=%s, tenant=%s]: %s",
                product_id,
                self.tenant_id,
                e,
            )
            raise

    def delete_product(self, product_id: uuid.UUID) -> bool:
        try:
            product = self.repo.find_by_id_and_tenant(product_id, self.tenant_id)
            if not product:
                return False
            self.db.delete(product)
            self.db.flush()
            return True
        except Exception as e:
            logger.error(
                "ProductService.delete_product failed [id=%s, tenant=%s]: %s",
                product_id,
                self.tenant_id,
                e,
            )
            raise

    def search(self, query: str, limit: int = 20) -> list[Product]:
        try:
            return self.repo.search_by_name(self.tenant_id, query, limit=limit)
        except Exception as e:
            logger.error(
                "ProductService.search failed [tenant=%s, query=%s]: %s",
                self.tenant_id,
                query,
                e,
            )
            raise

    def get_categories(self) -> list[str]:
        try:
            return self.repo.get_categories_by_tenant(self.tenant_id)
        except Exception as e:
            logger.error(
                "ProductService.get_categories failed [tenant=%s]: %s",
                self.tenant_id,
                e,
            )
            raise

    def count(self, category: str | None = None, available_only: bool = False) -> int:
        try:
            return self.repo.count_by_tenant(
                self.tenant_id, category=category, available_only=available_only
            )
        except Exception as e:
            logger.error(
                "ProductService.count failed [tenant=%s]: %s", self.tenant_id, e
            )
            raise
