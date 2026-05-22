from __future__ import annotations

from pydantic import BaseModel


class TenantProfileResponse(BaseModel):
    id: str
    slug: str
    name: str
    email: str | None
    phone: str | None
    address: str | None
    city: str | None
    website: str | None
    logo_url: str | None
    business_hours: dict | None
    status: str

    model_config = {"from_attributes": True}


class ProductResponse(BaseModel):
    id: str
    name: str
    description: str | None
    price: float | None
    stock: int
    category: str | None
    is_available: bool

    model_config = {"from_attributes": True}


class KBEntryResponse(BaseModel):
    id: str
    category: str
    title: str
    content: str
    is_active: bool

    model_config = {"from_attributes": True}


class KBSearchResultItem(BaseModel):
    id: str
    category: str
    title: str
    content: str
    rank: float


class KBSearchResponse(BaseModel):
    query: str
    results: list[KBSearchResultItem]
    count: int


class CategoryCountResponse(BaseModel):
    category: str
    count: int
