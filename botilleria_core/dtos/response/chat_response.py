from __future__ import annotations

from pydantic import BaseModel
from typing import List, Optional

class InteractiveButton(BaseModel):
    text: str
    payload: str

class ChatResponse(BaseModel):
    session_id: str
    user_id: str
    tenant_slug: str
    response: str
    buttons: Optional[List[InteractiveButton]] = None

class SessionHistoryItem(BaseModel):
    author: str
    content: str
