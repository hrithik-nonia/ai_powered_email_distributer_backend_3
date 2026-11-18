import json
from datetime import datetime, timezone
from typing import Optional

from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.database import drafts_collection
from app.middleware.auth_middleware import get_current_user
from app.models.draft import DraftCreate, DraftUpdate
from app.redis import redis_client

router = APIRouter(prefix="/drafts", tags=["Drafts"])

# Redis key helpers
DRAFT_KEY     = lambda draft_id: f"draft:{draft_id}"
USER_DRAFTS_KEY = lambda user_id: f"user_drafts:{user_id}"
DRAFT_TTL = 60 * 10  # 10 minutes


def _serialize(doc: dict) -> dict:
    """MongoDB doc → JSON-safe dict."""
    doc["id"] = str(doc.pop("_id"))
    if isinstance(doc.get("created_at"), datetime):
        doc["created_at"] = doc["created_at"].isoformat()
    if isinstance(doc.get("updated_at"), datetime):
        doc["updated_at"] = doc["updated_at"].isoformat()
    return doc


# ──────────────────────────────────────────────────────────────
# POST /drafts/  →  नया draft save करो
# ──────────────────────────────────────────────────────────────
@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_draft(
    payload: DraftCreate,
    user: dict = Depends(get_current_user),
):
    now = datetime.now(timezone.utc)
    doc = {
        "owner_user_id": str(user["_id"]),
        "thread_id":     payload.thread_id,
        "account_id":    payload.account_id,
        "to":            payload.to,
        "cc":            payload.cc or [],
        "bcc":           payload.bcc or [],
        "subject":       payload.subject,
        "body":          payload.body,
        "is_html":       payload.is_html,
        "created_at":    now,
        "updated_at":    now,
    }

    result = await drafts_collection.insert_one(doc)
    doc["_id"] = result.inserted_id
    serialized = _serialize(doc)

    # Redis: draft cache + list invalidate
    await redis_client.setex(DRAFT_KEY(serialized["id"]), DRAFT_TTL, json.dumps(serialized))
    await redis_client.delete(USER_DRAFTS_KEY(str(user["_id"])))

    return {"success": True, "data": serialized}


# ──────────────────────────────────────────────────────────────
# GET /drafts/  →  सभी drafts list करो
# ──────────────────────────────────────────────────────────────
@router.get("/")
async def list_drafts(
    thread_id: Optional[str] = Query(None, description="Specific thread ke drafts"),
    skip: int  = Query(0,  ge=0),
    limit: int = Query(20, ge=1, le=100),
    user: dict = Depends(get_current_user),
):
    user_id    = str(user["_id"])
    use_cache  = (thread_id is None and skip == 0 and limit == 20)
    redis      = await redis_client

    # Cache hit (sirf unfiltered first page ke liye)
    if use_cache and redis:
        cached = await redis.get(USER_DRAFTS_KEY(user_id))
        if cached:
            return {"success": True, "data": json.loads(cached), "source": "cache"}

    query: dict = {"owner_user_id": user_id}
    if thread_id:
        query["thread_id"] = thread_id

    cursor = (
        drafts_collection.find(query)
        .sort("updated_at", -1)
        .skip(skip)
        .limit(limit)
    )
    drafts = [_serialize(doc) async for doc in cursor]
    total  = await drafts_collection.count_documents(query)

    result = {"drafts": drafts, "total": total, "skip": skip, "limit": limit}

    # Cache store
    await redis_client.setex(USER_DRAFTS_KEY(user_id), DRAFT_TTL, json.dumps(result))

    return {"success": True, "data": result}


# ──────────────────────────────────────────────────────────────
# GET /drafts/{draft_id}  →  Single draft
# ──────────────────────────────────────────────────────────────
@router.get("/{draft_id}")
async def get_draft(
    draft_id: str,
    user: dict = Depends(get_current_user),
):
    redis = await redis_client

    # Redis पहले check करो
    if redis:
        cached = await redis.get(DRAFT_KEY(draft_id))
        if cached:
            data = json.loads(cached)
            if data.get("owner_user_id") != str(user["_id"]):
                raise HTTPException(status_code=403, detail="Access denied")
            return {"success": True, "data": data, "source": "cache"}

    # MongoDB fallback
    try:
        oid = ObjectId(draft_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid draft ID")

    doc = await drafts_collection.find_one({"_id": oid})
    if not doc:
        raise HTTPException(status_code=404, detail="Draft not found")
    if doc["owner_user_id"] != str(user["_id"]):
        raise HTTPException(status_code=403, detail="Access denied")

    serialized = _serialize(doc)

    await redis_client.setex(DRAFT_KEY(draft_id), DRAFT_TTL, json.dumps(serialized))

    return {"success": True, "data": serialized}


# ──────────────────────────────────────────────────────────────
# PATCH /drafts/{draft_id}  →  Draft update करो
# ──────────────────────────────────────────────────────────────
@router.patch("/{draft_id}")
async def update_draft(
    draft_id: str,
    payload: DraftUpdate,
    user: dict = Depends(get_current_user),
):
    try:
        oid = ObjectId(draft_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid draft ID")

    doc = await drafts_collection.find_one({"_id": oid})
    if not doc:
        raise HTTPException(status_code=404, detail="Draft not found")
    if doc["owner_user_id"] != str(user["_id"]):
        raise HTTPException(status_code=403, detail="Access denied")

    updates = payload.model_dump(exclude_none=True)
    if not updates:
        raise HTTPException(status_code=400, detail="Kuch bhi update karne ke liye bhejo")

    updates["updated_at"] = datetime.now(timezone.utc)
    await drafts_collection.update_one({"_id": oid}, {"$set": updates})

    updated    = await drafts_collection.find_one({"_id": oid})
    serialized = _serialize(updated)

    # Redis refresh
    
    await redis_client.setex(DRAFT_KEY(draft_id), DRAFT_TTL, json.dumps(serialized))
    await redis_client.delete(USER_DRAFTS_KEY(str(user["_id"])))

    return {"success": True, "data": serialized}


# ──────────────────────────────────────────────────────────────
# DELETE /drafts/{draft_id}  →  Draft delete करो
# ──────────────────────────────────────────────────────────────
@router.delete("/{draft_id}")
async def delete_draft(
    draft_id: str,
    user: dict = Depends(get_current_user),
):
    try:
        oid = ObjectId(draft_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid draft ID")

    doc = await drafts_collection.find_one({"_id": oid})
    if not doc:
        raise HTTPException(status_code=404, detail="Draft not found")
    if doc["owner_user_id"] != str(user["_id"]):
        raise HTTPException(status_code=403, detail="Access denied")

    await drafts_collection.delete_one({"_id": oid})

    # Redis cleanup
    await redis_client.delete(DRAFT_KEY(draft_id))
    await redis_client.delete(USER_DRAFTS_KEY(str(user["_id"])))

    return {"success": True, "message": "Draft deleted successfully"}