from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class DraftCreate(BaseModel):
    thread_id: Optional[str] = None
    account_id: str
    to: List[str]
    cc: Optional[List[str]] = []
    bcc: Optional[List[str]] = []
    subject: str
    body: str
    is_html: bool = False


class DraftUpdate(BaseModel):
    to: Optional[List[str]] = None
    cc: Optional[List[str]] = None
    bcc: Optional[List[str]] = None
    subject: Optional[str] = None
    body: Optional[str] = None
    is_html: Optional[bool] = None


class DraftResponse(BaseModel):
    id: str
    owner_user_id: str
    thread_id: Optional[str] = None
    account_id: str
    to: List[str]
    cc: List[str]
    bcc: List[str]
    subject: str
    body: str
    is_html: bool
    created_at: datetime
    updated_at: datetime