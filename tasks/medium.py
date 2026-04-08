EMAILS = [
    {
        "id": "m1",
        "subject": "Server is DOWN - production affected",
        "body": "Critical outage affecting all users. Need immediate help.",
        "sender": "oncall@company.com",
        "timestamp": "2024-01-01 09:00",
        "correct_priority": 5
    },
    {
        "id": "m2",
        "subject": "Newsletter: January updates",
        "body": "Here are this month's company updates and events.",
        "sender": "newsletter@company.com",
        "timestamp": "2024-01-01 09:01",
        "correct_priority": 1
    },
    {
        "id": "m3",
        "subject": "Client meeting rescheduled to tomorrow",
        "body": "Our key client moved the meeting to tomorrow 2pm.",
        "sender": "sales@company.com",
        "timestamp": "2024-01-01 09:02",
        "correct_priority": 4
    },
    {
        "id": "m4",
        "subject": "Office supplies order",
        "body": "Reminder to place the quarterly office supplies order.",
        "sender": "admin@company.com",
        "timestamp": "2024-01-01 09:03",
        "correct_priority": 2
    },
    {
        "id": "m5",
        "subject": "Security patch needs deployment this week",
        "body": "A moderate security vulnerability needs patching by Friday.",
        "sender": "security@company.com",
        "timestamp": "2024-01-01 09:04",
        "correct_priority": 3
    }
]

def get_emails():
    return EMAILS

def grade(email_id: str, priority: int, emails: list) -> float:
    """
    Exact match = 1.0
    Off by 1 = 0.7
    Off by 2 = 0.4
    More than 2 = 0.0
    """
    for email in emails:
        if email["id"] == email_id:
            diff = abs(priority - email["correct_priority"])
            if diff == 0:
                return 1.0
            elif diff == 1:
                return 0.7
            elif diff == 2:
                return 0.4
            else:
                return 0.0
    return 0.0