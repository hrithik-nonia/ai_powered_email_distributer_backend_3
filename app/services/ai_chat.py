from openai import AsyncOpenAI
from app.database import threads_collection
import os
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file

client = AsyncOpenAI(
    api_key=os.getenv("GROK_API_KEY"),
    base_url=os.getenv("GROK_BASE_URL", "https://openrouter.ai/api/v1")
)

CHAT_SYSTEM_PROMPT = """You are an intelligent email assistant for an executive PA (Personal Assistant) system.

You have access to a summary of the user's email threads. Answer questions about these emails clearly and concisely.

Guidelines:
- Be direct and specific. Reference actual email subjects and senders when relevant.
- If asked about a category (e.g., "client emails"), list the relevant ones briefly.
- If asked to summarize, give a crisp 2-3 line answer.
- Do not make up emails that aren't in the context.
- Respond in the same language the user asks in (English or Hinglish is fine)."""


def _build_inbox_context(threads: list) -> str:
    """Build a compact context string from up to 15 threads."""
    lines = ["=== INBOX CONTEXT (Latest 15 Threads) ===\n"]

    for i, t in enumerate(threads, 1):
        lines.append(f"{i}. Subject: {t.get('subject', 'N/A')}")
        lines.append(f"   From: {t.get('sender_name', '')} <{t.get('sender_email', '')}>")
        lines.append(f"   Label: {t.get('ai_label', 'unknown')}")
        lines.append(f"   Summary: {t.get('ai_summary') or 'No summary available'}")
        lines.append(f"   Important: {'Yes' if t.get('is_important') else 'No'}")
        lines.append("")

    return "\n".join(lines)


async def chat_with_inbox(user_message: str, user_id: str) -> dict:
    """
    Load up to 15 threads for the user, build context,
    send user's question to Grok, return answer.
    """
    # 1. Fetch latest 15 threads for this user
    cursor = threads_collection.find(
        {"owner_user_id": user_id}
    ).sort("last_message_at", -1).limit(15)

    threads = await cursor.to_list(length=15)

    if not threads:
        return {
            "answer": "Aapka inbox empty hai. Koi threads nahi mile.",
            "threads_used": 0
        }

    # 2. Build context
    inbox_context = _build_inbox_context(threads)

    # 3. Call Grok
    response = await client.chat.completions.create(
        model=os.getenv("GROK_MODEL", "openrouter/auto"),
        messages=[
            {"role": "system", "content": CHAT_SYSTEM_PROMPT},
            {
                "role": "user",
                "content": f"{inbox_context}\n\n---\nUser Question: {user_message}"
            }
        ],
        temperature=0.3,
        max_tokens=600
    )

    answer = response.choices[0].message.content.strip()

    return {
        "answer": answer,
        "threads_used": len(threads)
    }