EMAILS = [
    {
        "id": "h1",
        "subject": "I can't login to my account",
        "body": "I have been trying to login for 2 days. Please help.",
        "sender": "customer1@gmail.com",
        "timestamp": "2024-01-01 09:00",
        "correct_department": "support",
        "good_reply_keywords": ["password", "reset", "login", "help"]
    },
    {
        "id": "h2",
        "subject": "Interested in your Enterprise plan",
        "body": "We are a company of 500 people. What are your pricing options?",
        "sender": "cto@bigcorp.com",
        "timestamp": "2024-01-01 09:01",
        "correct_department": "sales",
        "good_reply_keywords": ["pricing", "demo", "enterprise", "contact"]
    },
    {
        "id": "h3",
        "subject": "Double charged on my credit card",
        "body": "I was charged twice for my subscription this month.",
        "sender": "angry@customer.com",
        "timestamp": "2024-01-01 09:02",
        "correct_department": "billing",
        "good_reply_keywords": ["refund", "charge", "invoice", "apologize"]
    }
]

def get_emails():
    return EMAILS

def grade(email_id: str, department: str, reply: str, emails: list) -> float:
    """
    Department correct = 0.6 points
    Reply contains good keywords = up to 0.4 points
    Total max = 1.0
    """
    score = 0.0
    for email in emails:
        if email["id"] == email_id:
            if department == email["correct_department"]:
                score += 0.6
            if reply:
                reply_lower = reply.lower()
                keywords = email["good_reply_keywords"]
                matched = sum(1 for kw in keywords if kw in reply_lower)
                keyword_score = (matched / len(keywords)) * 0.4
                score += keyword_score
            return round(score, 2)
    return 0.0