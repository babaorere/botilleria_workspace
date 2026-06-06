from __future__ import annotations

import asyncio
import logging

from fastapi import APIRouter, Depends, Request, BackgroundTasks, HTTPException, status
from sqlalchemy.orm import Session
from sse_starlette.sse import EventSourceResponse

from config.database import get_db, set_tenant_context
from config.settings import settings

from services import (
    LLMService,
    ChatService,
    TenantService,
    KBService,
    RAGContextBuilder,
    RateLimiter,
)
from exceptions.llm_exceptions import LLMProviderError
from dtos.request import ChatRequest
from dtos.response import ChatResponse


def get_rate_limiter(request: Request) -> RateLimiter:
    return request.app.state.rate_limiter


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["chat"])


async def resolve_tenant_from_request(
    request: Request,
    db: Session,
):
    tenant_service = TenantService(db)

    tenant_id_header = request.headers.get("X-Tenant-ID")
    if tenant_id_header:
        import uuid

        try:
            tenant_id = uuid.UUID(tenant_id_header)
        except ValueError as e:
            logger.warning(
                "Invalid X-Tenant-ID header format: %s — %s", tenant_id_header, e
            )
            raise HTTPException(401, "Invalid X-Tenant-ID format") from e

        tenant = await asyncio.to_thread(tenant_service.get_tenant_by_id, tenant_id)
        if not tenant:
            logger.warning("Tenant not found or inactive: %s", tenant_id)
            raise HTTPException(403, f"Tenant {tenant_id} not found or inactive")
        return tenant

    platform = request.headers.get("X-Platform")
    channel_identifier = request.headers.get("X-Channel-Identifier")

    if platform and channel_identifier:
        tenant = await asyncio.to_thread(
            tenant_service.resolve_tenant, platform, channel_identifier
        )
        if not tenant:
            logger.warning(
                "No channel route found: platform=%s, channel=%s",
                platform,
                channel_identifier,
            )
            raise HTTPException(
                403,
                f"No route found for platform={platform}, channel={channel_identifier}",
            )
        return tenant

    logger.warning("Missing tenant resolution headers on request: %s", request.url.path)
    raise HTTPException(401, "Missing X-Tenant-ID or channel mapping headers")


@router.post("", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    llm: LLMService = Depends(lambda: None),
    fastapi_request: Request = None,
    rate_limiter: RateLimiter = Depends(get_rate_limiter),
) -> ChatResponse:
    try:
        tenant = await resolve_tenant_from_request(fastapi_request, db)

        # Resolve rate_limiter if it was not injected (direct call in unit tests)
        if type(rate_limiter).__name__ == "Depends":
            if (
                fastapi_request
                and type(fastapi_request).__name__
                not in ("MagicMock", "Mock", "AsyncMock")
                and hasattr(fastapi_request, "app")
                and hasattr(fastapi_request.app.state, "rate_limiter")
            ):
                rate_limiter = fastapi_request.app.state.rate_limiter
            else:
                rate_limiter = RateLimiter(redis_client=None)

        # Rate Limiting Check
        is_limited = await rate_limiter.is_rate_limited(
            tenant_id=str(tenant.id),
            user_id=request.user_id,
            limit=settings.rate_limit_chat_max_requests,
            window=settings.rate_limit_chat_window_seconds,
        )
        if is_limited:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Demasiadas solicitudes. Por favor, intenta de nuevo más tarde.",
            )

        set_tenant_context(db, str(tenant.id))

        kb_service = KBService(db, tenant.id)
        rag_builder = RAGContextBuilder(kb_service)
        rag_context = await rag_builder.build_context(request.message, top_k=5)

        chat_service = ChatService(db, llm, background_tasks)
        try:
            session_id, response_text = await chat_service.process_message(
                tenant=tenant,
                user_id=request.user_id,
                platform=request.platform,
                message=request.message,
                session_id=request.session_id,
                rag_context=rag_context,
            )

            return ChatResponse(
                session_id=session_id,
                user_id=request.user_id,
                tenant_slug=tenant.slug,
                response=response_text,
            )
        except LLMProviderError as e:
            request_id = (
                getattr(fastapi_request.state, "request_id", "unknown")
                if fastapi_request
                else "unknown"
            )
            logger.warning(
                "LLM Provider fallback triggered [request_id=%s]: %s", request_id, e
            )
            import uuid

            fallback_session_id = request.session_id or str(uuid.uuid4())
            return ChatResponse(
                session_id=fallback_session_id,
                user_id=request.user_id,
                tenant_slug=tenant.slug,
                response="Disculpa, en este momento estoy revisando la bodega y no puedo responder. ¿Podrías intentar en unos minutos?",
            )
    except Exception as e:
        request_id = (
            getattr(fastapi_request.state, "request_id", "unknown")
            if fastapi_request
            else "unknown"
        )
        logger.error("Chat endpoint failed [request_id=%s]: %s", request_id, e)
        raise


@router.post("/stream")
async def chat_stream(
    request: ChatRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    llm: LLMService = Depends(lambda: None),
    fastapi_request: Request = None,
    rate_limiter: RateLimiter = Depends(get_rate_limiter),
) -> EventSourceResponse:
    try:
        tenant = await resolve_tenant_from_request(fastapi_request, db)

        # Resolve rate_limiter if it was not injected (direct call in unit tests)
        if type(rate_limiter).__name__ == "Depends":
            if (
                fastapi_request
                and type(fastapi_request).__name__
                not in ("MagicMock", "Mock", "AsyncMock")
                and hasattr(fastapi_request, "app")
                and hasattr(fastapi_request.app.state, "rate_limiter")
            ):
                rate_limiter = fastapi_request.app.state.rate_limiter
            else:
                rate_limiter = RateLimiter(redis_client=None)

        # Rate Limiting Check
        is_limited = await rate_limiter.is_rate_limited(
            tenant_id=str(tenant.id),
            user_id=request.user_id,
            limit=settings.rate_limit_chat_max_requests,
            window=settings.rate_limit_chat_window_seconds,
        )
        if is_limited:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Demasiadas solicitudes. Por favor, intenta de nuevo más tarde.",
            )

        set_tenant_context(db, str(tenant.id))

        kb_service = KBService(db, tenant.id)
        rag_builder = RAGContextBuilder(kb_service)
        rag_context = await rag_builder.build_context(request.message, top_k=5)

        chat_service = ChatService(db, llm, background_tasks)
        session_id, chat_stream_gen = await chat_service.process_message_stream(
            tenant=tenant,
            user_id=request.user_id,
            platform=request.platform,
            message=request.message,
            session_id=request.session_id,
            rag_context=rag_context,
        )

        async def event_generator():
            try:
                async for chunk in chat_stream_gen:
                    yield {"event": "chunk", "data": chunk}
                yield {"event": "done", "data": session_id}
            except LLMProviderError as e:
                request_id = (
                    getattr(fastapi_request.state, "request_id", "unknown")
                    if fastapi_request
                    else "unknown"
                )
                logger.warning(
                    "LLM Provider stream fallback triggered [request_id=%s]: %s",
                    request_id,
                    e,
                )
                yield {
                    "event": "chunk",
                    "data": "Disculpa, en este momento estoy revisando la bodega y no puedo responder. ¿Podrías intentar en unos minutos?",
                }
                yield {"event": "done", "data": session_id}

        return EventSourceResponse(event_generator())
    except Exception as e:
        request_id = (
            getattr(fastapi_request.state, "request_id", "unknown")
            if fastapi_request
            else "unknown"
        )
        logger.error("Chat stream endpoint failed [request_id=%s]: %s", request_id, e)
        raise
