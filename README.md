---
title: Email Triage OpenEnv
emoji: 📧
colorFrom: green
colorTo: blue
sdk: docker
pinned: false
tags:
  - openenv
---

# Email Triage OpenEnv
An OpenEnv-compliant environment where AI agents learn to triage emails
through labeling, prioritization, and routing.

## Environment Description

This environment simulates a real-world email triage system where an AI agent
must process incoming emails and make decisions about them. The agent learns
to handle emails efficiently across three progressive difficulty levels.

## Tasks

### Task 1: Easy - Spam Detection
- **Goal:** Label each email as `spam` or `not_spam`
- **Difficulty:** Easy
- **Max Steps:** 5
- **Scoring:** 1.0 for correct label, 0.0 for wrong label

### Task 2: Medium - Priority Ranking
- **Goal:** Rate each email priority from 1 (low) to 5 (urgent)
- **Difficulty:** Medium
- **Max Steps:** 5
- **Scoring:** 1.0 exact match, 0.7 off by 1, 0.4 off by 2, 0.0 otherwise

### Task 3: Hard - Department Routing
- **Goal:** Route emails to correct department and suggest a reply
- **Difficulty:** Hard
- **Max Steps:** 3
- **Departments:** support, sales, billing
- **Scoring:** 0.6 for correct department + 0.4 for reply quality

## Action Space
```json
{
  "action_type": "label | prioritize | route",
  "label": "spam | not_spam (for easy task)",
  "priority": "1-5 (for medium task)",
  "department": "support | sales | billing (for hard task)",
  "reply_suggestion": "string (for hard task)"
}
```

## Observation Space
```json
{
  "email": {
    "id": "string",
    "subject": "string",
    "body": "string",
    "sender": "string",
    "timestamp": "string"
  },
  "task_name": "string",
  "step_number": "integer",
  "max_steps": "integer",
  "instructions": "string"
}
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| / | GET | Health check |
| /health | GET | Server status |
| /reset | POST | Start new episode |
| /step | POST | Take one action |
| /state | GET | Get current state |
| /tasks | GET | List all tasks |

## Setup and Usage

### Local Setup
```bash
pip install -r requirements.txt
uvicorn main:app --reload
```

### Test the API
```
http://localhost:8000/docs
```

### Run Inference
```bash
export HF_TOKEN=your_token_here
export MODEL_NAME=gpt-4o-mini
export API_BASE_URL=https://api.openai.com/v1
export ENV_URL=http://localhost:8000
python inference.py
```

### Docker
```bash
docker build -t email-triage-env .
docker run -p 7860:7860 email-triage-env
```

## Baseline Scores

| Task | Expected Score |
|------|---------------|
| Easy | ~4.0 / 5.0 |
| Medium | ~3.5 / 5.0 |
| Hard | ~2.0 / 3.0 |

## Environment Variables

| Variable | Description |
|----------|-------------|
| API_BASE_URL | LLM API endpoint |
| MODEL_NAME | Model identifier |
| HF_TOKEN | Hugging Face API key |
| ENV_URL | Environment URL |
