import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import client as mongo_client, db
from app.database import (
    users_collection,
    threads_collection,
    drafts_collection,
    activity_collection,
)
from app.redis import ping_redis, close_redis, redis_client

from app.routes.auth import router as auth_router

logger = logging.getLogger(__name__)


async def create_indexes() -> None:
    # users
    await users_collection.create_index("email", unique=True)
    await users_collection.create_index("role")
    await users_collection.create_index("linked_assistant_id")

    # threads
    await threads_collection.create_index("owner_user_id")
    await threads_collection.create_index("ai_label")
    await threads_collection.create_index("is_read")
    await threads_collection.create_index("is_archived")
    await threads_collection.create_index("is_important")
    await threads_collection.create_index([("last_message_at", -1)])
    await threads_collection.create_index("segment")
    await threads_collection.create_index("status")
    await threads_collection.create_index([
        ("owner_user_id", 1),
        ("ai_label", 1),
        ("last_message_at", -1),
    ])
    await threads_collection.create_index([
        ("owner_user_id", 1),
        ("is_archived", 1),
        ("last_message_at", -1),
    ])

    # drafts
    await drafts_collection.create_index("thread_id")
    await drafts_collection.create_index("created_by")
    await drafts_collection.create_index("status")

    # activity
    await activity_collection.create_index("thread_id")
    await activity_collection.create_index("action_by")

    logger.info("All indexes created successfully")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # ─── Startup ───
    # MongoDB ping
    try:
        await mongo_client.admin.command("ping")
        logger.info("MongoDB connected successfully")
    except Exception as exc:
        logger.error("MongoDB connection failed: %s", exc)
        raise

    # Indexes
    await create_indexes()

    # Redis ping
    await ping_redis()

    yield

    # ─── Shutdown ───
    mongo_client.close()
    logger.info("MongoDB connection closed")

    await close_redis()


app = FastAPI(
    title="InboxAI API",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# include routers
app.include_router(auth_router)


@app.get("/")
async def root():
    return {"status": "InboxAI API running"}


@app.get("/health")
async def health():
    # MongoDB check
    try:
        await mongo_client.admin.command("ping")
        mongo_status = "connected"
    except Exception:
        mongo_status = "disconnected"

    # Redis check
    try:
        await redis_client.ping()
        redis_status = "connected"
    except Exception:
        redis_status = "disconnected"

    return {
        "status": "ok" if mongo_status == "connected" else "degraded",
        "mongodb": mongo_status,
        "redis": redis_status,
    }