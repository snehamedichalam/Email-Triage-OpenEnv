import random
import uuid
from datetime import datetime
from typing import Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

app = FastAPI(
    title="Email Triage OpenEnv",
    description="An OpenEnv-compliant environment for email triage tasks",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Sample email data
# ---------------------------------------------------------------------------

SPAM_EMAILS = [
    {
        "subject": "Congratulations! You've won $1,000,000!",
        "body": "Click here to claim your prize now! Limited time offer. Send your bank details to collect.",
        "sender": "noreply@prize-winner.xyz",
        "label": "spam",
    },
    {
        "subject": "FREE iPhone 15 – Act Now!",
        "body": "You have been selected for a FREE iPhone. Just pay shipping. Click the link below.",
        "sender": "offers@free-gadgets.biz",
        "label": "spam",
    },
    {
        "subject": "Enlarge your business profits overnight",
        "body": "Our secret formula guarantees 500% ROI. Buy now, no questions asked.",
        "sender": "deals@quickmoney.ru",
        "label": "spam",
    },
]

NOT_SPAM_EMAILS = [
    {
        "subject": "Team meeting rescheduled to 3 PM",
        "body": "Hi team, just a heads-up that today's standup has been moved to 3 PM. Please update your calendars.",
        "sender": "manager@company.com",
        "label": "not_spam",
    },
    {
        "subject": "Your invoice #4521 is ready",
        "body": "Dear customer, your invoice for this month is now available in your account dashboard.",
        "sender": "billing@saasproduct.com",
        "label": "not_spam",
    },
    {
        "subject": "Project deadline reminder",
        "body": "This is a reminder that the Q2 report is due by Friday EOD. Please submit via the usual portal.",
        "sender": "projects@company.com",
        "label": "not_spam",
    },
]

PRIORITY_EMAILS = [
    {"subject": "URGENT: Server is down", "body": "Production server has been unreachable for 10 minutes. Customers are affected.", "sender": "alerts@infra.com", "priority": 5},
    {"subject": "Security breach detected", "body": "Unusual login attempts detected from unknown IP. Immediate action required.", "sender": "security@company.com", "priority": 5},
    {"subject": "Meeting tomorrow at 10 AM", "body": "Reminder about our weekly sync tomorrow morning.", "sender": "calendar@company.com", "priority": 3},
    {"subject": "New feature request from client", "body": "Client ABC is requesting a dark mode option. Please review and add to backlog.", "sender": "sales@company.com", "priority": 3},
    {"subject": "Office newsletter – April edition", "body": "Check out this month's company news, upcoming events, and employee spotlight.", "sender": "newsletter@company.com", "priority": 1},
    {"subject": "Lunch order confirmation", "body": "Your lunch order for today has been confirmed and will arrive at 1 PM.", "sender": "food@office.com", "priority": 1},
    {"subject": "Client contract renewal due", "body": "The contract with client XYZ expires in 7 days. Please initiate renewal process.", "sender": "legal@company.com", "priority": 4},
    {"subject": "Bug report: payment gateway failing", "body": "Multiple users reporting payment failures since this morning. Needs immediate investigation.", "sender": "support@company.com", "priority": 5},
]

ROUTING_EMAILS = [
    {"subject": "Can't login to my account", "body": "I've been trying to log in for an hour and keep getting an error. Please help!", "sender": "user123@gmail.com", "department": "support"},
    {"subject": "Interested in your enterprise plan", "body": "Hi, we're a 200-person company looking to upgrade. Can someone from sales reach out?", "sender": "cto@bigcorp.com", "department": "sales"},
    {"subject": "Incorrect charge on my account", "body": "I was charged twice this month. Please refund the duplicate payment.", "sender": "customer@email.com", "department": "billing"},
    {"subject": "How do I export my data?", "body": "I need to download all my data for compliance purposes. What's the process?", "sender": "admin@startup.io", "department": "support"},
    {"subject": "Request for volume discount", "body": "We're planning to buy 50 licenses. Is there a bulk pricing option?", "sender": "procurement@enterprise.com", "department": "sales"},
    {"subject": "Invoice shows wrong amount", "body": "My invoice for March shows $500 but I should be on the $200 plan.", "sender": "finance@client.com", "department": "billing"},
]

TASK_INSTRUCTIONS = {
    "easy": "Label each email as 'spam' or 'not_spam'. Spam emails are unsolicited, deceptive, or promotional junk mail.",
    "medium": "Assign a priority score from 1 (lowest) to 5 (highest/urgent) based on the email content and urgency.",
    "hard": "Route the email to the correct department (support, sales, or billing) and write a brief professional reply suggestion.",
}

# ---------------------------------------------------------------------------
# In-memory state
# ---------------------------------------------------------------------------

state: dict = {}


def get_email_pool(task_name: str):
    if task_name == "easy":
        return SPAM_EMAILS + NOT_SPAM_EMAILS
    elif task_name == "medium":
        return PRIORITY_EMAILS
    else:
        return ROUTING_EMAILS


def make_email(raw: dict) -> dict:
    return {
        "id": str(uuid.uuid4()),
        "subject": raw["subject"],
        "body": raw["body"],
        "sender": raw["sender"],
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }


# ---------------------------------------------------------------------------
# Reward helpers
# ---------------------------------------------------------------------------

def compute_easy_reward(action: dict, ground_truth: dict) -> float:
    return 1.0 if action.get("label") == ground_truth["label"] else 0.0


def compute_medium_reward(action: dict, ground_truth: dict) -> float:
    try:
        diff = abs(int(action.get("priority", 0)) - ground_truth["priority"])
    except (TypeError, ValueError):
        return 0.0
    if diff == 0:
        return 1.0
    elif diff == 1:
        return 0.7
    elif diff == 2:
        return 0.4
    return 0.0


def compute_hard_reward(action: dict, ground_truth: dict) -> float:
    dept_score = 0.6 if action.get("department") == ground_truth["department"] else 0.0
    reply = action.get("reply_suggestion", "")
    reply_score = 0.4 if isinstance(reply, str) and len(reply.strip()) > 10 else 0.0
    return round(dept_score + reply_score, 2)


# ---------------------------------------------------------------------------
# Request / Response models
# ---------------------------------------------------------------------------

class ActionRequest(BaseModel):
    action_type: str
    label: Optional[str] = None
    priority: Optional[int] = None
    department: Optional[str] = None
    reply_suggestion: Optional[str] = None


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@app.get("/")
def root():
    return {"status": "ok", "message": "Email Triage OpenEnv is running"}


@app.get("/health")
def health():
    return {"status": "healthy", "version": "1.0.0"}


@app.get("/tasks")
def list_tasks():
    return {
        "tasks": [
            {"name": "easy", "description": "Label emails as spam or not_spam", "difficulty": "easy", "max_steps": 5},
            {"name": "medium", "description": "Prioritize emails on a scale of 1 to 5", "difficulty": "medium", "max_steps": 5},
            {"name": "hard", "description": "Route emails to correct department and suggest replies", "difficulty": "hard", "max_steps": 3},
        ]
    }


@app.post("/reset")
def reset(task_name: str = "easy"):
    pool = get_email_pool(task_name)
    max_steps = 3 if task_name == "hard" else 5
    selected = random.sample(pool, min(max_steps, len(pool)))

    state["task_name"] = task_name
    state["step_number"] = 0
    state["max_steps"] = max_steps
    state["email_queue"] = selected
    state["total_reward"] = 0.0
    state["done"] = False

    current_raw = selected[0]
    state["current_raw"] = current_raw

    return {
        "email": make_email(current_raw),
        "task_name": task_name,
        "step_number": 0,
        "max_steps": max_steps,
        "instructions": TASK_INSTRUCTIONS[task_name],
    }


@app.post("/step")
def step(action: ActionRequest):
    if not state or state.get("done"):
        return {"error": "Episode not started. Call /reset first."}, 400

    task_name = state["task_name"]
    current_raw = state["current_raw"]

    # Compute reward
    if task_name == "easy":
        reward = compute_easy_reward(action.dict(), current_raw)
    elif task_name == "medium":
        reward = compute_medium_reward(action.dict(), current_raw)
    else:
        reward = compute_hard_reward(action.dict(), current_raw)

    state["total_reward"] += reward
    state["step_number"] += 1

    done = state["step_number"] >= state["max_steps"]
    state["done"] = done

    observation = None
    if not done:
        next_raw = state["email_queue"][state["step_number"]]
        state["current_raw"] = next_raw
        observation = {
            "email": make_email(next_raw),
            "task_name": task_name,
            "step_number": state["step_number"],
            "max_steps": state["max_steps"],
            "instructions": TASK_INSTRUCTIONS[task_name],
        }

    return {
        "reward": {"score": reward},
        "done": done,
        "observation": observation,
        "total_reward": round(state["total_reward"], 2),
    }


@app.get("/state")
def get_state():
    if not state:
        return {"error": "No active episode. Call /reset first."}
    return {
        "task_name": state.get("task_name"),
        "step_number": state.get("step_number"),
        "max_steps": state.get("max_steps"),
        "total_reward": round(state.get("total_reward", 0.0), 2),
        "done": state.get("done"),
    }
