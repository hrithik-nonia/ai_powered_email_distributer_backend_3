from openai import AsyncOpenAI
from app.database import threads_collection
from bson import ObjectId
import os
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file

client = AsyncOpenAI(
    api_key=os.getenv("GROK_API_KEY"),
    base_url=os.getenv("GROK_BASE_URL", "https://openrouter.ai/api/v1")
)

DRAFT_SYSTEM_PROMPT = """You are a professional email writer for an executive's Personal Assistant.

Your job is to write clear, polite, and professional email replies.

Guidelines:
- Match the tone of the original email (formal if formal, friendly if friendly)
- Keep it concise — no fluff, no filler
- If dates/times are mentioned, acknowledge them naturally
- End with a professional sign-off
- Write ONLY the email body — no subject line, no metadata
- Do not add placeholders like [Your Name] — write naturally as the PA"""


def _build_thread_context(thread: dict) -> str:
    """Build thread context for draft generation."""
    lines = []
    lines.append(f"Subject: {thread.get('subject', '')}")
    lines.append(f"Original Sender: {thread.get('sender_name', '')} <{thread.get('sender_email', '')}>")
    lines.append("")
    lines.append("=== Email Thread ===")

    for msg in thread.get("messages", []):
        lines.append(f"\nFrom: {msg.get('from_name', '')} ({msg.get('date', '')})")
        lines.append(f"{msg.get('body', '')}")

    if thread.get("ai_summary"):
        lines.append(f"\n=== AI Summary ===")
        lines.append(thread["ai_summary"])

    return "\n".join(lines)


async def generate_draft(thread_id: str, instruction: str = "") -> dict:
    """
    Fetch thread, generate a professional reply draft using Grok.
    Optional instruction lets user customize the tone/intent.
    """
    # 1. Fetch thread
    thread = await threads_collection.find_one({"_id": ObjectId(thread_id)})
    if not thread:
        raise ValueError(f"Thread {thread_id} not found")

    # 2. Build context
    context = _build_thread_context(thread)

    # 3. Build user prompt
    user_prompt = f"{context}\n\n---\nPlease write a professional reply to this email."
    if instruction:
        user_prompt += f"\n\nSpecial instruction: {instruction}"

    # 4. Call Grok
    response = await client.chat.completions.create(
        model=os.getenv("GROK_MODEL", "openrouter/auto"),
        messages=[
            {"role": "system", "content": DRAFT_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.5,   # Bit more creative for drafts
        max_tokens=800
    )

    draft_body = response.choices[0].message.content.strip()

    return {
        "thread_id":    thread_id,
        "subject":      thread.get("subject", ""),
        "draft_body":   draft_body,
        "instruction":  instruction or None,
        "generated_by": "grok-beta"
    }