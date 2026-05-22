from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session
from sse_starlette.sse import EventSourceResponse

from config.database import get_db, set_tenant_context
from services import (
    LLMService,
    ChatService,
    TenantService,
    KBService,
    RAGContextBuilder,
)
from dtos.request import ChatRequest
from dtos.response import ChatResponse

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
            from fastapi import HTTPException

            raise HTTPException(401, "Invalid X-Tenant-ID format") from e

        tenant = tenant_service.get_tenant_by_id(tenant_id)
        if not tenant:
            logger.warning("Tenant not found or inactive: %s", tenant_id)
            from fastapi import HTTPException

            raise HTTPException(403, f"Tenant {tenant_id} not found or inactive")
        return tenant

    platform = request.headers.get("X-Platform")
    channel_identifier = request.headers.get("X-Channel-Identifier")

    if platform and channel_identifier:
        tenant = tenant_service.resolve_tenant(platform, channel_identifier)
        if not tenant:
            logger.warning(
                "No channel route found: platform=%s, channel=%s",
                platform,
                channel_identifier,
            )
            from fastapi import HTTPException

            raise HTTPException(
                403,
                f"No route found for platform={platform}, channel={channel_identifier}",
            )
        return tenant

    logger.warning("Missing tenant resolution headers on request: %s", request.url.path)
    from fastapi import HTTPException

    raise HTTPException(401, "Missing X-Tenant-ID or channel mapping headers")


@router.post("", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    db: Session = Depends(get_db),
    llm: LLMService = Depends(lambda: None),
    fastapi_request: Request = None,
) -> ChatResponse:
    try:
        tenant = await resolve_tenant_from_request(fastapi_request, db)
        set_tenant_context(db, str(tenant.id))

        kb_service = KBService(db, tenant.id)
        rag_builder = RAGContextBuilder(kb_service)
        rag_context = await rag_builder.build_context(request.message, top_k=5)

        chat_service = ChatService(db, llm)
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
    db: Session = Depends(get_db),
    llm: LLMService = Depends(lambda: None),
    fastapi_request: Request = None,
) -> EventSourceResponse:
    try:
        tenant = await resolve_tenant_from_request(fastapi_request, db)
        set_tenant_context(db, str(tenant.id))

        kb_service = KBService(db, tenant.id)
        rag_builder = RAGContextBuilder(kb_service)
        rag_context = await rag_builder.build_context(request.message, top_k=5)

        chat_service = ChatService(db, llm)

        async def event_generator():
            async for chunk in chat_service.process_message_stream(
                tenant=tenant,
                user_id=request.user_id,
                platform=request.platform,
                message=request.message,
                session_id=request.session_id,
                rag_context=rag_context,
            ):
                yield {"event": "chunk", "data": chunk}
            yield {"event": "done", "data": ""}

        return EventSourceResponse(event_generator())
    except Exception as e:
        request_id = (
            getattr(fastapi_request.state, "request_id", "unknown")
            if fastapi_request
            else "unknown"
        )
        logger.error("Chat stream endpoint failed [request_id=%s]: %s", request_id, e)
        raise
