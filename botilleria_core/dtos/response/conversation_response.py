from datetime import datetime
from pydantic import BaseModel

class ConversationResponse(BaseModel):
    id: int
    user_id: int
    session_id: str

    model_config = {"from_attributes": True}


class MessageResponse(BaseModel):
    id: int
    role: str
    content: str
    created_at: datetime
    response_time_ms: int | None

    model_config = {"from_attributes": True}


class ConversationQueueItemResponse(BaseModel):
    id: int
    session_id: str
    state: str
    version: int
    created_at: datetime
    user_id: int
    user_external_id: str
    user_display_name: str | None
    user_platform: str
    last_message: str | None
    last_message_time: datetime | None

    model_config = {"from_attributes": True}
