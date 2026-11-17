#!/bin/bash

# ═══════════════════════════════════════════════
#  InboxAI — Grok AI Endpoints Test Script
# ═══════════════════════════════════════════════

BASE_URL="http://localhost:8000"

# ── CONFIG: Apna email/password yahan daalo ──
EMAIL="hrithiknonia66@gmail.com"
PASSWORD="Hritik@123"

echo ""
echo "🤖 InboxAI — Grok AI Test Script"
echo "================================="

# ─────────────────────────────────────────────
# STEP 1: Login → Token lo
# ─────────────────────────────────────────────
echo ""
echo "📌 Step 1: Login kar rahe hain..."

LOGIN_RESPONSE=$(curl -s -X POST "$BASE_URL/auth/login" \
  -H "Content-Type: application/json" \
  -d "{\"email\": \"$EMAIL\", \"password\": \"$PASSWORD\"}")

echo "Login Response: $LOGIN_RESPONSE"

TOKEN=$(echo $LOGIN_RESPONSE | python3 -c "import sys,json; print(json.load(sys.stdin).get('access_token',''))" 2>/dev/null)

if [ -z "$TOKEN" ]; then
  echo "❌ Login failed. TOKEN nahi mila. Email/password check karo."
  exit 1
fi

echo "✅ Token mila: ${TOKEN:0:30}..."

# ─────────────────────────────────────────────
# STEP 2: Pehla Thread ID lo
# ─────────────────────────────────────────────
echo ""
echo "📌 Step 2: Threads se pehla ID nikal rahe hain..."

THREADS_RESPONSE=$(curl -s -X GET "$BASE_URL/threads/?limit=1" \
  -H "Authorization: Bearer $TOKEN")

echo "Threads Response (first): $THREADS_RESPONSE"

THREAD_ID=$(echo $THREADS_RESPONSE | python3 -c "
import sys, json
data = json.load(sys.stdin)
threads = data.get('threads') or data.get('data') or data
if isinstance(threads, list) and len(threads) > 0:
    print(threads[0].get('_id') or threads[0].get('id',''))
" 2>/dev/null)

if [ -z "$THREAD_ID" ]; then
  echo "❌ Thread ID nahi mila. /threads/ response check karo."
  exit 1
fi

echo "✅ Thread ID mila: $THREAD_ID"

# ─────────────────────────────────────────────
# TEST 1: Re-classify
# ─────────────────────────────────────────────
echo ""
echo "════════════════════════════════════"
echo "🧪 TEST 1: AI Re-classify"
echo "════════════════════════════════════"

CLASSIFY_RESPONSE=$(curl -s -X POST "$BASE_URL/ai/classify/$THREAD_ID" \
  -H "Authorization: Bearer $TOKEN")

echo "$CLASSIFY_RESPONSE" | python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
    data = d.get('data', {})
    print('✅ Classify Result:')
    print(f\"   Label      : {data.get('ai_label')}\")
    print(f\"   Confidence : {data.get('ai_confidence')}\")
    print(f\"   Reason     : {data.get('ai_reason')}\")
    print(f\"   Summary    : {data.get('ai_summary', '')[:100]}...\")
    print(f\"   Prev Label : {data.get('previous_label')}\")
except:
    print('Raw:', sys.stdin.read())
" 2>/dev/null || echo "$CLASSIFY_RESPONSE"

# ─────────────────────────────────────────────
# TEST 2: Chat
# ─────────────────────────────────────────────
echo ""
echo "════════════════════════════════════"
echo "🧪 TEST 2: AI Chat"
echo "════════════════════════════════════"

CHAT_RESPONSE=$(curl -s -X POST "$BASE_URL/ai/chat" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"message": "Kaun se emails client ke liye hain? List karo."}')

echo "$CHAT_RESPONSE" | python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
    data = d.get('data', {})
    print('✅ Chat Result:')
    print(f\"   Threads used : {data.get('threads_used')}\")
    print(f\"   Answer       :\")
    print(data.get('answer',''))
except:
    print('Raw:', sys.stdin.read())
" 2>/dev/null || echo "$CHAT_RESPONSE"

# ─────────────────────────────────────────────
# TEST 3: Draft Generate
# ─────────────────────────────────────────────
echo ""
echo "════════════════════════════════════"
echo "🧪 TEST 3: AI Draft Generate"
echo "════════════════════════════════════"

DRAFT_RESPONSE=$(curl -s -X POST "$BASE_URL/ai/draft/$THREAD_ID" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"instruction": "Politely decline the meeting request"}')

echo "$DRAFT_RESPONSE" | python3 -c "
import sys, json
try:
    d = json.load(sys.stdin)
    data = d.get('data', {})
    print('✅ Draft Result:')
    print(f\"   Subject : {data.get('subject')}\")
    print(f\"   Model   : {data.get('generated_by')}\")
    print(f\"   Draft   :\")
    print(data.get('draft_body',''))
except:
    print('Raw:', sys.stdin.read())
" 2>/dev/null || echo "$DRAFT_RESPONSE"

# ─────────────────────────────────────────────
echo ""
echo "================================="
echo "✅ Saare tests complete!"
echo "================================="
echo ""