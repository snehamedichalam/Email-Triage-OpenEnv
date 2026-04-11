import os
import json
import requests
from openai import OpenAI

# Config from environment variables
API_BASE_URL = os.environ.get("API_BASE_URL", "https://api.openai.com/v1")
MODEL_NAME = os.environ.get("MODEL_NAME", "gpt-4o-mini")
HF_TOKEN = os.environ.get("HF_TOKEN", "")
ENV_URL = os.environ.get("ENV_URL", "https://sne23-email-triage-env.hf.space")

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


def get_default_action(task_name: str) -> dict:
    """Return safe default action for each task"""
    if task_name == "easy":
        return {"action_type": "label", "label": "not_spam"}
    elif task_name == "medium":
        return {"action_type": "prioritize", "priority": 3}
    else:
        return {
            "action_type": "route",
            "department": "support",
            "reply_suggestion": "Thank you for contacting us. We will look into this and get back to you shortly."
        }


def run_task(task_name: str) -> float:
    """Run one full task episode"""
    print(json.dumps({
        "event": "START",
        "task": task_name,
        "model": MODEL_NAME
    }))

    # Reset environment
    try:
        res = requests.post(
            f"{ENV_URL}/reset",
            params={"task_name": task_name},
            timeout=30
        )
        res.raise_for_status()
        obs = res.json()
    except Exception as e:
        print(json.dumps({"event": "ERROR", "message": f"Reset failed: {str(e)}"}))
        return 0.0

    step_num = 0
    total_reward = 0.0
    done = False

    while not done:
        step_num += 1

        try:
            email = obs.get("email", {})
            instructions = obs.get("instructions", "")

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
- Subject: {email.get('subject', '')}
- From: {email.get('sender', '')}
- Body: {email.get('body', '')}

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
                action_data = get_default_action(task_name)

            # Send action to environment
            try:
                step_res = requests.post(
                    f"{ENV_URL}/step",
                    json=action_data,
                    timeout=30
                )
                step_res.raise_for_status()
                result = step_res.json()
            except Exception as e:
                print(json.dumps({"event": "ERROR", "message": f"Step request failed: {str(e)}"}))
                break

            # Safely extract reward
            if "reward" not in result:
                print(json.dumps({
                    "event": "ERROR",
                    "message": f"No reward in response: {result}"
                }))
                # Use default reward of 0 and check if done
                reward = 0.0
                done = result.get("done", True)
            else:
                reward = result["reward"].get("score", 0.0)
                done = result.get("done", True)

            total_reward += reward

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

        except Exception as e:
            print(json.dumps({
                "event": "ERROR",
                "message": f"Step {step_num} failed: {str(e)}"
            }))
            break

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
        try:
            score = run_task(task)
            all_scores[task] = round(score, 2)
        except Exception as e:
            print(json.dumps({"event": "ERROR", "task": task, "message": str(e)}))
            all_scores[task] = 0.0

    print(json.dumps({
        "event": "SUMMARY",
        "scores": all_scores
    }))
