from __future__ import annotations

import logging
import os
import time
from typing import Any, AsyncGenerator

from google.adk import Agent, Runner
from google.adk.models.lite_llm import LiteLlm
from google.adk.sessions.base_session_service import BaseSessionService
from google.genai import types

from exceptions.llm_exceptions import LLMProviderError
from models.tenant import Tenant
from services.session_service_factory import create_session_service

logger = logging.getLogger(__name__)


class LLMService:
    def __init__(self, session_service: BaseSessionService | None = None) -> None:
        self._runners: dict[str, Runner] = {}
        self._runner_specs: dict[str, tuple[str, str]] = {}
        self._session_service = session_service or create_session_service()

    def _get_runner(self, tenant: Tenant) -> Runner:
        tenant_key = str(tenant.id)
        current_spec = (tenant.get_model(), tenant.get_instruction())

        if (
            tenant_key not in self._runners
            or self._runner_specs.get(tenant_key) != current_spec
        ):
            api_key = (
                tenant.get_api_key()
                or os.getenv("NVIDIA_API_KEY")
                or os.getenv("OPENROUTER_API_KEY")
            )
            if not api_key:
                raise RuntimeError(
                    f"NVIDIA_API_KEY o OPENROUTER_API_KEY not configured for tenant {tenant.slug}"
                )

            from agents.root_agent import BOTILLERIA_TOOLS

            agent = Agent(
                name=f"{tenant.slug}_{int(time.time())}",
                model=LiteLlm(model=tenant.get_model(), api_key=api_key),
                instruction=tenant.get_instruction(),
                tools=BOTILLERIA_TOOLS,
            )

            self._runners[tenant_key] = Runner(
                agent=agent,
                app_name=f"botilleria_{tenant_key}",
                session_service=self._session_service,
                auto_create_session=True,
            )
            self._runner_specs[tenant_key] = current_spec
            logger.info(
                "Runner created for tenant: %s (model=%s)",
                tenant.slug,
                tenant.get_model(),
            )

        return self._runners[tenant_key]

    async def run_chat(
        self,
        tenant: Tenant,
        user_id: str,
        session_id: str,
        message: str,
        rag_context: str | None = None,
    ) -> str:
        from config.context import tenant_id_var, user_id_var, session_id_var

        t_token = tenant_id_var.set(tenant.id)
        u_token = user_id_var.set(user_id)
        s_token = session_id_var.set(session_id)
        try:
            runner = self._get_runner(tenant)
            full_response: list[str] = []
            content = types.Content(
                role="user",
                parts=[
                    types.Part(text=self._build_input_message(message, rag_context))
                ],
            )

            async for event in runner.run_async(
                user_id=user_id,
                session_id=session_id,
                new_message=content,
            ):
                if event.content and event.content.parts:
                    for part in event.content.parts:
                        if part.text and not getattr(part, "thought", False):
                            full_response.append(part.text)

            return (
                "".join(full_response)
                if full_response
                else "No pude generar una respuesta."
            )
        except Exception as e:
            logger.error(
                "LLMService.run_chat failed [tenant=%s, user=%s, session=%s]: %s",
                tenant.slug,
                user_id,
                session_id,
                e,
            )
            raise LLMProviderError(f"Error al generar respuesta: {e}") from e
        finally:
            tenant_id_var.reset(t_token)
            user_id_var.reset(u_token)
            session_id_var.reset(s_token)

    async def run_chat_stream(
        self,
        tenant: Tenant,
        user_id: str,
        session_id: str,
        message: str,
        rag_context: str | None = None,
    ) -> AsyncGenerator[str, None]:
        from config.context import tenant_id_var, user_id_var, session_id_var

        t_token = tenant_id_var.set(tenant.id)
        u_token = user_id_var.set(user_id)
        s_token = session_id_var.set(session_id)
        try:
            runner = self._get_runner(tenant)
            content = types.Content(
                role="user",
                parts=[
                    types.Part(text=self._build_input_message(message, rag_context))
                ],
            )

            async for event in runner.run_async(
                user_id=user_id,
                session_id=session_id,
                new_message=content,
            ):
                if event.content and event.content.parts:
                    for part in event.content.parts:
                        if part.text and not getattr(part, "thought", False):
                            yield part.text
        except Exception as e:
            logger.error(
                "LLMService.run_chat_stream failed [tenant=%s, user=%s, session=%s]: %s",
                tenant.slug,
                user_id,
                session_id,
                e,
            )
            raise LLMProviderError(f"Error al generar stream de respuesta: {e}") from e
        finally:
            tenant_id_var.reset(t_token)
            user_id_var.reset(u_token)
            session_id_var.reset(s_token)

    async def get_session_history(
        self,
        tenant: Tenant,
        user_id: str,
        session_id: str,
    ) -> list[dict[str, Any]]:
        try:
            runner = self._get_runner(tenant)
            session = await self._session_service.get_session(
                app_name=runner.app_name,
                user_id=user_id,
                session_id=session_id,
            )
            if not session:
                return []

            history: list[dict[str, Any]] = []
            for event in session.events:
                if event.content and event.content.parts:
                    texts = [p.text for p in event.content.parts if p.text]
                    if texts:
                        history.append(
                            {"author": event.author, "content": "".join(texts)}
                        )
            return history
        except Exception as e:
            logger.error(
                "LLMService.get_session_history failed [tenant=%s, user=%s, session=%s]: %s",
                tenant.slug,
                user_id,
                session_id,
                e,
            )
            raise

    def _build_input_message(self, message: str, rag_context: str | None) -> str:
        if not rag_context:
            return message
        return (
            "CONTEXTO DE CONOCIMIENTO DEL NEGOCIO PARA ESTA CONSULTA:\n"
            f"{rag_context}\n\n"
            "Usa el contexto anterior solo si es relevante para responder. "
            "Si no alcanza, responde con honestidad y ofrece contactar a un humano.\n\n"
            f"MENSAJE DEL USUARIO:\n{message}"
        )


def create_llm_service(
    session_service: BaseSessionService | None = None,
) -> LLMService:
    return LLMService(session_service=session_service)
