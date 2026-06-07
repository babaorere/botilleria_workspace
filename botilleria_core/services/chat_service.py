from __future__ import annotations

import asyncio
import logging
import time
import uuid
from typing import AsyncGenerator

from fastapi import BackgroundTasks
from sqlalchemy.orm import Session

from config.database import SessionLocal, set_tenant_context
from models.message import Message
from models.tenant import Tenant
from services.conversation_service import ConversationService
from services.llm_service import LLMService
from services.user_service import UserService

logger = logging.getLogger(__name__)


class ChatService:
    def __init__(
        self,
        db: Session,
        llm_service: LLMService,
        background_tasks: BackgroundTasks | None = None,
    ) -> None:
        self.db = db
        self.llm_service = llm_service
        self.background_tasks = background_tasks

    @staticmethod
    def _save_message_background(
        tenant_id_str: str,
        conversation_id: int,
        role: str,
        content: str,
        response_time_ms: int | None = None,
    ) -> None:
        db_session = SessionLocal()
        try:
            set_tenant_context(db_session, tenant_id_str)
            msg = Message(
                tenant_id=uuid.UUID(tenant_id_str),
                conversation_id=conversation_id,
                role=role,
                content=content,
                response_time_ms=response_time_ms,
            )
            db_session.add(msg)
            db_session.commit()
        except Exception as e:
            db_session.rollback()
            logger.error("Failed to save message in background task: %s", e)
        finally:
            db_session.close()

    def _schedule_save(
        self,
        tenant_id_str: str,
        conversation_id: int,
        role: str,
        content: str,
        response_time_ms: int | None = None,
    ) -> None:
        if self.background_tasks:
            self.background_tasks.add_task(
                self._save_message_background,
                tenant_id_str,
                conversation_id,
                role,
                content,
                response_time_ms,
            )
        else:
            # Fallback to sync if no background tasks provided
            self._save_message_background(
                tenant_id_str,
                conversation_id,
                role,
                content,
                response_time_ms,
            )

    def _resolve_user_and_conversation(
        self,
        tenant_id: uuid.UUID,
        user_id: str,
        platform: str,
        session_id: str,
    ) -> tuple[int, str, int]:
        """Resolve the user and conversation info in a synchronous, thread-safe context."""
        user_svc = UserService(self.db, tenant_id)
        user = user_svc.get_or_create(
            external_id=user_id,
            platform=platform,
        )

        conv_svc = ConversationService(self.db, tenant_id)
        conv = conv_svc.get_by_session_id(session_id)
        if not conv:
            conv = conv_svc.create_for_user(user_id=user.id, session_id=session_id)

        self.db.commit()
        return conv.id, conv.state, conv.version

    async def process_message(
        self,
        tenant: Tenant,
        user_id: str,
        platform: str,
        message: str,
        session_id: str | None = None,
        rag_context: str | None = None,
    ) -> tuple[str, str, int, str]:
        try:
            if message.strip().lower() in ["/start", "/chat"]:
                session_id = str(uuid.uuid4())
            else:
                session_id = session_id or str(uuid.uuid4())

            conv_id, state, version = await asyncio.to_thread(
                self._resolve_user_and_conversation,
                tenant.id,
                user_id,
                platform,
                session_id,
            )

            self._schedule_save(str(tenant.id), conv_id, "user", message)

            # Anti-Ghost Clicks: Callback Versioning Pattern
            if message.startswith("v"):
                import re

                match = re.match(r"^v(\d+):(.*)$", message)
                if match:
                    payload_version = int(match.group(1))
                    message_action = match.group(2)
                    if payload_version != version:
                        logger.warning(
                            "Ghost click descartado: versión %s (actual es %s)",
                            payload_version,
                            version,
                        )
                        return (
                            session_id,
                            "Ese botón ya expiró. Por favor usa las opciones más recientes.",
                            version,
                            state,
                        )
                    message = message_action  # Usamos la acción limpia para el LLM

            # Hybrid FSM Pattern Logic
            if state == "ESPERANDO_HUMANO":
                response_text = "Estamos esperando a que un humano te atienda, por favor espera un momento."
                return session_id, response_text, version, state

            if state == "HUMANO_ATENDIENDO":
                response_text = "Un agente humano te está atendiendo en este momento."
                return session_id, response_text, version, state

            if state == "POSPUESTA":
                response_text = "Tu solicitud de atención humana ha sido pospuesta. Te atenderemos lo antes posible."
                return session_id, response_text, version, state

            if state == "CHECKOUT_BLOQUEADO":
                response_text = "Estamos procesando tu pago. Si deseas cancelar o volver atrás, presiona el botón correspondiente."
                return session_id, response_text, version, state

            start_time = time.time()

            response_text = await self.llm_service.run_chat(
                tenant=tenant,
                user_id=user_id,
                session_id=session_id,
                message=message,
                rag_context=rag_context,
            )

            latency_ms = int((time.time() - start_time) * 1000)

            self._schedule_save(
                str(tenant.id),
                conv_id,
                "assistant",
                response_text,
                response_time_ms=latency_ms,
            )

            return session_id, response_text, version, state
        except Exception as e:
            logger.error(
                "ChatService.process_message failed [tenant=%s, user=%s, session=%s]: %s",
                tenant.slug,
                user_id,
                session_id,
                e,
            )
            raise

    async def process_message_stream(
        self,
        tenant: Tenant,
        user_id: str,
        platform: str,
        message: str,
        session_id: str | None = None,
        rag_context: str | None = None,
    ) -> tuple[str, AsyncGenerator[str, None], int, str]:
        try:
            if message.strip().lower() in ["/start", "/chat"]:
                session_id = str(uuid.uuid4())
            else:
                session_id = session_id or str(uuid.uuid4())

            conv_id, state, version = await asyncio.to_thread(
                self._resolve_user_and_conversation,
                tenant.id,
                user_id,
                platform,
                session_id,
            )

            self._schedule_save(str(tenant.id), conv_id, "user", message)

            # Anti-Ghost Clicks: Callback Versioning Pattern
            if message.startswith("v"):
                import re

                match = re.match(r"^v(\d+):(.*)$", message)
                if match:
                    payload_version = int(match.group(1))
                    message_action = match.group(2)
                    if payload_version != version:
                        logger.warning(
                            "Ghost click descartado en stream: versión %s (actual es %s)",
                            payload_version,
                            version,
                        )

                        async def error_stream():
                            yield "Ese botón ya expiró. Por favor usa las opciones más recientes."

                        return session_id, error_stream(), version, state
                    message = message_action

            # Hybrid FSM Pattern Logic
            if state == "ESPERANDO_HUMANO":

                async def simple_stream():
                    yield "Estamos esperando a que un humano te atienda, por favor espera un momento."

                return session_id, simple_stream(), version, state

            if state == "HUMANO_ATENDIENDO":

                async def human_stream():
                    yield "Un agente humano te está atendiendo en este momento."

                return session_id, human_stream(), version, state

            if state == "POSPUESTA":

                async def postponed_stream():
                    yield "Tu solicitud de atención humana ha sido pospuesta. Te atenderemos lo antes posible."

                return session_id, postponed_stream(), version, state

            if state == "CHECKOUT_BLOQUEADO":

                async def checkout_stream():
                    yield "Estamos procesando tu pago. Si deseas cancelar o volver atrás, presiona el botón correspondiente."

                return session_id, checkout_stream(), version, state

            start_time = time.time()

            async def stream_generator() -> AsyncGenerator[str, None]:
                full_response = []
                async for chunk in self.llm_service.run_chat_stream(
                    tenant=tenant,
                    user_id=user_id,
                    session_id=session_id,
                    message=message,
                    rag_context=rag_context,
                ):
                    full_response.append(chunk)
                    yield chunk

                latency_ms = int((time.time() - start_time) * 1000)
                self._schedule_save(
                    str(tenant.id),
                    conv_id,
                    "assistant",
                    "".join(full_response),
                    response_time_ms=latency_ms,
                )

            return session_id, stream_generator(), version, state
        except Exception as e:
            logger.error(
                "ChatService.process_message_stream failed [tenant=%s, user=%s, session=%s]: %s",
                tenant.slug,
                user_id,
                session_id,
                e,
            )
            raise
