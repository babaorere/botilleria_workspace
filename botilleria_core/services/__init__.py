from __future__ import annotations

from importlib import import_module
from typing import Any

__all__ = [
    "TenantService",
    "UserService",
    "ConversationService",
    "LLMService",
    "create_llm_service",
    "AuthService",
    "AnalyticsService",
    "ChatService",
    "KBService",
    "ProductService",
    "CategoryService",
    "KBCategoryService",
    "RAGContextBuilder",
    "RedisSessionService",
    "create_session_service",
    "AgentFactory",
    "transactional",
    "RateLimiter",
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
    "AuthService": ("services.auth_service", "AuthService"),
    "AnalyticsService": ("services.analytics_service", "AnalyticsService"),
    "ChatService": ("services.chat_service", "ChatService"),
    "KBService": ("services.kb_service", "KBService"),
    "ProductService": ("services.product_service", "ProductService"),
    "CategoryService": ("services.category_service", "CategoryService"),
    "KBCategoryService": ("services.kb_category_service", "KBCategoryService"),
    "RAGContextBuilder": (
        "services.rag_context_builder",
        "RAGContextBuilder",
    ),
    "RedisSessionService": (
        "services.redis_session_service",
        "RedisSessionService",
    ),
    "create_session_service": (
        "services.session_service_factory",
        "create_session_service",
    ),
    "AgentFactory": ("services.agent_factory", "AgentFactory"),
    "transactional": ("services.transactional", "transactional"),
    "RateLimiter": ("services.rate_limiter", "RateLimiter"),
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
