from openai import AsyncOpenAI
from app.database import threads_collection
from bson import ObjectId
from datetime import datetime, timezone
import os
import json
import re
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file

client = AsyncOpenAI(
    api_key=os.getenv("GROK_API_KEY"),
    base_url=os.getenv("GROK_BASE_URL", "https://openrouter.ai/api/v1")
)

SYSTEM_PROMPT = """You are an expert email classifier for an executive assistant (PA) system.

Your job is to analyze emails and classify them into exactly one of these labels:

1. assistant_reply   → PA can handle this independently (scheduling, booking, confirmations, admin tasks, routine follow-ups)
2. client_reply      → Requires the client's personal attention (business decisions, LOI, sensitive matters, negotiations, legal)
3. no_reply          → No response needed (newsletters, notifications, automated emails, marketing)
4. needs_review      → Unclear, needs human judgment before action

Respond ONLY with a valid JSON object. No explanation, no markdown, no extra text.

JSON format:
{
  "ai_label": "assistant_reply" | "client_reply" | "no_reply" | "needs_review",
  "ai_confidence": <float between 0.0 and 1.0>,
  "ai_reason": "<one sentence explaining why this label was chosen>",
  "ai_summary": "<2-3 sentence summary of the email thread>",
  "ai_extracted_dates": ["<date string>", ...]
}"""


def _build_thread_text(thread: dict) -> str:
    """Convert thread document into readable text for Grok."""
    lines = []
    lines.append(f"Subject: {thread.get('subject', 'No Subject')}")
    lines.append(f"From: {thread.get('sender_name', '')} <{thread.get('sender_email', '')}>")
    lines.append(f"To: {thread.get('recipient_email', '')}")
    lines.append("")

    messages = thread.get("messages", [])
    for i, msg in enumerate(messages, 1):
        lines.append(f"--- Message {i} ---")
        lines.append(f"From: {msg.get('from_name', '')} <{msg.get('from_email', '')}>")
        lines.append(f"Date: {msg.get('date', '')}")
        lines.append(f"Body: {msg.get('body', '')}")
        lines.append("")

    return "\n".join(lines)


async def classify_thread(thread_id: str) -> dict:
    """
    Fetch thread from MongoDB, send to Grok for classification,
    update MongoDB with result, return updated fields.
    """
    # 1. Fetch thread
    thread = await threads_collection.find_one({"_id": ObjectId(thread_id)})
    if not thread:
        raise ValueError(f"Thread {thread_id} not found")

    # 2. Build prompt
    thread_text = _build_thread_text(thread)

    # 3. Call Grok
    response = await client.chat.completions.create(
        model=os.getenv("GROK_MODEL", "openrouter/auto"),
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": f"Classify this email thread:\n\n{thread_text}"}
        ],
        temperature=0.1,  # Low temp for consistent classification
        max_tokens=500
    )

    raw = response.choices[0].message.content.strip()

    # 4. Parse JSON safely
    try:
        # Strip markdown code blocks if Grok wraps it
        clean = re.sub(r"```(?:json)?|```", "", raw).strip()
        result = json.loads(clean)
    except json.JSONDecodeError:
        # Fallback if Grok doesn't return valid JSON
        result = {
            "ai_label": "needs_review",
            "ai_confidence": 0.0,
            "ai_reason": "AI response could not be parsed. Manual review needed.",
            "ai_summary": raw[:300],
            "ai_extracted_dates": []
        }

    # 5. Validate label
    valid_labels = {"assistant_reply", "client_reply", "no_reply", "needs_review"}
    if result.get("ai_label") not in valid_labels:
        result["ai_label"] = "needs_review"

    # 6. Update MongoDB
    update_data = {
        "ai_label":           result.get("ai_label", "needs_review"),
        "ai_confidence":      float(result.get("ai_confidence", 0.0)),
        "ai_reason":          result.get("ai_reason", ""),
        "ai_summary":         result.get("ai_summary", ""),
        "ai_extracted_dates": result.get("ai_extracted_dates", []),
        "ai_classified_at":   datetime.now(timezone.utc)
    }

    await threads_collection.update_one(
        {"_id": ObjectId(thread_id)},
        {"$set": update_data}
    )

    return {
        "thread_id": thread_id,
        "previous_label": thread.get("ai_label"),
        **update_data,
        "ai_classified_at": update_data["ai_classified_at"].isoformat()
    }