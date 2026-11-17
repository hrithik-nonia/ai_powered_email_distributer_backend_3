from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from typing import Literal
from datetime import datetime, timezone
from bson import ObjectId

from app.middleware.auth_middleware import get_current_user, require_role
from app.database import accounts_collection       
from app.models.account import AccountResponse
from seed import seed_threads_for_user


router = APIRouter(prefix="/accounts", tags=["accounts"])


def _serialize_account(doc: dict) -> AccountResponse:
    return AccountResponse(
        id=str(doc["_id"]),
        user_id=str(doc["user_id"]),
        provider=doc["provider"],
        email_address=doc["email_address"],
        status=doc["status"],
        last_synced_at=doc["last_synced_at"],
        created_at=doc["created_at"],
    )


@router.post("/connect-demo", response_model=AccountResponse, status_code=201)
async def connect_demo_account(current_user=Depends(require_role("assistant"))):
    user_id = current_user["_id"]
    existing = await accounts_collection.find_one({"user_id": user_id, "provider": "demo"})
    if existing:
        raise HTTPException(status_code=409, detail="A demo account is already connected.")

    now = datetime.now(timezone.utc)
    doc = {
        "user_id": user_id,
        "provider": "demo",
        "email_address": "demo@inboxai.com",
        "status": "connected",
        "last_synced_at": now,
        "created_at": now,
    }
    result = await accounts_collection.insert_one(doc)
    doc["_id"] = result.inserted_id
    await seed_threads_for_user(user_id, result.inserted_id)
    return _serialize_account(doc)


@router.get("/", response_model=list[AccountResponse])
async def list_accounts(current_user=Depends(get_current_user)):
    cursor = accounts_collection.find({"user_id": current_user["_id"]})
    return [_serialize_account(a) for a in await cursor.to_list(length=100)]


class StatusUpdate(BaseModel):
    status: Literal["connected", "disconnected"]


@router.patch("/{account_id}/status", response_model=AccountResponse)
async def update_account_status(
    account_id: str,
    body: StatusUpdate,
    current_user=Depends(require_role("assistant")),
):
    try:
        oid = ObjectId(account_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid account ID.")

    result = await accounts_collection.find_one_and_update(
        {"_id": oid, "user_id": current_user["_id"]},
        {"$set": {"status": body.status, "last_synced_at": datetime.now(timezone.utc)}},
        return_document=True,
    )
    if not result:
        raise HTTPException(status_code=404, detail="Account not found.")
    return _serialize_account(result)