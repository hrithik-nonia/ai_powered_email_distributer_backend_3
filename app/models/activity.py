from typing import Any, Optional
from pydantic import BaseModel

class ActivityCreate(BaseModel):
    action: str                        # "label_changed", "draft_generated", etc.
    entity_type: str                   # "thread", "draft", "account"
    entity_id: str                     # us entity ka ID
    description: str                   # human-readable: "Thread labeled as PA"
    metadata: Optional[dict[str, Any]] = {}