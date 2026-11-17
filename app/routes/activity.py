import json
from datetime import datetime, timezone
from typing import Optional

from bson import ObjectId
from fastapi import APIRouter, Depends, Query, status

from app.database import activity_collection
from app.middleware.auth_middleware import get_current_user
from app.models.activity import ActivityCreate
from app.redis import redis_client

router = APIRouter(prefix="/activity", tags=["Activity"])

# Redis keys
USER_ACTIVITY_KEY = lambda user_id: f"user_activity:{user_id}"
ACTIVITY_TTL = 60 * 5  # 5 minutes


def _serialize(doc: dict) -> dict:
    doc["id"] = str(doc.pop("_id"))
    if isinstance(doc.get("created_at"), datetime):
        doc["created_at"] = doc["created_at"].isoformat()
    return doc


# ──────────────────────────────────────────────
# POST /activity/  →  Action log karo (internal)
# ──────────────────────────────────────────────
@router.post("/", status_code=status.HTTP_201_CREATED)
async def log_activity(
    payload: ActivityCreate,
    user: dict = Depends(get_current_user),
):
    doc = {
        "owner_user_id": str(user["_id"]),
        "action":        payload.action,
        "entity_type":   payload.entity_type,
        "entity_id":     payload.entity_id,
        "description":   payload.description,
        "metadata":      payload.metadata or {},
        "created_at":    datetime.now(timezone.utc),
    }

    result = await activity_collection.insert_one(doc)
    doc["_id"] = result.inserted_id
    serialized = _serialize(doc)

    # List cache invalidate
    await redis_client.delete(USER_ACTIVITY_KEY(str(user["_id"])))

    return {"success": True, "data": serialized}


# ──────────────────────────────────────────────
# GET /activity/  →  Activity feed
# ──────────────────────────────────────────────
@router.get("/")
async def list_activity(
    entity_type: Optional[str] = Query(None, description="Filter: thread, draft, account"),
    entity_id:   Optional[str] = Query(None, description="Specific entity ke logs"),
    skip:  int = Query(0,  ge=0),
    limit: int = Query(20, ge=1, le=100),
    user: dict = Depends(get_current_user),
):
    user_id   = str(user["_id"])
    use_cache = (entity_type is None and entity_id is None and skip == 0 and limit == 20)

    # Cache check
    if use_cache:
        cached = await redis_client.get(USER_ACTIVITY_KEY(user_id))
        if cached:
            return {"success": True, "data": json.loads(cached), "source": "cache"}

    query: dict = {"owner_user_id": user_id}
    if entity_type:
        query["entity_type"] = entity_type
    if entity_id:
        query["entity_id"] = entity_id

    cursor = (
        activity_collection.find(query)
        .sort("created_at", -1)
        .skip(skip)
        .limit(limit)
    )
    logs  = [_serialize(doc) async for doc in cursor]
    total = await activity_collection.count_documents(query)

    result = {"logs": logs, "total": total, "skip": skip, "limit": limit}

    # Cache store (sirf unfiltered first page)
    if use_cache:
        await redis_client.setex(USER_ACTIVITY_KEY(user_id), ACTIVITY_TTL, json.dumps(result))

    return {"success": True, "data": result}