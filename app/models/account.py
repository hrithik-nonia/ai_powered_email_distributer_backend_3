from pydantic import BaseModel
from datetime import datetime


class AccountResponse(BaseModel):
    id: str
    user_id: str
    provider: str
    email_address: str
    status: str
    last_synced_at: datetime
    created_at: datetime

    class Config:
        populate_by_name = True