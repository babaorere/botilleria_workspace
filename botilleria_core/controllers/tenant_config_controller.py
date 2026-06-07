from __future__ import annotations

import logging
from typing import Optional
from pydantic import BaseModel

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy.orm import Session

from config.database import get_db, set_tenant_context, safe_transaction
from dtos.response.conversation_response import (
    ConversationQueueItemResponse,
    MessageResponse,
)
from services import (
    TenantService,
    UserService,
    ConversationService,
    AnalyticsService,
)
from dtos.request import (
    TenantProfileUpdateRequest,
)
from dtos.response import (
    TenantProfileResponse,
    ChannelRouteResponse,
)
from controllers.dependencies import get_current_tenant

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/tenants/me", tags=["tenant_config_controller"])


@router.get("/profile", response_model=TenantProfileResponse)
def get_profile(
    db: Session = Depends(get_db),
    fastapi_request: Request = None,
) -> TenantProfileResponse:
    try:
        tenant = get_current_tenant(fastapi_request, db)
        set_tenant_context(db, str(tenant.id))
        return TenantProfileResponse.model_validate(tenant)
    except HTTPException:
        raise
    except Exception as e:
        logger.error("get_profile failed: %s", e)
        raise


@router.put("/profile", response_model=TenantProfileResponse)
def update_profile(
    data: TenantProfileUpdateRequest,
    db: Session = Depends(get_db),
    fastapi_request: Request = None,
) -> TenantProfileResponse:
    try:
        tenant = get_current_tenant(fastapi_request, db)
        set_tenant_context(db, str(tenant.id))

        with safe_transaction(db):
            if data.name is not None:
                tenant.name = data.name
            if data.email is not None:
                tenant.email = data.email
            if data.phone is not None:
                tenant.phone = data.phone
            if data.address is not None:
                tenant.address = data.address
            if data.city is not None:
                tenant.city = data.city
            if data.website is not None:
                tenant.website = data.website
            if data.logo_url is not None:
                tenant.logo_url = data.logo_url
            if data.business_hours is not None:
                tenant.business_hours = data.business_hours
            if data.human_available is not None:
                tenant.config["human_available"] = data.human_available
                from sqlalchemy.orm.attributes import flag_modified

                flag_modified(tenant, "config")

            db.flush()
            db.refresh(tenant)

        return TenantProfileResponse.model_validate(tenant)
    except HTTPException:
        raise
    except Exception as e:
        logger.error("update_profile failed: %s", e)
        raise


# ── Channels ─────────────────────────────────────────────────────────────────


@router.get("/channels", response_model=list[ChannelRouteResponse])
def list_channels(
    db: Session = Depends(get_db),
    fastapi_request: Request = None,
) -> list[ChannelRouteResponse]:
    try:
        tenant = get_current_tenant(fastapi_request, db)
        set_tenant_context(db, str(tenant.id))

        tenant_service = TenantService(db)
        routes = tenant_service.channel_repo.find_by_tenant_id(tenant.id)
        return [ChannelRouteResponse.model_validate(r) for r in routes]
    except HTTPException:
        raise
    except Exception as e:
        logger.error("list_channels failed: %s", e)
        raise


# ── Products ─────────────────────────────────────────────────────────────────


@router.get("/users/count")
def get_user_count(
    db: Session = Depends(get_db),
    fastapi_request: Request = None,
) -> dict:
    try:
        tenant = get_current_tenant(fastapi_request, db)
        set_tenant_context(db, str(tenant.id))

        user_svc = UserService(db, tenant.id)
        count = user_svc.repo.count_by_tenant(tenant.id)
        return {"count": count}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("get_user_count failed: %s", e)
        raise


@router.get("/conversations/count")
def get_conversation_count(
    db: Session = Depends(get_db),
    fastapi_request: Request = None,
) -> dict:
    try:
        tenant = get_current_tenant(fastapi_request, db)
        set_tenant_context(db, str(tenant.id))

        conv_svc = ConversationService(db, tenant.id)
        count = conv_svc.repo.count_by_tenant(tenant.id)
        return {"count": count}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("get_conversation_count failed: %s", e)
        raise


@router.get("/analytics")
def get_analytics(
    db: Session = Depends(get_db),
    fastapi_request: Request = None,
) -> dict:
    try:
        tenant = get_current_tenant(fastapi_request, db)
        set_tenant_context(db, str(tenant.id))

        analytics_svc = AnalyticsService(db, tenant.id)
        basic = analytics_svc.get_basic_metrics()
        sales = analytics_svc.get_sales_metrics()

        return {"basic": basic, "lost_sales": sales}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("get_analytics failed: %s", e)
        raise


# ── Categories CRUD ──────────────────────────────────────────────────────────


class ConversationStateUpdateRequest(BaseModel):
    state: str


@router.get("/conversations", response_model=list[ConversationQueueItemResponse])
def get_conversations(
    state: str = Query("all_human"),
    search: Optional[str] = Query(None),
    sort_by: str = Query("created_at"),
    sort_order: str = Query("asc"),
    db: Session = Depends(get_db),
    fastapi_request: Request = None,
) -> list[ConversationQueueItemResponse]:
    try:
        tenant = get_current_tenant(fastapi_request, db)
        set_tenant_context(db, str(tenant.id))

        from models.conversation import Conversation
        from models.user import User
        from models.message import Message
        from sqlalchemy import or_

        query = db.query(Conversation).filter(Conversation.tenant_id == tenant.id)
        query = query.join(User, Conversation.user_id == User.id)

        if state == "all_human":
            query = query.filter(
                Conversation.state.in_(
                    ["ESPERANDO_HUMANO", "HUMANO_ATENDIENDO", "POSPUESTA", "CANCELADA"]
                )
            )
        elif state and state != "all":
            query = query.filter(Conversation.state == state)

        if search:
            search_term = f"%{search.strip()}%"
            query = query.filter(
                or_(
                    User.display_name.ilike(search_term),
                    User.external_id.ilike(search_term),
                )
            )

        if sort_by == "user_name":
            if sort_order == "desc":
                query = query.order_by(User.display_name.desc())
            else:
                query = query.order_by(User.display_name.asc())
        else:  # default to arrival time (created_at)
            if sort_order == "desc":
                query = query.order_by(Conversation.created_at.desc())
            else:
                query = query.order_by(Conversation.created_at.asc())

        conversations = query.all()
        result = []
        for conv in conversations:
            # Get last message
            last_msg = (
                db.query(Message)
                .filter(Message.conversation_id == conv.id)
                .order_by(Message.created_at.desc())
                .first()
            )
            result.append(
                ConversationQueueItemResponse(
                    id=conv.id,
                    session_id=conv.session_id,
                    state=conv.state,
                    version=conv.version,
                    created_at=conv.created_at,
                    user_id=conv.user_id,
                    user_external_id=conv.user.external_id,
                    user_display_name=conv.user.display_name,
                    user_platform=conv.user.platform,
                    last_message=last_msg.content if last_msg else None,
                    last_message_time=last_msg.created_at if last_msg else None,
                )
            )
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error("get_conversations failed: %s", e)
        raise


@router.put("/conversations/{session_id}/state")
def update_conversation_state(
    session_id: str,
    data: ConversationStateUpdateRequest,
    db: Session = Depends(get_db),
    fastapi_request: Request = None,
):
    try:
        tenant = get_current_tenant(fastapi_request, db)
        set_tenant_context(db, str(tenant.id))

        from models.conversation import Conversation

        conv = (
            db.query(Conversation)
            .filter(
                Conversation.session_id == session_id,
                Conversation.tenant_id == tenant.id,
            )
            .first()
        )

        if not conv:
            raise HTTPException(404, "Conversation not found")

        try:
            conv.transition_to(data.state)
            db.flush()
            db.commit()
        except ValueError as e:
            raise HTTPException(400, str(e))

        return {"status": "success", "state": conv.state}
    except HTTPException:
        raise
    except Exception as e:
        logger.error("update_conversation_state failed: %s", e)
        raise


@router.get(
    "/conversations/{session_id}/messages", response_model=list[MessageResponse]
)
def get_conversation_messages(
    session_id: str,
    db: Session = Depends(get_db),
    fastapi_request: Request = None,
) -> list[MessageResponse]:
    try:
        tenant = get_current_tenant(fastapi_request, db)
        set_tenant_context(db, str(tenant.id))

        from models.conversation import Conversation
        from models.message import Message

        conv = (
            db.query(Conversation)
            .filter(
                Conversation.session_id == session_id,
                Conversation.tenant_id == tenant.id,
            )
            .first()
        )

        if not conv:
            raise HTTPException(404, "Conversation not found")

        messages = (
            db.query(Message)
            .filter(Message.conversation_id == conv.id)
            .order_by(Message.created_at.asc())
            .all()
        )
        return [MessageResponse.model_validate(m) for m in messages]
    except HTTPException:
        raise
    except Exception as e:
        logger.error("get_conversation_messages failed: %s", e)
        raise
