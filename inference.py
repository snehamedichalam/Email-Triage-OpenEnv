import os
import json
import requests
from openai import OpenAI

# Config from environment variables
API_BASE_URL = os.environ.get("API_BASE_URL", "https://api.openai.com/v1")
MODEL_NAME = os.environ.get("MODEL_NAME", "gpt-4o-mini")
HF_TOKEN = os.environ.get("HF_TOKEN", "")
ENV_URL = os.environ.get("ENV_URL", "http://localhost:8000")

client = OpenAI(
    api_key=HF_TOKEN if HF_TOKEN else os.environ.get("OPENAI_API_KEY", ""),
    base_url=API_BASE_URL
)

def call_llm(prompt: str) -> str:
    """Call LLM and return response"""
    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )
        return response.choices[0].message.content
    except Exception as e:
        print(json.dumps({"event": "ERROR", "message": str(e)}))
        return "{}"

def run_task(task_name: str) -> float:
    """Run one full task episode"""
    print(json.dumps({
        "event": "START",
        "task": task_name,
        "model": MODEL_NAME
    }))

    # Reset environment
    res = requests.post(
        f"{ENV_URL}/reset",
        params={"task_name": task_name}
    )
    obs = res.json()

    step_num = 0
    total_reward = 0.0
    done = False

    while not done:
        step_num += 1
        email = obs["email"]
        instructions = obs["instructions"]

        # Build prompt based on task
        if task_name == "easy":
            format_hint = '{"action_type": "label", "label": "spam"} or {"action_type": "label", "label": "not_spam"}'
        elif task_name == "medium":
            format_hint = '{"action_type": "prioritize", "priority": 3}'
        else:
            format_hint = '{"action_type": "route", "department": "support", "reply_suggestion": "Thank you for contacting us..."}'

        prompt = f"""
You are an email triage assistant.

Instructions: {instructions}
Task: {task_name}

Email Details:
- Subject: {email['subject']}
- From: {email['sender']}
- Body: {email['body']}

Respond ONLY with valid JSON in this format:
{format_hint}

No explanation. Just JSON.
"""

        # Get LLM response
        llm_response = call_llm(prompt)

        # Parse response
        try:
            clean = llm_response.strip()
            if "```" in clean:
                clean = clean.split("```")[1]
                if clean.startswith("json"):
                    clean = clean[4:]
            action_data = json.loads(clean.strip())
        except Exception:
            if task_name == "easy":
                action_data = {"action_type": "label", "label": "not_spam"}
            elif task_name == "medium":
                action_data = {"action_type": "prioritize", "priority": 3}
            else:
                action_data = {
                    "action_type": "route",
                    "department": "support",
                    "reply_suggestion": "Thank you for contacting us."
                }

        # Send action to environment
        step_res = requests.post(
            f"{ENV_URL}/step",
            json=action_data
        )
        result = step_res.json()

        reward = result["reward"]["score"]
        total_reward += reward
        done = result["done"]

        print(json.dumps({
            "event": "STEP",
            "task": task_name,
            "step": step_num,
            "action": action_data,
            "reward": reward,
            "done": done
        }))

        if not done and result.get("observation"):
            obs = result["observation"]

    print(json.dumps({
        "event": "END",
        "task": task_name,
        "total_reward": round(total_reward, 2),
        "steps": step_num
    }))

    return total_reward


if __name__ == "__main__":
    tasks = ["easy", "medium", "hard"]
    all_scores = {}

    for task in tasks:
        score = run_task(task)
        all_scores[task] = round(score, 2)

    print(json.dumps({
        "event": "SUMMARY",
        "scores": all_scores
    }))