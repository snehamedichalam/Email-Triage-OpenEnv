EMAILS = [
    {
        "id": "e1",
        "subject": "Win a FREE iPhone now!!!",
        "body": "Click here to claim your prize immediately!",
        "sender": "promo@fakesite.xyz",
        "timestamp": "2024-01-01 09:00",
        "correct_label": "spam"
    },
    {
        "id": "e2",
        "subject": "Team meeting tomorrow at 10am",
        "body": "Hi, just a reminder about our weekly sync.",
        "sender": "manager@company.com",
        "timestamp": "2024-01-01 09:05",
        "correct_label": "not_spam"
    },
    {
        "id": "e3",
        "subject": "Your account has been compromised",
        "body": "Send us your password to verify your identity.",
        "sender": "security@totallyreal.ru",
        "timestamp": "2024-01-01 09:10",
        "correct_label": "spam"
    },
    {
        "id": "e4",
        "subject": "Invoice #1234 attached",
        "body": "Please find the invoice for last month attached.",
        "sender": "billing@vendor.com",
        "timestamp": "2024-01-01 09:15",
        "correct_label": "not_spam"
    },
    {
        "id": "e5",
        "subject": "URGENT: You won $1,000,000",
        "body": "You have been selected. Wire transfer fee required.",
        "sender": "winner@lottery-scam.net",
        "timestamp": "2024-01-01 09:20",
        "correct_label": "spam"
    }
]

def get_emails():
    return EMAILS

def grade(email_id: str, label: str, emails: list) -> float:
    """Returns 1.0 if correct, 0.0 if wrong"""
    for email in emails:
        if email["id"] == email_id:
            if label == email["correct_label"]:
                return 1.0
            else:
                return 0.0
    return 0.0