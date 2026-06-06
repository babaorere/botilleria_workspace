from __future__ import annotations

import contextvars
import uuid

tenant_id_var: contextvars.ContextVar[uuid.UUID] = contextvars.ContextVar("tenant_id")
user_id_var: contextvars.ContextVar[str] = contextvars.ContextVar("user_id")
session_id_var: contextvars.ContextVar[str] = contextvars.ContextVar("session_id")
