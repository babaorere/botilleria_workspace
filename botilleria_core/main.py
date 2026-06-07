from __future__ import annotations

import logging
import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from redis.asyncio import Redis
from sqlalchemy.orm import Session

from config.database import _sync_engine, enable_rls_on_startup, SessionLocal
from config.redis import create_redis_client
from config.settings import settings
from models import Tenant, CartItem  # noqa: F401
from services import (
    TenantService,
    LLMService,
    create_llm_service,
    create_session_service,
    RateLimiter,
)
from exceptions import register_exception_handlers
from middleware import RequestIdMiddleware
from controllers import (
    health_router,
    chat_router,
    tenant_router,
    user_router,
    session_router,
    tenant_config_router,
    tenant_products_router,
    tenant_kb_router,
    admin_router,
    auth_router,
)

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

_llm_service: LLMService | None = None
_redis_client: Redis | None = None


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
            "model": "nvidia_nim/google/gemma-4-31b-it",
            "api_key": os.getenv("NVIDIA_API_KEY", "")
            or os.getenv("OPENROUTER_API_KEY", ""),
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
    global _redis_client

    # SQLAlchemy: create tables
    # Ahora usamos Alembic para las migraciones (ver alembic_migrations/)
    # Base.metadata.create_all(bind=_sync_engine)
    logger.info("DB tables created")

    with _sync_engine.begin() as conn:
        enable_rls_on_startup(conn)
    logger.info("Row-Level Security policies enabled")

    with SessionLocal() as seed_db:
        seed_default_tenant(seed_db)
        seed_db.commit()

    session_service = create_session_service(config=settings)
    if settings.use_redis_sessions:
        try:
            _redis_client = create_redis_client()
            await _redis_client.ping()
            session_service = create_session_service(
                config=settings,
                redis_client=_redis_client,
            )
            logger.info("Redis session backend initialized")
        except Exception as e:
            logger.error("Failed to initialize Redis session backend: %s", e)
            raise

    _llm_service = create_llm_service(session_service=session_service)
    app.state.rate_limiter = RateLimiter(redis_client=_redis_client)
    logger.info(
        "LLMService initialized — worker PID=%s, model=%s, session_backend=%s",
        os.getpid(),
        settings.model_display,
        settings.session_backend,
    )

    yield

    _llm_service = None
    if _redis_client is not None:
        await _redis_client.aclose()
        _redis_client = None
    logger.info("LLMService shut down")


app = FastAPI(
    title="Botilleria Core (Multi-Tenant)",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(RequestIdMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
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
app.include_router(tenant_config_router)
app.include_router(tenant_products_router)
app.include_router(tenant_kb_router)
app.include_router(admin_router)
app.include_router(auth_router)
