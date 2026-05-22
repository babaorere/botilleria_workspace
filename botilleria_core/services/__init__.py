from __future__ import annotations

from importlib import import_module
from typing import Any

__all__ = [
    "TenantService",
    "UserService",
    "ConversationService",
    "LLMService",
    "create_llm_service",
    "ChatService",
    "KBService",
    "ProductService",
    "RAGContextBuilder",
    "AgentFactory",
    "transactional",
]

_LAZY_IMPORTS: dict[str, tuple[str, str]] = {
    "TenantService": ("services.tenant_service", "TenantService"),
    "UserService": ("services.user_service", "UserService"),
    "ConversationService": (
        "services.conversation_service",
        "ConversationService",
    ),
    "LLMService": ("services.llm_service", "LLMService"),
    "create_llm_service": ("services.llm_service", "create_llm_service"),
    "ChatService": ("services.chat_service", "ChatService"),
    "KBService": ("services.kb_service", "KBService"),
    "ProductService": ("services.product_service", "ProductService"),
    "RAGContextBuilder": (
        "services.rag_context_builder",
        "RAGContextBuilder",
    ),
    "AgentFactory": ("services.agent_factory", "AgentFactory"),
    "transactional": ("services.transactional", "transactional"),
}


def __getattr__(name: str) -> Any:
    try:
        module_name, attr_name = _LAZY_IMPORTS[name]
    except KeyError as exc:
        raise AttributeError(f"module 'services' has no attribute {name!r}") from exc

    module = import_module(module_name)
    value = getattr(module, attr_name)
    globals()[name] = value
    return value
