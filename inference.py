import os
import json
import requests
from openai import OpenAI

API_BASE_URL = os.environ.get("API_BASE_URL", "https://api.openai.com/v1")
MODEL_NAME = os.environ.get("MODEL_NAME", "gpt-4o-mini")
HF_TOKEN = os.environ.get("HF_TOKEN", "")
ENV_URL = os.environ.get("ENV_URL", "https://sne23-email-triage-env.hf.space")

client = OpenAI(
    api_key=HF_TOKEN if HF_TOKEN else os.environ.get("OPENAI_API_KEY", ""),
    base_url=API_BASE_URL
)

def call_llm(prompt):
    try:
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[{"role": "user", "content": prompt}],
            temperature=0
        )
        return response.choices[0].message.content
    except Exception as e:
        print("[ERROR] message=" + str(e), flush=True)
        return "{}"

def get_default_action(task_name):
    if task_name == "easy":
        return {"action_type": "label", "label": "not_spam"}
    elif task_name == "medium":
        return {"action_type": "prioritize", "priority": 3}
    else:
        return {"action_type": "route", "department": "support", "reply_suggestion": "Thank you for contacting us."}

def run_task(task_name):
    print("[START] task=" + task_name + " model=" + MODEL_NAME, flush=True)
    try:
        res = requests.post(ENV_URL + "/reset", params={"task_name": task_name}, timeout=30)
        res.raise_for_status()
        obs = res.json()
    except Exception as e:
        print("[ERROR] message=Reset failed: " + str(e), flush=True)
        print("[END] task=" + task_name + " score=0.0 steps=0", flush=True)
        return 0.0

    step_num = 0
    total_reward = 0.0
    done = False

    while not done:
        step_num += 1
        try:
            email = obs.get("email", {})
            instructions = obs.get("instructions", "")
            if task_name == "easy":
                format_hint = '{"action_type": "label", "label": "spam"}'
            elif task_name == "medium":
                format_hint = '{"action_type": "prioritize", "priority": 3}'
            else:
                format_hint = '{"action_type": "route", "department": "support", "reply_suggestion": "..."}'

            prompt = "You are an email triage assistant.\nInstructions: " + instructions + "\nTask: " + task_name + "\nSubject: " + email.get("subject","") + "\nFrom: " + email.get("sender","") + "\nBody: " + email.get("body","") + "\nRespond ONLY with valid JSON like: " + format_hint

            llm_response = call_llm(prompt)

            try:
                clean = llm_response.strip()
                if "```" in clean:
                    clean = clean.split("```")[1]
                    if clean.startswith("json"):
                        clean = clean[4:]
                action_data = json.loads(clean.strip())
            except Exception:
                action_data = get_default_action(task_name)

            try:
                step_res = requests.post(ENV_URL + "/step", json=action_data, timeout=30)
                step_res.raise_for_status()
                result = step_res.json()
            except Exception as e:
                print("[ERROR] message=Step failed: " + str(e), flush=True)
                break

            reward = 0.0
            if "reward" in result:
                reward = result["reward"].get("score", 0.0)
            done = result.get("done", True)
            total_reward += reward

            print("[STEP] task=" + task_name + " step=" + str(step_num) + " reward=" + str(reward) + " done=" + str(done), flush=True)

            if not done and result.get("observation"):
                obs = result["observation"]

        except Exception as e:
            print("[ERROR] message=Step " + str(step_num) + " failed: " + str(e), flush=True)
            break

    print("[END] task=" + task_name + " score=" + str(round(total_reward, 2)) + " steps=" + str(step_num), flush=True)
    return total_reward

if __name__ == "__main__":
    tasks = ["easy", "medium", "hard"]
    all_scores = {}
    for task in tasks:
        try:
            score = run_task(task)
            all_scores[task] = round(score, 2)
        except Exception as e:
            print("[ERROR] task=" + task + " message=" + str(e), flush=True)
            all_scores[task] = 0.0
    print("[SUMMARY] scores=" + json.dumps(all_scores), flush=True)
