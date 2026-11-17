"""
seed_service.py
Populates 25 demo email threads for a newly connected demo account.
"""

import uuid
from datetime import datetime, timezone, timedelta
from bson import ObjectId

from app.database import db


def _msg_id() -> str:
    return f"<{uuid.uuid4().hex}@demo.inboxai.com>"


def _dt(days_ago: float, hour: int = 10, minute: int = 0) -> datetime:
    base = datetime.now(timezone.utc).replace(hour=hour, minute=minute, second=0, microsecond=0)
    return base - timedelta(days=days_ago)


# ─────────────────────────────────────────────────────────────────────────────
# Thread definitions
# ─────────────────────────────────────────────────────────────────────────────

def _build_threads(user_id: ObjectId, account_id: ObjectId) -> list[dict]:
    now = datetime.now(timezone.utc)

    threads = []

    # ── 5× assistant_reply (scheduling, booking, admin) ──────────────────────

    threads.append({
        "_id": ObjectId(),
        "account_id": account_id,
        "owner_user_id": user_id,
        "subject": "Board Meeting — Room Booking Confirmation",
        "participants": [
            {"name": "Sarah Chen", "email": "sarah.chen@meridianvc.com"},
            {"name": "James Okafor", "email": "james.okafor@meridianvc.com"},
        ],
        "messages": [
            {
                "message_id": _msg_id(),
                "from_name": "Sarah Chen",
                "from_email": "sarah.chen@meridianvc.com",
                "to": ["demo@inboxai.com"],
                "body": (
                    "Hi,\n\nCould you please book the Meridian conference room for our Q3 board meeting "
                    "on November 22nd from 2–5 PM? We'll need AV setup and catering for 12 people.\n\nThanks,\nSarah"
                ),
                "timestamp": _dt(3, 9, 15),
                "is_read": True,
            },
            {
                "message_id": _msg_id(),
                "from_name": "James Okafor",
                "from_email": "james.okafor@meridianvc.com",
                "to": ["demo@inboxai.com", "sarah.chen@meridianvc.com"],
                "body": (
                    "Also, please add a 30-min buffer before for setup. "
                    "The AV tech needs access from 1:30 PM."
                ),
                "timestamp": _dt(3, 11, 42),
                "is_read": False,
            },
        ],
        "ai_label": "assistant_reply",
        "ai_confidence": 0.95,
        "ai_reason": "Logistics request with clear action items — room booking and catering.",
        "ai_summary": "Board room booking for Nov 22 Q3 meeting; AV + catering for 12; setup from 1:30 PM.",
        "ai_extracted_dates": ["2026-11-22T14:00:00Z", "2026-11-22T13:30:00Z"],
        "manual_override": False,
        "segment": ["action_required", "general"],
        "is_important": False,
        "is_read": False,
        "is_archived": False,
        "status": "open",
        "last_message_at": _dt(3, 11, 42),
        "created_at": _dt(3, 9, 15),
    })

    threads.append({
        "_id": ObjectId(),
        "account_id": account_id,
        "owner_user_id": user_id,
        "subject": "Flight & Hotel for SF Summit — October 14–16",
        "participants": [
            {"name": "Priya Nair", "email": "priya.nair@atlaspartners.io"},
        ],
        "messages": [
            {
                "message_id": _msg_id(),
                "from_name": "Priya Nair",
                "from_email": "priya.nair@atlaspartners.io",
                "to": ["demo@inboxai.com"],
                "body": (
                    "Hi,\n\nI need to attend the FinTech Summit in San Francisco from Oct 14–16. "
                    "Please book:\n- Flight from NYC (JFK) arriving by noon Oct 14\n"
                    "- Hotel near Moscone Center (2 nights)\n\nPrefer aisle seat. Budget ~$1,800.\n\nPriya"
                ),
                "timestamp": _dt(5, 8, 30),
                "is_read": True,
            },
            {
                "message_id": _msg_id(),
                "from_name": "Priya Nair",
                "from_email": "priya.nair@atlaspartners.io",
                "to": ["demo@inboxai.com"],
                "body": "Also check if the Marriott Marquis has availability — my preference.",
                "timestamp": _dt(5, 10, 5),
                "is_read": False,
            },
        ],
        "ai_label": "assistant_reply",
        "ai_confidence": 0.97,
        "ai_reason": "Travel booking request with clear dates, budget, and preferences.",
        "ai_summary": "Book JFK→SFO flight and Marriott Marquis for Oct 14–16 FinTech Summit; aisle seat; $1,800 budget.",
        "ai_extracted_dates": ["2026-10-14", "2026-10-16"],
        "manual_override": False,
        "segment": ["action_required"],
        "is_important": False,
        "is_read": False,
        "is_archived": False,
        "status": "open",
        "last_message_at": _dt(5, 10, 5),
        "created_at": _dt(5, 8, 30),
    })

    threads.append({
        "_id": ObjectId(),
        "account_id": account_id,
        "owner_user_id": user_id,
        "subject": "Annual Report Printing — 200 Copies",
        "participants": [
            {"name": "Daniel Ferreira", "email": "d.ferreira@novaequity.com"},
        ],
        "messages": [
            {
                "message_id": _msg_id(),
                "from_name": "Daniel Ferreira",
                "from_email": "d.ferreira@novaequity.com",
                "to": ["demo@inboxai.com"],
                "body": (
                    "Please arrange printing of our 2025 Annual Report — 200 copies, saddle-stitched, "
                    "full colour on 150gsm gloss. Files attached. Needed by Nov 20.\n\nThanks, Daniel"
                ),
                "timestamp": _dt(7, 14, 20),
                "is_read": True,
            },
            {
                "message_id": _msg_id(),
                "from_name": "Daniel Ferreira",
                "from_email": "d.ferreira@novaequity.com",
                "to": ["demo@inboxai.com"],
                "body": "CC the finance team once you have a quote please.",
                "timestamp": _dt(6, 9, 10),
                "is_read": True,
            },
            {
                "message_id": _msg_id(),
                "from_name": "Daniel Ferreira",
                "from_email": "d.ferreira@novaequity.com",
                "to": ["demo@inboxai.com"],
                "body": "Any update on the quote? Deadline is tight.",
                "timestamp": _dt(1, 8, 55),
                "is_read": False,
            },
        ],
        "ai_label": "assistant_reply",
        "ai_confidence": 0.93,
        "ai_reason": "Administrative task — vendor coordination for print job.",
        "ai_summary": "Get print quote for 200 copies of 2025 Annual Report; deadline Nov 20; CC finance team.",
        "ai_extracted_dates": ["2026-11-20"],
        "manual_override": False,
        "segment": ["action_required"],
        "is_important": False,
        "is_read": False,
        "is_archived": False,
        "status": "open",
        "last_message_at": _dt(1, 8, 55),
        "created_at": _dt(7, 14, 20),
    })

    threads.append({
        "_id": ObjectId(),
        "account_id": account_id,
        "owner_user_id": user_id,
        "subject": "Expense Report Submission — October",
        "participants": [
            {"name": "Lena Hoffmann", "email": "l.hoffmann@spektrum.de"},
        ],
        "messages": [
            {
                "message_id": _msg_id(),
                "from_name": "Lena Hoffmann",
                "from_email": "l.hoffmann@spektrum.de",
                "to": ["demo@inboxai.com"],
                "body": (
                    "Hi, please submit my October expenses to Finance by Nov 10. "
                    "Total: €3,240. Receipts in the shared Drive folder `/Finance/Lena/Oct26`.\n\nLena"
                ),
                "timestamp": _dt(9, 11, 0),
                "is_read": True,
            },
            {
                "message_id": _msg_id(),
                "from_name": "Lena Hoffmann",
                "from_email": "l.hoffmann@spektrum.de",
                "to": ["demo@inboxai.com"],
                "body": "Let me know once it's done — I need Finance to confirm before the 15th.",
                "timestamp": _dt(2, 16, 30),
                "is_read": False,
            },
        ],
        "ai_label": "assistant_reply",
        "ai_confidence": 0.91,
        "ai_reason": "Administrative task — expense submission with clear deadline.",
        "ai_summary": "Submit Lena's Oct expenses (€3,240) to Finance by Nov 10; confirm before the 15th.",
        "ai_extracted_dates": ["2026-11-10", "2026-11-15"],
        "manual_override": False,
        "segment": ["action_required"],
        "is_important": False,
        "is_read": False,
        "is_archived": False,
        "status": "open",
        "last_message_at": _dt(2, 16, 30),
        "created_at": _dt(9, 11, 0),
    })

    threads.append({
        "_id": ObjectId(),
        "account_id": account_id,
        "owner_user_id": user_id,
        "subject": "Catering Order — Leadership Offsite (Nov 25–26)",
        "participants": [
            {"name": "Marcus Webb", "email": "m.webb@cornerstone.co"},
        ],
        "messages": [
            {
                "message_id": _msg_id(),
                "from_name": "Marcus Webb",
                "from_email": "m.webb@cornerstone.co",
                "to": ["demo@inboxai.com"],
                "body": (
                    "Could you sort out catering for our offsite? 18 attendees, Nov 25–26 at Oakridge Lodge. "
                    "Lunch + dinner each day. 3 vegetarian, 1 vegan, 1 nut allergy. Budget: £120/person/day.\n\nMarcus"
                ),
                "timestamp": _dt(4, 10, 45),
                "is_read": True,
            },
            {
                "message_id": _msg_id(),
                "from_name": "Marcus Webb",
                "from_email": "m.webb@cornerstone.co",
                "to": ["demo@inboxai.com"],
                "body": "Also need tea/coffee station from 8 AM both days.",
                "timestamp": _dt(4, 12, 10),
                "is_read": False,
            },
        ],
        "ai_label": "assistant_reply",
        "ai_confidence": 0.96,
        "ai_reason": "Event logistics — catering coordination with dietary requirements.",
        "ai_summary": "Arrange catering for 18-person offsite Nov 25–26; dietary needs; £120/pp/day; tea station from 8 AM.",
        "ai_extracted_dates": ["2026-11-25", "2026-11-26"],
        "manual_override": False,
        "segment": ["action_required"],
        "is_important": False,
        "is_read": False,
        "is_archived": False,
        "status": "open",
        "last_message_at": _dt(4, 12, 10),
        "created_at": _dt(4, 10, 45),
    })

    # ── 5× client_reply (decisions, approvals, sensitive) ────────────────────

    threads.append({
        "_id": ObjectId(),
        "account_id": account_id,
        "owner_user_id": user_id,
        "subject": "Term Sheet — Series A: Vantage Capital",
        "participants": [
            {"name": "Rachel Kim", "email": "rachel.kim@vantagecap.com"},
            {"name": "Omar Al-Rashid", "email": "omar@venturesync.io"},
        ],
        "messages": [
            {
                "message_id": _msg_id(),
                "from_name": "Rachel Kim",
                "from_email": "rachel.kim@vantagecap.com",
                "to": ["demo@inboxai.com"],
                "body": (
                    "Hi,\n\nPlease find attached our updated term sheet for the $4M Series A. "
                    "Key changes from last draft: pre-money valuation revised to $18M (from $16M), "
                    "pro-rata rights removed. We'd need a decision by Nov 20.\n\nRachel"
                ),
                "timestamp": _dt(6, 9, 0),
                "is_read": True,
            },
            {
                "message_id": _msg_id(),
                "from_name": "Omar Al-Rashid",
                "from_email": "omar@venturesync.io",
                "to": ["demo@inboxai.com", "rachel.kim@vantagecap.com"],
                "body": (
                    "We've reviewed internally. The valuation works for us. "
                    "However, we need to discuss the liquidation preference clause (1.5× non-participating). "
                    "Can we schedule a call this week?"
                ),
                "timestamp": _dt(5, 14, 30),
                "is_read": False,
            },
        ],
        "ai_label": "client_reply",
        "ai_confidence": 0.88,
        "ai_reason": "Investment term negotiation — requires principal decision-maker to respond.",
        "ai_summary": "Vantage Capital $4M Series A term sheet: $18M pre-money, liquidation preference under discussion; decision needed by Nov 20.",
        "ai_extracted_dates": ["2026-11-20"],
        "manual_override": False,
        "segment": ["action_required", "important"],
        "is_important": True,
        "is_read": False,
        "is_archived": False,
        "status": "open",
        "last_message_at": _dt(5, 14, 30),
        "created_at": _dt(6, 9, 0),
    })

    threads.append({
        "_id": ObjectId(),
        "account_id": account_id,
        "owner_user_id": user_id,
        "subject": "Partnership Proposal — Nexus Distribution Agreement",
        "participants": [
            {"name": "Claire Dubois", "email": "c.dubois@nexus-group.fr"},
        ],
        "messages": [
            {
                "message_id": _msg_id(),
                "from_name": "Claire Dubois",
                "from_email": "c.dubois@nexus-group.fr",
                "to": ["demo@inboxai.com"],
                "body": (
                    "Dear team,\n\nFollowing our discussions, we're formalising the distribution "
                    "partnership for the EMEA region. The draft agreement is attached. "
                    "Revenue split: 70/30 in our favour for Year 1, moving to 60/40 from Year 2. "
                    "Exclusivity period: 24 months. Please review and revert with any comments.\n\nClaire"
                ),
                "timestamp": _dt(10, 15, 0),
                "is_read": True,
            },
            {
                "message_id": _msg_id(),
                "from_name": "Claire Dubois",
                "from_email": "c.dubois@nexus-group.fr",
                "to": ["demo@inboxai.com"],
                "body": "Following up — our board needs sign-off before end of month.",
                "timestamp": _dt(2, 9, 20),
                "is_read": False,
            },
        ],
        "ai_label": "client_reply",
        "ai_confidence": 0.85,
        "ai_reason": "Partnership agreement negotiation — legal/commercial decision needed from principal.",
        "ai_summary": "Nexus EMEA distribution deal: 70/30 → 60/40 split, 24-month exclusivity; sign-off required EOM.",
        "ai_extracted_dates": [],
        "manual_override": False,
        "segment": ["action_required"],
        "is_important": False,
        "is_read": False,
        "is_archived": False,
        "status": "open",
        "last_message_at": _dt(2, 9, 20),
        "created_at": _dt(10, 15, 0),
    })

    threads.append({
        "_id": ObjectId(),
        "account_id": account_id,
        "owner_user_id": user_id,
        "subject": "Strategic Pivot — Approval Needed Before Friday",
        "participants": [
            {"name": "Tom Braddock", "email": "t.braddock@helix.ventures"},
        ],
        "messages": [
            {
                "message_id": _msg_id(),
                "from_name": "Tom Braddock",
                "from_email": "t.braddock@helix.ventures",
                "to": ["demo@inboxai.com"],
                "body": (
                    "Hi,\n\nWe need your sign-off on the revised go-to-market strategy before Friday's "
                    "all-hands. The deck has been updated based on last week's customer research. "
                    "Key change: we're deprioritising SMB and doubling down on enterprise. "
                    "Slide 12 has the revenue model. Let me know your thoughts.\n\nTom"
                ),
                "timestamp": _dt(2, 11, 15),
                "is_read": False,
            },
            {
                "message_id": _msg_id(),
                "from_name": "Tom Braddock",
                "from_email": "t.braddock@helix.ventures",
                "to": ["demo@inboxai.com"],
                "body": "Quick reminder — we need this before 5 PM Friday to finalise the deck.",
                "timestamp": _dt(1, 9, 0),
                "is_read": False,
            },
        ],
        "ai_label": "client_reply",
        "ai_confidence": 0.90,
        "ai_reason": "Strategic decision requiring principal approval; time-sensitive.",
        "ai_summary": "Approval needed for GTM pivot to enterprise-only by Friday; see slide 12 for revenue model.",
        "ai_extracted_dates": [],
        "manual_override": False,
        "segment": ["action_required", "important"],
        "is_important": False,
        "is_read": False,
        "is_archived": False,
        "status": "open",
        "last_message_at": _dt(1, 9, 0),
        "created_at": _dt(2, 11, 15),
    })

    threads.append({
        "_id": ObjectId(),
        "account_id": account_id,
        "owner_user_id": user_id,
        "subject": "Acquisition Offer — Preliminary LOI",
        "participants": [
            {"name": "Stephanie Yuen", "email": "s.yuen@apexstrat.com"},
            {"name": "Legal Team", "email": "legal@apexstrat.com"},
        ],
        "messages": [
            {
                "message_id": _msg_id(),
                "from_name": "Stephanie Yuen",
                "from_email": "s.yuen@apexstrat.com",
                "to": ["demo@inboxai.com"],
                "body": (
                    "Dear team,\n\nApex Strategy is pleased to submit a preliminary letter of intent "
                    "to acquire a 60% stake at a $22M valuation. This is non-binding and subject to DD. "
                    "We'd like to open exclusivity discussions. Please treat this as strictly confidential.\n\nStephanie"
                ),
                "timestamp": _dt(14, 16, 0),
                "is_read": True,
            },
            {
                "message_id": _msg_id(),
                "from_name": "Stephanie Yuen",
                "from_email": "s.yuen@apexstrat.com",
                "to": ["demo@inboxai.com"],
                "body": "Following up on the LOI — have you had a chance to review with your advisors?",
                "timestamp": _dt(7, 10, 45),
                "is_read": False,
            },
        ],
        "ai_label": "client_reply",
        "ai_confidence": 0.92,
        "ai_reason": "Acquisition LOI — highly sensitive, requires direct principal response.",
        "ai_summary": "Apex Strategy LOI: 60% stake at $22M valuation; non-binding; exclusivity discussions pending.",
        "ai_extracted_dates": [],
        "manual_override": False,
        "segment": ["important"],
        "is_important": True,
        "is_read": False,
        "is_archived": False,
        "status": "open",
        "last_message_at": _dt(7, 10, 45),
        "created_at": _dt(14, 16, 0),
    })

    threads.append({
        "_id": ObjectId(),
        "account_id": account_id,
        "owner_user_id": user_id,
        "subject": "Investor Update Request — Q3 Portfolio Report",
        "participants": [
            {"name": "Ben Hargreaves", "email": "ben.h@lumenfund.co.uk"},
        ],
        "messages": [
            {
                "message_id": _msg_id(),
                "from_name": "Ben Hargreaves",
                "from_email": "ben.h@lumenfund.co.uk",
                "to": ["demo@inboxai.com"],
                "body": (
                    "Hi,\n\nOur LPs are requesting Q3 portfolio performance figures. "
                    "Could you send the deck from the last board meeting along with updated financials? "
                    "Specifically interested in ARR growth and burn rate.\n\nBen"
                ),
                "timestamp": _dt(3, 14, 0),
                "is_read": True,
            },
            {
                "message_id": _msg_id(),
                "from_name": "Ben Hargreaves",
                "from_email": "ben.h@lumenfund.co.uk",
                "to": ["demo@inboxai.com"],
                "body": "Also — please confirm whether we can share these externally with our LP advisory committee.",
                "timestamp": _dt(1, 11, 30),
                "is_read": False,
            },
        ],
        "ai_label": "client_reply",
        "ai_confidence": 0.83,
        "ai_reason": "Investor data request with confidentiality question — principal must approve sharing.",
        "ai_summary": "Lumen Fund LP update: Q3 board deck + ARR/burn figures requested; confirm if data can be shared externally.",
        "ai_extracted_dates": [],
        "manual_override": False,
        "segment": ["action_required"],
        "is_important": False,
        "is_read": False,
        "is_archived": False,
        "status": "open",
        "last_message_at": _dt(1, 11, 30),
        "created_at": _dt(3, 14, 0),
    })

    # ── 5× no_reply (newsletters, notifications, updates) ────────────────────

    threads.append({
        "_id": ObjectId(),
        "account_id": account_id,
        "owner_user_id": user_id,
        "subject": "Your Stripe Dashboard Summary — October 2026",
        "participants": [
            {"name": "Stripe", "email": "no-reply@stripe.com"},
        ],
        "messages": [
            {
                "message_id": _msg_id(),
                "from_name": "Stripe",
                "from_email": "no-reply@stripe.com",
                "to": ["demo@inboxai.com"],
                "body": (
                    "Here's your October summary:\n\n"
                    "Gross Volume: $142,350\n"
                    "Successful Payments: 1,204\n"
                    "Failed Payments: 23\n"
                    "New Customers: 87\n\n"
                    "View your full dashboard at dashboard.stripe.com"
                ),
                "timestamp": _dt(16, 8, 0),
                "is_read": True,
            },
            {
                "message_id": _msg_id(),
                "from_name": "Stripe",
                "from_email": "no-reply@stripe.com",
                "to": ["demo@inboxai.com"],
                "body": "Reminder: your monthly payout of $138,920 will be deposited on Nov 5.",
                "timestamp": _dt(15, 8, 0),
                "is_read": True,
            },
        ],
        "ai_label": "no_reply",
        "ai_confidence": 0.99,
        "ai_reason": "Automated payment platform summary — no action required.",
        "ai_summary": "Stripe October summary: $142K gross volume, 1,204 payments, $138,920 payout on Nov 5.",
        "ai_extracted_dates": ["2026-11-05"],
        "manual_override": False,
        "segment": ["general"],
        "is_important": False,
        "is_read": True,
        "is_archived": False,
        "status": "done",
        "last_message_at": _dt(15, 8, 0),
        "created_at": _dt(16, 8, 0),
    })

    threads.append({
        "_id": ObjectId(),
        "account_id": account_id,
        "owner_user_id": user_id,
        "subject": "CB Insights Weekly — Top 10 FinTech Deals This Week",
        "participants": [
            {"name": "CB Insights", "email": "newsletter@cbinsights.com"},
        ],
        "messages": [
            {
                "message_id": _msg_id(),
                "from_name": "CB Insights",
                "from_email": "newsletter@cbinsights.com",
                "to": ["demo@inboxai.com"],
                "body": (
                    "This week's top deals:\n\n"
                    "1. Klarna — $500M Series F at $6.7B\n"
                    "2. Payfare — $120M growth round\n"
                    "3. Nuvei — $80M strategic investment\n\n"
                    "Full report: cbinsights.com/research/fintech-deals-nov-2026"
                ),
                "timestamp": _dt(5, 7, 30),
                "is_read": True,
            },
        ],
        "ai_label": "no_reply",
        "ai_confidence": 0.98,
        "ai_reason": "Newsletter — informational, no reply expected.",
        "ai_summary": "CB Insights weekly FinTech deals digest; top deals include Klarna $500M and Payfare $120M.",
        "ai_extracted_dates": [],
        "manual_override": False,
        "segment": ["general"],
        "is_important": False,
        "is_read": True,
        "is_archived": False,
        "status": "done",
        "last_message_at": _dt(5, 7, 30),
        "created_at": _dt(5, 7, 30),
    })

    threads.append({
        "_id": ObjectId(),
        "account_id": account_id,
        "owner_user_id": user_id,
        "subject": "GitHub Actions — Deployment to Production Succeeded",
        "participants": [
            {"name": "GitHub", "email": "noreply@github.com"},
        ],
        "messages": [
            {
                "message_id": _msg_id(),
                "from_name": "GitHub",
                "from_email": "noreply@github.com",
                "to": ["demo@inboxai.com"],
                "body": (
                    "✅ Workflow run succeeded\n\n"
                    "Repository: inboxai/backend\n"
                    "Branch: main\n"
                    "Commit: a3f9c12 — 'feat: add email thread AI classification'\n"
                    "Duration: 2m 34s\n\n"
                    "View run: github.com/inboxai/backend/actions/runs/9823410"
                ),
                "timestamp": _dt(1, 15, 22),
                "is_read": False,
            },
        ],
        "ai_label": "no_reply",
        "ai_confidence": 0.99,
        "ai_reason": "Automated CI/CD notification — no action needed.",
        "ai_summary": "Production deployment succeeded for inboxai/backend commit a3f9c12.",
        "ai_extracted_dates": [],
        "manual_override": False,
        "segment": ["general"],
        "is_important": False,
        "is_read": False,
        "is_archived": False,
        "status": "done",
        "last_message_at": _dt(1, 15, 22),
        "created_at": _dt(1, 15, 22),
    })

    threads.append({
        "_id": ObjectId(),
        "account_id": account_id,
        "owner_user_id": user_id,
        "subject": "AWS Cost Anomaly Detected — November",
        "participants": [
            {"name": "AWS Budgets", "email": "aws-noreply@amazon.com"},
        ],
        "messages": [
            {
                "message_id": _msg_id(),
                "from_name": "AWS Budgets",
                "from_email": "aws-noreply@amazon.com",
                "to": ["demo@inboxai.com"],
                "body": (
                    "An anomaly was detected in your AWS account (ID: 912345678901).\n\n"
                    "Service: Amazon EC2\n"
                    "Expected spend: $340/day\n"
                    "Actual spend: $1,120/day\n"
                    "Anomaly period: Nov 12–14\n\n"
                    "Review in Cost Explorer: console.aws.amazon.com/cost-management"
                ),
                "timestamp": _dt(3, 6, 0),
                "is_read": True,
            },
            {
                "message_id": _msg_id(),
                "from_name": "AWS Budgets",
                "from_email": "aws-noreply@amazon.com",
                "to": ["demo@inboxai.com"],
                "body": "Anomaly resolved. Spend returned to normal on Nov 15.",
                "timestamp": _dt(2, 6, 0),
                "is_read": True,
            },
        ],
        "ai_label": "no_reply",
        "ai_confidence": 0.95,
        "ai_reason": "Automated infrastructure alert — resolved, no action needed.",
        "ai_summary": "AWS EC2 cost spike Nov 12–14 ($1,120/day vs $340 expected); resolved Nov 15.",
        "ai_extracted_dates": ["2026-11-12", "2026-11-15"],
        "manual_override": False,
        "segment": ["general"],
        "is_important": False,
        "is_read": True,
        "is_archived": False,
        "status": "done",
        "last_message_at": _dt(2, 6, 0),
        "created_at": _dt(3, 6, 0),
    })

    threads.append({
        "_id": ObjectId(),
        "account_id": account_id,
        "owner_user_id": user_id,
        "subject": "Notion Update: Team Wiki — Q4 OKRs Published",
        "participants": [
            {"name": "Notion", "email": "notify@makenotion.com"},
        ],
        "messages": [
            {
                "message_id": _msg_id(),
                "from_name": "Notion",
                "from_email": "notify@makenotion.com",
                "to": ["demo@inboxai.com"],
                "body": (
                    "Alex Turner shared a page with you:\n\n"
                    "📄 Q4 2026 OKRs — Company-Wide\n\n"
                    "\"Sharing our Q4 objectives. Please review by Nov 10 and add your team's key results.\"\n\n"
                    "Open in Notion →"
                ),
                "timestamp": _dt(8, 9, 0),
                "is_read": True,
            },
        ],
        "ai_label": "no_reply",
        "ai_confidence": 0.97,
        "ai_reason": "Automated Notion share notification — informational.",
        "ai_summary": "Q4 OKRs page shared on Notion by Alex Turner; review and add key results by Nov 10.",
        "ai_extracted_dates": ["2026-11-10"],
        "manual_override": False,
        "segment": ["general"],
        "is_important": False,
        "is_read": True,
        "is_archived": True,
        "status": "done",
        "last_message_at": _dt(8, 9, 0),
        "created_at": _dt(8, 9, 0),
    })

    # ── 3× needs_review (ambiguous, ai_confidence < 0.6) ─────────────────────

    threads.append({
        "_id": ObjectId(),
        "account_id": account_id,
        "owner_user_id": user_id,
        "subject": "Checking in — Q4 plans",
        "participants": [
            {"name": "Mia Tanaka", "email": "mia.tanaka@futurestack.jp"},
        ],
        "messages": [
            {
                "message_id": _msg_id(),
                "from_name": "Mia Tanaka",
                "from_email": "mia.tanaka@futurestack.jp",
                "to": ["demo@inboxai.com"],
                "body": (
                    "Hey,\n\nHope all is well. Just wanted to touch base about Q4. "
                    "We've had some internal changes and I wanted to see if there's anything on your end "
                    "that could affect our timeline. Would love to reconnect soon.\n\nMia"
                ),
                "timestamp": _dt(6, 11, 0),
                "is_read": True,
            },
            {
                "message_id": _msg_id(),
                "from_name": "Mia Tanaka",
                "from_email": "mia.tanaka@futurestack.jp",
                "to": ["demo@inboxai.com"],
                "body": "Following up on this — just checking you got my previous message.",
                "timestamp": _dt(2, 10, 15),
                "is_read": False,
            },
        ],
        "ai_label": "needs_review",
        "ai_confidence": 0.48,
        "ai_reason": "Ambiguous check-in — unclear if scheduling or business-sensitive. May need personal reply.",
        "ai_summary": "Mia Tanaka (FutureStack) checking in about Q4 timelines; possible rescheduling needed.",
        "ai_extracted_dates": [],
        "manual_override": False,
        "segment": ["general"],
        "is_important": False,
        "is_read": False,
        "is_archived": False,
        "status": "open",
        "last_message_at": _dt(2, 10, 15),
        "created_at": _dt(6, 11, 0),
    })

    threads.append({
        "_id": ObjectId(),
        "account_id": account_id,
        "owner_user_id": user_id,
        "subject": "Introduction — Arvind Mehta, Greenleaf Capital",
        "participants": [
            {"name": "Arvind Mehta", "email": "arvind@greenleafcap.in"},
            {"name": "Zara Patel", "email": "zara.patel@connectedvc.com"},
        ],
        "messages": [
            {
                "message_id": _msg_id(),
                "from_name": "Zara Patel",
                "from_email": "zara.patel@connectedvc.com",
                "to": ["demo@inboxai.com", "arvind@greenleafcap.in"],
                "body": (
                    "Hi both,\n\nHappy to introduce Arvind Mehta from Greenleaf Capital. "
                    "Arvind is exploring opportunities in your sector and wanted to connect. "
                    "I'll leave it with you two to take it from here!\n\nZara"
                ),
                "timestamp": _dt(4, 15, 30),
                "is_read": True,
            },
            {
                "message_id": _msg_id(),
                "from_name": "Arvind Mehta",
                "from_email": "arvind@greenleafcap.in",
                "to": ["demo@inboxai.com"],
                "body": (
                    "Hi,\n\nThanks Zara! Great to meet you. I'd love to learn more about what you're building. "
                    "Could we find 20 minutes this week?\n\nArvind"
                ),
                "timestamp": _dt(3, 9, 50),
                "is_read": False,
            },
        ],
        "ai_label": "needs_review",
        "ai_confidence": 0.52,
        "ai_reason": "Warm intro from investor — could be scheduling (assistant) or investor relationship (client).",
        "ai_summary": "Investor intro via Zara Patel; Arvind Mehta (Greenleaf Capital) wants a 20-min call.",
        "ai_extracted_dates": [],
        "manual_override": False,
        "segment": ["general"],
        "is_important": False,
        "is_read": False,
        "is_archived": False,
        "status": "open",
        "last_message_at": _dt(3, 9, 50),
        "created_at": _dt(4, 15, 30),
    })

    threads.append({
        "_id": ObjectId(),
        "account_id": account_id,
        "owner_user_id": user_id,
        "subject": "Re: Collaboration idea",
        "participants": [
            {"name": "Felix Wagner", "email": "felix.wagner@buildworks.io"},
        ],
        "messages": [
            {
                "message_id": _msg_id(),
                "from_name": "Felix Wagner",
                "from_email": "felix.wagner@buildworks.io",
                "to": ["demo@inboxai.com"],
                "body": (
                    "Hey,\n\nI've been following your work and think there could be some real synergy "
                    "between our platforms. Nothing formal yet — just wanted to gauge interest in "
                    "a conversation. Happy to share more context if that's useful.\n\nFelix"
                ),
                "timestamp": _dt(11, 13, 0),
                "is_read": True,
            },
            {
                "message_id": _msg_id(),
                "from_name": "Felix Wagner",
                "from_email": "felix.wagner@buildworks.io",
                "to": ["demo@inboxai.com"],
                "body": "Following up — any interest in connecting this week?",
                "timestamp": _dt(5, 10, 0),
                "is_read": False,
            },
        ],
        "ai_label": "needs_review",
        "ai_confidence": 0.41,
        "ai_reason": "Vague outreach — unclear if relevant partnership or cold spam. Principal should evaluate.",
        "ai_summary": "Felix Wagner (Buildworks) exploring potential collaboration; vague synergy claim.",
        "ai_extracted_dates": [],
        "manual_override": False,
        "segment": ["general"],
        "is_important": False,
        "is_read": False,
        "is_archived": False,
        "status": "open",
        "last_message_at": _dt(5, 10, 0),
        "created_at": _dt(11, 13, 0),
    })

    # ── 3× meetings + assistant_reply ────────────────────────────────────────

    threads.append({
        "_id": ObjectId(),
        "account_id": account_id,
        "owner_user_id": user_id,
        "subject": "Scheduling: Investor Call — Sequoia LP Meeting",
        "participants": [
            {"name": "Nina Vasquez", "email": "nina.vasquez@sequoiacap.com"},
        ],
        "messages": [
            {
                "message_id": _msg_id(),
                "from_name": "Nina Vasquez",
                "from_email": "nina.vasquez@sequoiacap.com",
                "to": ["demo@inboxai.com"],
                "body": (
                    "Hi,\n\nWe'd like to schedule a 45-minute LP update call with your team. "
                    "Our preference is a slot between Nov 18–22, ideally mornings (9–11 AM PT). "
                    "Could you send a Calendly link or propose three options?\n\nNina"
                ),
                "timestamp": _dt(2, 16, 0),
                "is_read": False,
            },
        ],
        "ai_label": "assistant_reply",
        "ai_confidence": 0.94,
        "ai_reason": "Meeting scheduling request — calendar coordination task.",
        "ai_summary": "Sequoia requesting 45-min LP call Nov 18–22, 9–11 AM PT; send availability.",
        "ai_extracted_dates": ["2026-11-18", "2026-11-22"],
        "manual_override": False,
        "segment": ["meetings", "action_required"],
        "is_important": False,
        "is_read": False,
        "is_archived": False,
        "status": "open",
        "last_message_at": _dt(2, 16, 0),
        "created_at": _dt(2, 16, 0),
    })

    threads.append({
        "_id": ObjectId(),
        "account_id": account_id,
        "owner_user_id": user_id,
        "subject": "Team Standup — Recurring Friday Slot Change",
        "participants": [
            {"name": "Chris Molina", "email": "c.molina@workstream.app"},
        ],
        "messages": [
            {
                "message_id": _msg_id(),
                "from_name": "Chris Molina",
                "from_email": "c.molina@workstream.app",
                "to": ["demo@inboxai.com"],
                "body": (
                    "Hi,\n\nOur Friday standups need to move from 9 AM to 10 AM starting next week — "
                    "conflict with the new executive sync. Can you update the calendar invite for all attendees?\n\nChris"
                ),
                "timestamp": _dt(3, 11, 30),
                "is_read": True,
            },
            {
                "message_id": _msg_id(),
                "from_name": "Chris Molina",
                "from_email": "c.molina@workstream.app",
                "to": ["demo@inboxai.com"],
                "body": "Also check if Lisa and Yusuf accepted the new time — they haven't responded yet.",
                "timestamp": _dt(1, 14, 0),
                "is_read": False,
            },
        ],
        "ai_label": "assistant_reply",
        "ai_confidence": 0.96,
        "ai_reason": "Calendar update task — reschedule recurring meeting.",
        "ai_summary": "Move Friday standup from 9 AM to 10 AM from next week; check acceptance from Lisa and Yusuf.",
        "ai_extracted_dates": [],
        "manual_override": False,
        "segment": ["meetings", "action_required"],
        "is_important": False,
        "is_read": False,
        "is_archived": False,
        "status": "open",
        "last_message_at": _dt(1, 14, 0),
        "created_at": _dt(3, 11, 30),
    })

    threads.append({
        "_id": ObjectId(),
        "account_id": account_id,
        "owner_user_id": user_id,
        "subject": "Demo Call Confirmation — Accenture Procurement",
        "participants": [
            {"name": "Janet Park", "email": "j.park@accenture.com"},
        ],
        "messages": [
            {
                "message_id": _msg_id(),
                "from_name": "Janet Park",
                "from_email": "j.park@accenture.com",
                "to": ["demo@inboxai.com"],
                "body": (
                    "Hi,\n\nWe've confirmed the product demo for Nov 19 at 3 PM EST. "
                    "Please send a Zoom link. Attendees: myself + 3 from our procurement team. "
                    "Could you also prepare a 10-min intro slide before the live demo?\n\nJanet"
                ),
                "timestamp": _dt(4, 10, 0),
                "is_read": True,
            },
            {
                "message_id": _msg_id(),
                "from_name": "Janet Park",
                "from_email": "j.park@accenture.com",
                "to": ["demo@inboxai.com"],
                "body": "Quick question — will the demo cover the API integration features?",
                "timestamp": _dt(1, 16, 45),
                "is_read": False,
            },
        ],
        "ai_label": "assistant_reply",
        "ai_confidence": 0.93,
        "ai_reason": "Meeting setup request — Zoom link and slides needed for a sales demo.",
        "ai_summary": "Accenture demo confirmed Nov 19 at 3 PM EST; send Zoom link + 10-min intro deck; confirm API coverage.",
        "ai_extracted_dates": ["2026-11-19T20:00:00Z"],
        "manual_override": False,
        "segment": ["meetings", "action_required"],
        "is_important": False,
        "is_read": False,
        "is_archived": False,
        "status": "open",
        "last_message_at": _dt(1, 16, 45),
        "created_at": _dt(4, 10, 0),
    })

    # ── 2× waiting ────────────────────────────────────────────────────────────

    threads.append({
        "_id": ObjectId(),
        "account_id": account_id,
        "owner_user_id": user_id,
        "subject": "Contract Signed — Awaiting Countersignature",
        "participants": [
            {"name": "Renata Sousa", "email": "r.sousa@talentbridge.pt"},
        ],
        "messages": [
            {
                "message_id": _msg_id(),
                "from_name": "Renata Sousa",
                "from_email": "r.sousa@talentbridge.pt",
                "to": ["demo@inboxai.com"],
                "body": (
                    "Hi,\n\nI've signed and returned the consulting agreement. "
                    "Please send it back once countersigned. "
                    "We're aiming to kick off on Dec 1.\n\nRenata"
                ),
                "timestamp": _dt(5, 14, 0),
                "is_read": True,
            },
            {
                "message_id": _msg_id(),
                "from_name": "Renata Sousa",
                "from_email": "r.sousa@talentbridge.pt",
                "to": ["demo@inboxai.com"],
                "body": "Any update on the countersignature? We start onboarding next week.",
                "timestamp": _dt(1, 9, 30),
                "is_read": False,
            },
        ],
        "ai_label": "assistant_reply",
        "ai_confidence": 0.88,
        "ai_reason": "Waiting on countersignature — follow-up task for assistant.",
        "ai_summary": "Consulting agreement signed by Renata; awaiting countersignature; Dec 1 kickoff.",
        "ai_extracted_dates": ["2026-12-01"],
        "manual_override": False,
        "segment": ["waiting", "action_required"],
        "is_important": False,
        "is_read": False,
        "is_archived": False,
        "status": "open",
        "last_message_at": _dt(1, 9, 30),
        "created_at": _dt(5, 14, 0),
    })

    threads.append({
        "_id": ObjectId(),
        "account_id": account_id,
        "owner_user_id": user_id,
        "subject": "Design Agency Quote — Waiting on Response",
        "participants": [
            {"name": "Studio Vesper", "email": "hello@studiovesper.com"},
        ],
        "messages": [
            {
                "message_id": _msg_id(),
                "from_name": "demo@inboxai.com",
                "from_email": "demo@inboxai.com",
                "to": ["hello@studiovesper.com"],
                "body": (
                    "Hi Studio Vesper,\n\nWe'd like a quote for a full brand refresh — "
                    "logo, colour palette, website redesign. Timeline: Jan 2027. "
                    "Budget range: $15–25K. Please let us know your availability.\n\nThanks"
                ),
                "timestamp": _dt(7, 11, 0),
                "is_read": True,
            },
            {
                "message_id": _msg_id(),
                "from_name": "Studio Vesper",
                "from_email": "hello@studiovesper.com",
                "to": ["demo@inboxai.com"],
                "body": "Thanks for reaching out! We'll put together a proposal and get back to you within 5 business days.",
                "timestamp": _dt(6, 15, 20),
                "is_read": True,
            },
        ],
        "ai_label": "no_reply",
        "ai_confidence": 0.80,
        "ai_reason": "Waiting on vendor proposal — no action needed until they respond.",
        "ai_summary": "Brand refresh quote requested from Studio Vesper ($15–25K, Jan 2027); proposal expected within 5 business days.",
        "ai_extracted_dates": [],
        "manual_override": False,
        "segment": ["waiting"],
        "is_important": False,
        "is_read": True,
        "is_archived": False,
        "status": "open",
        "last_message_at": _dt(6, 15, 20),
        "created_at": _dt(7, 11, 0),
    })

    # ── 2× is_important=True, client_reply (already counted above: thread[5] and thread[8]) ──
    # Both are already marked is_important=True with ai_label="client_reply".
    # Thread[5] = Series A term sheet (is_important=True)
    # Thread[8] = Acquisition LOI (is_important=True)
    # Total important client_reply threads = 2 ✓

    # ── Verify count ──────────────────────────────────────────────────────────
    # assistant_reply: threads 0–4 = 5
    # client_reply:    threads 5–9 = 5
    # no_reply:        threads 10–14 = 5
    # needs_review:    threads 15–17 = 3
    # meetings:        threads 18–20 = 3  (all assistant_reply)
    # waiting:         threads 21–22 = 2
    # Total = 23 ... need 2 more to reach 25

    # ── 2 more general threads ────────────────────────────────────────────────

    threads.append({
        "_id": ObjectId(),
        "account_id": account_id,
        "owner_user_id": user_id,
        "subject": "LinkedIn Notification — 3 people viewed your profile",
        "participants": [
            {"name": "LinkedIn", "email": "notifications-noreply@linkedin.com"},
        ],
        "messages": [
            {
                "message_id": _msg_id(),
                "from_name": "LinkedIn",
                "from_email": "notifications-noreply@linkedin.com",
                "to": ["demo@inboxai.com"],
                "body": (
                    "3 people viewed your profile this week:\n\n"
                    "• Head of Strategy at Palantir\n"
                    "• Investment Associate at Tiger Global\n"
                    "• Founder & CEO at Stealth Startup\n\n"
                    "See who else viewed your profile →"
                ),
                "timestamp": _dt(2, 7, 0),
                "is_read": True,
            },
        ],
        "ai_label": "no_reply",
        "ai_confidence": 0.99,
        "ai_reason": "Social notification — no action required.",
        "ai_summary": "LinkedIn: 3 profile views from Palantir, Tiger Global, and a stealth founder.",
        "ai_extracted_dates": [],
        "manual_override": False,
        "segment": ["general"],
        "is_important": False,
        "is_read": True,
        "is_archived": False,
        "status": "done",
        "last_message_at": _dt(2, 7, 0),
        "created_at": _dt(2, 7, 0),
    })

    threads.append({
        "_id": ObjectId(),
        "account_id": account_id,
        "owner_user_id": user_id,
        "subject": "Office Lease Renewal — Terms for 2027",
        "participants": [
            {"name": "Greg Ashton", "email": "g.ashton@propertyco.com"},
        ],
        "messages": [
            {
                "message_id": _msg_id(),
                "from_name": "Greg Ashton",
                "from_email": "g.ashton@propertyco.com",
                "to": ["demo@inboxai.com"],
                "body": (
                    "Hi,\n\nYour current lease expires Feb 28, 2027. We'd like to offer a renewal on the following terms:\n"
                    "- 2-year term\n- Rent: £8,500/month (+5% from current)\n"
                    "- Break clause at 12 months\n\n"
                    "Please let us know if you'd like to proceed or discuss further. "
                    "We'll need a decision by Dec 15 to process the paperwork.\n\nGreg"
                ),
                "timestamp": _dt(6, 10, 0),
                "is_read": True,
            },
            {
                "message_id": _msg_id(),
                "from_name": "Greg Ashton",
                "from_email": "g.ashton@propertyco.com",
                "to": ["demo@inboxai.com"],
                "body": "Following up — have you had a chance to review the renewal terms?",
                "timestamp": _dt(1, 11, 0),
                "is_read": False,
            },
        ],
        "ai_label": "client_reply",
        "ai_confidence": 0.78,
        "ai_reason": "Lease renewal — commercial decision requiring principal review before Dec 15.",
        "ai_summary": "Office lease renewal offer: £8,500/month, 2-year term, break at 12 months; decision needed by Dec 15.",
        "ai_extracted_dates": ["2026-12-15", "2027-02-28"],
        "manual_override": False,
        "segment": ["action_required"],
        "is_important": False,
        "is_read": False,
        "is_archived": False,
        "status": "open",
        "last_message_at": _dt(1, 11, 0),
        "created_at": _dt(6, 10, 0),
    })

    return threads


# ─────────────────────────────────────────────────────────────────────────────
# Public function
# ─────────────────────────────────────────────────────────────────────────────

async def seed_threads_for_user(user_id: ObjectId, account_id: ObjectId) -> None:
    """Insert 25 demo email threads for the given user/account."""
    threads = _build_threads(user_id, account_id)
    if threads:
        await db["threads"].insert_many(threads)