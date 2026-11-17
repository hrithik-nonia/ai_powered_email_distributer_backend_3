from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class MessageResponse(BaseModel):
    message_id: str
    from_name: str
    from_email: str
    to: list[str]
    body: str
    timestamp: datetime
    is_read: bool


class ThreadResponse(BaseModel):
    id: str
    account_id: str
    owner_user_id: str
    subject: str
    participants: list[dict]
    messages: list[MessageResponse]
    ai_label: str
    ai_confidence: float
    ai_reason: str
    ai_summary: str
    ai_extracted_dates: list[str]
    manual_override: bool
    segment: list[str]
    is_important: bool
    is_read: bool
    is_archived: bool
    status: str
    last_message_at: datetime
    created_at: datetime


class ThreadListResponse(BaseModel):
    threads: list[ThreadResponse]
    total: int
    skip: int
    limit: int


class StatsResponse(BaseModel):
    total: int
    unread: int
    assistant_reply: int
    client_reply: int
    needs_review: int
    no_reply: int
    action_required: int
    waiting: int
    meetings: int
    important: int
