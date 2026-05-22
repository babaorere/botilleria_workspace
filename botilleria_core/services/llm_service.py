from __future__ import annotations

import logging
import os
import time
from typing import Any, AsyncGenerator

from google.adk import Agent, Runner
from google.adk.models.lite_llm import LiteLlm
from google.adk.sessions import InMemorySessionService
from google.genai import types

from models.tenant import Tenant

logger = logging.getLogger(__name__)


class LLMService:
    def __init__(self) -> None:
        self._runners: dict[str, Runner] = {}
        self._session_service = InMemorySessionService()

    def _get_runner(self, tenant: Tenant, rag_context: str | None = None) -> Runner:
        tenant_key = str(tenant.id)
        instruction = tenant.get_instruction()
        if rag_context:
            instruction = (
                f"{instruction}\n\n"
                f"{rag_context}\n\n"
                f"Usa la información anterior para responder con precisión. "
                f"Si la información no es suficiente, responde honestamente "
                f"y ofrece contactar a un humano."
            )

        if tenant_key not in self._runners:
            api_key = tenant.get_api_key() or os.getenv("OPENROUTER_API_KEY")
            if not api_key:
                raise RuntimeError(
                    f"OPENROUTER_API_KEY not configured for tenant {tenant.slug}"
                )

            agent = Agent(
                name=f"{tenant.slug}_{int(time.time())}",
                model=LiteLlm(model=tenant.get_model(), api_key=api_key),
                instruction=instruction,
                tools=[],
            )

            self._runners[tenant_key] = Runner(
                agent=agent,
                app_name=f"botilleria_{tenant_key}",
                session_service=self._session_service,
                auto_create_session=True,
            )
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
        try:
            runner = self._get_runner(tenant, rag_context)
            full_response: list[str] = []
            content = types.Content(role="user", parts=[types.Part(text=message)])

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
            raise

    async def run_chat_stream(
        self,
        tenant: Tenant,
        user_id: str,
        session_id: str,
        message: str,
        rag_context: str | None = None,
    ) -> AsyncGenerator[str, None]:
        try:
            runner = self._get_runner(tenant, rag_context)
            content = types.Content(role="user", parts=[types.Part(text=message)])

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
            raise

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


def create_llm_service() -> LLMService:
    return LLMService()
