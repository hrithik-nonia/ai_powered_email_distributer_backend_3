from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from app.middleware.auth_middleware import get_current_user, require_role
from app.services.classifier import classify_thread
from app.services.ai_chat import chat_with_inbox
from app.services.draft_generator import generate_draft

router = APIRouter(prefix="/ai", tags=["AI"])


# ── Request schemas ────────────────────────────────────────────────

class ChatRequest(BaseModel):
    message: str

class DraftRequest(BaseModel):
    instruction: str = ""   # Optional tone/intent override


# ── 1. Re-classify a thread ───────────────────────────────────────

@router.post("/classify/{thread_id}")
async def reclassify_thread(
    thread_id: str,
    current_user: dict = Depends(require_role("assistant", "client"))
):
    """
    Re-classify any thread using Grok AI.
    Updates ai_label, ai_confidence, ai_reason, ai_summary in MongoDB.
    """
    try:
        result = await classify_thread(thread_id)
        return {
            "success": True,
            "message": "Thread classified successfully",
            "data": result
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Grok AI error: {str(e)}")


# ── 2. Chat with inbox ────────────────────────────────────────────

@router.post("/chat")
async def ask_ai(
    body: ChatRequest,
    current_user: dict = Depends(require_role("assistant", "client"))
):
    """
    Ask anything about your inbox.
    Grok uses latest 15 threads as context and answers your question.
    """
    if not body.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    try:
        result = await chat_with_inbox(
            user_message=body.message,
            user_id=str(current_user["_id"])
        )
        return {
            "success": True,
            "data": result
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Grok AI error: {str(e)}")


# ── 3. Generate draft reply ───────────────────────────────────────

@router.post("/draft/{thread_id}")
async def generate_reply_draft(
    thread_id: str,
    body: DraftRequest,
    current_user: dict = Depends(require_role("assistant", "client"))
):
    """
    Generate a professional reply draft for any thread.
    Optional: pass 'instruction' to customize tone (e.g. "politely decline")
    """
    try:
        result = await generate_draft(
            thread_id=thread_id,
            instruction=body.instruction
        )
        return {
            "success": True,
            "message": "Draft generated successfully",
            "data": result
        }
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Grok AI error: {str(e)}")