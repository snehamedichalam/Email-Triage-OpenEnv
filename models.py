from pydantic import BaseModel
from typing import Optional

class Email(BaseModel):
    id: str
    subject: str
    body: str
    sender: str
    timestamp: str

class Observation(BaseModel):
    email: Email
    task_name: str
    step_number: int
    max_steps: int
    instructions: str

class Action(BaseModel):
    action_type: str
    label: Optional[str] = None
    priority: Optional[int] = None
    department: Optional[str] = None
    reply_suggestion: Optional[str] = None

class Reward(BaseModel):
    score: float
    reason: str
    done: bool

class StepResult(BaseModel):
    observation: Optional[Observation] = None
    reward: Reward
    done: bool
    info: dict