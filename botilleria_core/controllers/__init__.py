from .health_controller import router as health_router
from .chat_controller import router as chat_router
from .tenant_controller import router as tenant_router
from .user_controller import router as user_router
from .session_controller import router as session_router
from .tenant_config_controller import router as tenant_config_router
from .tenant_products_controller import router as tenant_products_router
from .tenant_kb_controller import router as tenant_kb_router
from .auth_controller import router as auth_router
from .admin_controller import router as admin_router

__all__ = [
    "health_router",
    "chat_router",
    "tenant_router",
    "user_router",
    "session_router",
    "tenant_config_router",
    "tenant_products_router",
    "tenant_kb_router",
    "admin_router",
    "auth_router",
]
