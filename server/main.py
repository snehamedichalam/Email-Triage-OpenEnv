from fastapi import FastAPI, HTTPException
# Add the dots here to signify "same folder"
from server.models import Action, Observation, StepResult 
from server.environment import EmailTriageEnvironment

env = EmailTriageEnvironment()

@app.get("/")
def root():
    return {"status": "ok", "env": "email-triage-openenv"}

@app.get("/health")
def health():
    return {"status": "healthy"}

@app.post("/reset")
def reset(task_name: str = "easy"):
    """Start a new episode"""
    if task_name not in ["easy", "medium", "hard"]:
        raise HTTPException(
            status_code=400,
            detail="task_name must be easy, medium, or hard"
        )
    obs = env.reset(task_name)
    return obs

@app.post("/step")
def step(action: Action):
    """Take one action"""
    if env.current_task is None:
        raise HTTPException(
            status_code=400,
            detail="Call /reset first"
        )
    result = env.step(action)
    return result

@app.get("/state")
def state():
    """Get current state"""
    return env.state()

@app.get("/tasks")
def list_tasks():
    """List all available tasks"""
    return {
        "tasks": [
            {
                "name": "easy",
                "description": "Label emails as spam/not_spam",
                "difficulty": "easy"
            },
            {
                "name": "medium",
                "description": "Prioritize emails 1-5",
                "difficulty": "medium"
            },
            {
                "name": "hard",
                "description": "Route and reply to emails",
                "difficulty": "hard"
            }
        ]
    }