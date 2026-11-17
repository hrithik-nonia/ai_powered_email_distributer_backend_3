from fastapi import APIRouter, Depends, HTTPException, Query, status
from typing import Optional, Literal
from datetime import datetime, timezone
from bson import ObjectId
import json
import asyncio

from app.middleware.auth_middleware import get_current_user
from app.database import threads_collection, activity_collection, users_collection
from app.redis import redis_client
from app.models.thread import (
    ThreadResponse,
    ThreadListResponse,
    StatsResponse,
    MessageResponse,
    LabelUpdate,
    ReadUpdate,
    StatusUpdate,
    ClientAction,
)

router = APIRouter(prefix="/threads", tags=["threads"])


# ── TTL / Interval Constants ──────────────────────────────────────────────────

THREAD_TTL         = 300   # 5 min  — individual thread cache
LIST_CACHE_TTL     = 120   # 2 min  — list query results
STATS_TTL          = 60    # 1 min  — stats
USER_TTL           = 600   # 10 min — user/assistant lookup
WRITE_BEHIND_FLUSH = 30    # 30 sec — flush dirty data to MongoDB

DIRTY_SET_KEY = "dirty:thread_ids"  # Redis SET: tracks all thread IDs with pending writes


# ── Redis Key Helpers ─────────────────────────────────────────────────────────

def _thread_key(thread_id) -> str:
    return f"thread:{thread_id}"

def _list_key(user_id, label, segment, search, is_important, is_archived, skip, limit) -> str:
    parts = "|".join(map(str, [user_id, label, segment, search, is_important, is_archived, skip, limit]))
    return f"threads:list:{parts}"

def _stats_key(user_id) -> str:
    return f"threads:stats:{user_id}"

def _client_assistant_key(client_id) -> str:
    return f"client:linked_assistant:{client_id}"

def _dirty_key(thread_id) -> str:
    return f"thread:dirty:{thread_id}"


# ── Helpers ───────────────────────────────────────────────────────────────────

def _serialize_thread(doc: dict) -> ThreadResponse:
    messages = [
        MessageResponse(
            message_id=m["message_id"],
            from_name=m["from_name"],
            from_email=m["from_email"],
            to=m.get("to", []),
            body=m["body"],
            timestamp=m["timestamp"],
            is_read=m.get("is_read", False),
        )
        for m in doc.get("messages", [])
    ]
    return ThreadResponse(
        id=str(doc["_id"]),
        account_id=str(doc["account_id"]),
        owner_user_id=str(doc["owner_user_id"]),
        subject=doc["subject"],
        participants=doc.get("participants", []),
        messages=messages,
        ai_label=doc["ai_label"],
        ai_confidence=doc.get("ai_confidence", 0.0),
        ai_reason=doc.get("ai_reason", ""),
        ai_summary=doc.get("ai_summary", ""),
        ai_extracted_dates=doc.get("ai_extracted_dates", []),
        manual_override=doc.get("manual_override", False),
        segment=doc.get("segment", []),
        is_important=doc.get("is_important", False),
        is_read=doc.get("is_read", False),
        is_archived=doc.get("is_archived", False),
        status=doc.get("status", "open"),
        last_message_at=doc["last_message_at"],
        created_at=doc["created_at"],
    )


async def _base_query(current_user: dict) -> dict:
    role = current_user.get("role")

    if role == "assistant":
        return {"owner_user_id": current_user["_id"]}

    elif role == "client":
        linked_id = current_user.get("linked_assistant_id")
        if not linked_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No linked assistant found for this client.",
            )

        # Redis cache: skip MongoDB lookup on repeat requests
        cache_key = _client_assistant_key(str(current_user["_id"]))
        cached = await redis_client.get(cache_key)

        if cached:
            assistant_oid = ObjectId(cached.decode() if isinstance(cached, bytes) else cached)
        else:
            try:
                assistant_oid = ObjectId(str(linked_id))
            except Exception:
                raise HTTPException(status_code=400, detail="Invalid linked_assistant_id.")

            assistant = await users_collection.find_one({"_id": assistant_oid})
            if not assistant:
                raise HTTPException(status_code=404, detail="Linked assistant not found.")

            # Cache only the assistant's ID — no PII, lightweight
            await redis_client.setex(cache_key, USER_TTL, str(assistant_oid))

        return {
            "owner_user_id": assistant_oid,
            "ai_label": "client_reply",
        }

    raise HTTPException(status_code=403, detail="Unknown role.")


def _apply_filters(query: dict, label, segment, search, is_important, is_archived) -> dict:
    if label:
        query["ai_label"] = label
    if segment:
        query["segment"] = {"$in": [segment]}
    if search:
        query["subject"] = {"$regex": search, "$options": "i"}
    if is_important is not None:
        query["is_important"] = is_important
    if is_archived is not None:
        query["is_archived"] = is_archived
    return query


# ── Cache Helpers ─────────────────────────────────────────────────────────────

async def _get_thread_cache(thread_id: str) -> Optional[ThreadResponse]:
    raw = await redis_client.get(_thread_key(thread_id))
    if raw:
        return ThreadResponse.model_validate_json(raw if isinstance(raw, str) else raw.decode())
    return None


async def _set_thread_cache(thread: ThreadResponse):
    await redis_client.setex(_thread_key(thread.id), THREAD_TTL, thread.model_dump_json())


async def _invalidate_user_list_stats(user_id: str):
    """Bust stats + all list caches belonging to this user."""
    await redis_client.delete(_stats_key(user_id))
    async for key in redis_client.scan_iter(match=f"threads:list:{user_id}|*"):
        await redis_client.delete(key)


# ── Write-Behind ──────────────────────────────────────────────────────────────

async def _write_behind(thread_id: str, fields: dict):
    """
    Two things happen here:
    1. If the thread is already in Redis cache, update it in-place (fast read on next GET).
    2. Store the pending field changes in a Redis HASH under dirty:<thread_id>.
       The flush worker picks these up every WRITE_BEHIND_FLUSH seconds and syncs to MongoDB.

    Flow:
        PATCH /read (500x in 30s) → Redis only → after 30s → 1 MongoDB write
    """
    tid = str(thread_id)

    cached = await _get_thread_cache(tid)
    if cached:
        await _set_thread_cache(cached.model_copy(update=fields))

    # Accumulate dirty fields (later writes overwrite earlier ones — correct behavior)
    encoded = {k: json.dumps(v, default=str) for k, v in fields.items()}
    await redis_client.hset(_dirty_key(tid), mapping=encoded)
    await redis_client.sadd(DIRTY_SET_KEY, tid)


async def _flush_dirty_thread(thread_id: str):
    dirty_key = _dirty_key(thread_id)
    raw = await redis_client.hgetall(dirty_key)
    if not raw:
        await redis_client.srem(DIRTY_SET_KEY, thread_id)
        return

    updates = {
        (k.decode() if isinstance(k, bytes) else k): json.loads(v.decode() if isinstance(v, bytes) else v)
        for k, v in raw.items()
    }

    # Clear dirty data atomically before the MongoDB write.
    # Any new writes that arrive during the write go into a fresh dirty hash — safe.
    pipe = redis_client.pipeline()
    pipe.delete(dirty_key)
    pipe.srem(DIRTY_SET_KEY, thread_id)
    await pipe.execute()

    await threads_collection.update_one(
        {"_id": ObjectId(thread_id)},
        {"$set": updates},
    )


async def flush_all_dirty():
    """Drain the dirty set. Called by the background worker."""
    thread_ids = await redis_client.smembers(DIRTY_SET_KEY)
    for tid_raw in thread_ids:
        tid = tid_raw.decode() if isinstance(tid_raw, bytes) else tid_raw
        try:
            await _flush_dirty_thread(tid)
        except Exception as e:
            print(f"[write-behind] flush failed for thread {tid}: {e}")


async def start_write_behind_worker():
    """
    Long-running coroutine — register once at app startup in main.py:

        @app.on_event("startup")
        async def startup():
            asyncio.create_task(start_write_behind_worker())
    """
    while True:
        await asyncio.sleep(WRITE_BEHIND_FLUSH)
        await flush_all_dirty()


# ── GET /threads/ ─────────────────────────────────────────────────────────────

@router.get("/", response_model=ThreadListResponse)
async def list_threads(
    label: Optional[Literal["assistant_reply", "client_reply", "no_reply", "needs_review"]] = None,
    segment: Optional[Literal["action_required", "waiting", "meetings", "important", "general"]] = None,
    search: Optional[str] = None,
    is_important: Optional[bool] = None,
    is_archived: Optional[bool] = None,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=20, ge=1, le=100),
    current_user: dict = Depends(get_current_user),
):
    user_id = str(current_user["_id"])
    cache_key = _list_key(user_id, label, segment, search, is_important, is_archived, skip, limit)

    raw = await redis_client.get(cache_key)
    if raw:
        return ThreadListResponse.model_validate_json(raw if isinstance(raw, str) else raw.decode())

    query = await _base_query(current_user)
    query = _apply_filters(query, label, segment, search, is_important, is_archived)

    total = await threads_collection.count_documents(query)
    cursor = threads_collection.find(query).sort("last_message_at", -1).skip(skip).limit(limit)
    docs = await cursor.to_list(length=limit)

    result = ThreadListResponse(
        threads=[_serialize_thread(d) for d in docs],
        total=total,
        skip=skip,
        limit=limit,
    )
    await redis_client.setex(cache_key, LIST_CACHE_TTL, result.model_dump_json())
    return result


# ── GET /threads/stats ────────────────────────────────────────────────────────

@router.get("/stats", response_model=StatsResponse)
async def get_stats(current_user: dict = Depends(get_current_user)):
    user_id = str(current_user["_id"])
    cache_key = _stats_key(user_id)

    raw = await redis_client.get(cache_key)
    if raw:
        return StatsResponse.model_validate_json(raw if isinstance(raw, str) else raw.decode())

    base = await _base_query(current_user)

    async def count(extra: dict) -> int:
        return await threads_collection.count_documents({**base, **extra})

    result = StatsResponse(
        total           = await count({}),
        unread          = await count({"is_read": False}),
        assistant_reply = await count({"ai_label": "assistant_reply"}),
        client_reply    = await count({"ai_label": "client_reply"}),
        needs_review    = await count({"ai_label": "needs_review"}),
        no_reply        = await count({"ai_label": "no_reply"}),
        action_required = await count({"segment": {"$in": ["action_required"]}}),
        waiting         = await count({"segment": {"$in": ["waiting"]}}),
        meetings        = await count({"segment": {"$in": ["meetings"]}}),
        important       = await count({"is_important": True}),
    )
    await redis_client.setex(cache_key, STATS_TTL, result.model_dump_json())
    return result


# ── GET /threads/{thread_id} ──────────────────────────────────────────────────

@router.get("/{thread_id}", response_model=ThreadResponse)
async def get_thread(
    thread_id: str,
    current_user: dict = Depends(get_current_user),
):
    try:
        oid = ObjectId(thread_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid thread ID.")

    # Redis hit
    cached = await _get_thread_cache(thread_id)
    if cached:
        if not cached.is_read:
            await _write_behind(thread_id, {"is_read": True})
            cached = cached.model_copy(update={"is_read": True})
        return cached

    # MongoDB fallback
    base = await _base_query(current_user)
    base["_id"] = oid
    thread = await threads_collection.find_one(base)
    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found.")

    if not thread.get("is_read"):
        await _write_behind(thread_id, {"is_read": True})
        thread["is_read"] = True

    result = _serialize_thread(thread)
    await _set_thread_cache(result)
    return result


# ── PATCH /threads/{thread_id}/label ─────────────────────────────────────────

@router.patch("/{thread_id}/label", response_model=ThreadResponse)
async def update_label(
    thread_id: str,
    body: LabelUpdate,
    current_user: dict = Depends(get_current_user),
):
    try:
        oid = ObjectId(thread_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid thread ID.")

    thread = await threads_collection.find_one({"_id": oid})
    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found.")

    old_label = thread.get("ai_label")

    updated = await threads_collection.find_one_and_update(
        {"_id": oid},
        {"$set": {"ai_label": body.label, "manual_override": True}},
        return_document=True,
    )

    result = _serialize_thread(updated)
    await _set_thread_cache(result)
    await _invalidate_user_list_stats(str(current_user["_id"]))

    await activity_collection.insert_one({
        "thread_id": oid,
        "action_by": current_user["_id"],
        "role": current_user.get("role"),
        "action": "label_changed",
        "old_value": old_label,
        "new_value": body.label,
        "timestamp": datetime.now(timezone.utc),
    })

    return result


# ── PATCH /threads/{thread_id}/important ─────────────────────────────────────

@router.patch("/{thread_id}/important", response_model=ThreadResponse)
async def toggle_important(
    thread_id: str,
    current_user: dict = Depends(get_current_user),
):
    try:
        oid = ObjectId(thread_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid thread ID.")

    thread = await threads_collection.find_one({"_id": oid})
    if not thread:
        raise HTTPException(status_code=404, detail="Thread not found.")

    new_val = not thread.get("is_important", False)
    updated = await threads_collection.find_one_and_update(
        {"_id": oid},
        {"$set": {"is_important": new_val}},
        return_document=True,
    )

    result = _serialize_thread(updated)
    await _set_thread_cache(result)
    await _invalidate_user_list_stats(str(current_user["_id"]))
    return result


# ── PATCH /threads/{thread_id}/read  (write-behind) ──────────────────────────

@router.patch("/{thread_id}/read", response_model=ThreadResponse)
async def update_read(
    thread_id: str,
    body: ReadUpdate,
    current_user: dict = Depends(get_current_user),
):
    try:
        oid = ObjectId(thread_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid thread ID.")

    cached = await _get_thread_cache(thread_id)
    if cached:
        result = cached.model_copy(update={"is_read": body.is_read})
    else:
        doc = await threads_collection.find_one({"_id": oid})
        if not doc:
            raise HTTPException(status_code=404, detail="Thread not found.")
        doc["is_read"] = body.is_read
        result = _serialize_thread(doc)

    await _write_behind(thread_id, {"is_read": body.is_read})
    return result


# ── PATCH /threads/{thread_id}/archive  (write-behind) ───────────────────────

@router.patch("/{thread_id}/archive", response_model=ThreadResponse)
async def toggle_archive(
    thread_id: str,
    current_user: dict = Depends(get_current_user),
):
    try:
        oid = ObjectId(thread_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid thread ID.")

    cached = await _get_thread_cache(thread_id)
    if cached:
        new_val = not cached.is_archived
        result = cached.model_copy(update={"is_archived": new_val})
    else:
        doc = await threads_collection.find_one({"_id": oid})
        if not doc:
            raise HTTPException(status_code=404, detail="Thread not found.")
        new_val = not doc.get("is_archived", False)
        doc["is_archived"] = new_val
        result = _serialize_thread(doc)

    await _write_behind(thread_id, {"is_archived": new_val})
    return result


# ── PATCH /threads/{thread_id}/status  (write-behind) ────────────────────────

@router.patch("/{thread_id}/status", response_model=ThreadResponse)
async def update_status(
    thread_id: str,
    body: StatusUpdate,
    current_user: dict = Depends(get_current_user),
):
    try:
        oid = ObjectId(thread_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid thread ID.")

    cached = await _get_thread_cache(thread_id)
    if cached:
        result = cached.model_copy(update={"status": body.status})
    else:
        doc = await threads_collection.find_one({"_id": oid})
        if not doc:
            raise HTTPException(status_code=404, detail="Thread not found.")
        doc["status"] = body.status
        result = _serialize_thread(doc)

    await _write_behind(thread_id, {"status": body.status})
    return result


# ── POST /threads/{thread_id}/client-action  (write-behind) ───────────────────

@router.post("/{thread_id}/client-action", response_model=ThreadResponse)
async def client_action(
    thread_id: str,
    body: ClientAction,
    current_user: dict = Depends(get_current_user),
):
    if current_user.get("role") != "client":
        raise HTTPException(status_code=403, detail="Only client role can perform this action.")

    try:
        oid = ObjectId(thread_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid thread ID.")

    if body.action == "handled":
        update_fields = {"status": "done"}
        activity_action = "client_handled"
    else:  # take_over
        update_fields = {"ai_label": "assistant_reply", "manual_override": True}
        activity_action = "client_taken_over"

    cached = await _get_thread_cache(thread_id)
    if cached:
        result = cached.model_copy(update=update_fields)
    else:
        doc = await threads_collection.find_one({"_id": oid})
        if not doc:
            raise HTTPException(status_code=404, detail="Thread not found.")
        doc.update(update_fields)
        result = _serialize_thread(doc)

    await _write_behind(thread_id, update_fields)

    await activity_collection.insert_one({
        "thread_id": oid,
        "action_by": current_user["_id"],
        "role": "client",
        "action": activity_action,
        "timestamp": datetime.now(timezone.utc),
    })

    return result