from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from config.database import _sync_engine, Base, enable_rls_on_startup, SessionLocal
from config.settings import settings
from models import Tenant  # noqa: F401
from services import TenantService, LLMService, create_llm_service
from exceptions import register_exception_handlers
from middleware import RequestIdMiddleware
from controllers import (
    health_router,
    chat_router,
    tenant_router,
    user_router,
    session_router,
    tenant_portal_router,
    admin_router,
)

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

_llm_service: LLMService | None = None


def get_llm_service() -> LLMService:
    assert _llm_service is not None, "LLMService not initialized"
    return _llm_service


def seed_default_tenant(db: Session) -> None:
    tenant_service = TenantService(db)
    existing = tenant_service.list_active_tenants()
    if existing:
        return

    default_tenant = tenant_service.create_tenant(
        slug="el_buen_trago",
        name="Botillería El Buen Trago",
        config={
            "instruction": (
                "Eres el asistente virtual de la Botillería El Buen Trago. "
                "Tu rol es atender consultas de clientes, ayudar con pedidos de productos, "
                "resolver dudas sobre horarios y disponibilidad, y mantener un tono amable y profesional.\n\n"
                "INFORMACIÓN DE LA BOTILLERÍA:\n"
                "- Horario: Lunes a Sábado 10:00-22:00, Domingo 12:00-20:00\n"
                "- Servicios: Venta de licores, cervezas artesanales, vinos, pedidos a domicilio\n"
                "- Ubicación: Santiago, Chile\n\n"
                "REGLAS:\n"
                "1. NUNCA inventes precios ni stock. Si no sabes algo, sé honesto.\n"
                "2. Si te preguntan por disponibilidad, indica que consultarás y responderás pronto.\n"
                "3. Mantén un tono amable, profesional y cercano.\n"
                "4. Si el usuario pide algo fuera de scope, ofrece contactar a un humano.\n"
                "5. Responde en español siempre."
            ),
            "model": "openrouter/nvidia/nemotron-3-super-120b-a12b:free",
            "api_key": os.getenv("OPENROUTER_API_KEY", ""),
            "products": [],
        },
    )
    tenant_service.add_channel_route(
        tenant_id=default_tenant.id,
        platform="telegram",
        channel_identifier=os.getenv("TELEGRAM_BOT_TOKEN", "default_token"),
    )
    logger.info("Default tenant created: el_buen_trago")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    global _llm_service

    Base.metadata.create_all(bind=_sync_engine)
    logger.info("DB tables created")

    with _sync_engine.begin() as conn:
        enable_rls_on_startup(conn)
    logger.info("Row-Level Security policies enabled")

    with SessionLocal() as seed_db:
        seed_default_tenant(seed_db)
        seed_db.commit()

    _llm_service = create_llm_service()
    logger.info(
        "LLMService initialized — worker PID=%s, model=%s",
        os.getpid(),
        settings.model_display,
    )

    yield

    _llm_service = None
    logger.info("LLMService shut down")


app = FastAPI(
    title="Botilleria Core (Multi-Tenant)",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(RequestIdMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_exception_handlers(app)

app.include_router(health_router)
app.include_router(chat_router)
app.include_router(tenant_router)
app.include_router(user_router)
app.include_router(session_router)
app.include_router(tenant_portal_router)
app.include_router(admin_router)
