import uuid
from models import Observation, Action, Reward, StepResult, Email
from tasks.easy import get_emails as easy_emails, grade as easy_grade
from tasks.medium import get_emails as medium_emails, grade as medium_grade
from tasks.hard import get_emails as hard_emails, grade as hard_grade

class EmailTriageEnvironment:
    def __init__(self):
        self.current_task = None
        self.emails = []
        self.current_index = 0
        self.total_reward = 0.0
        self.step_count = 0
        self.session_id = None
        self.consecutive_wrong = 0  # Track bad behavior

    def reset(self, task_name: str = "easy") -> Observation:
        """Start a new episode"""
        self.current_task = task_name
        self.current_index = 0
        self.total_reward = 0.0
        self.step_count = 0
        self.session_id = str(uuid.uuid4())
        self.consecutive_wrong = 0

        if task_name == "easy":
            self.emails = easy_emails()
            instructions = "Label each email as 'spam' or 'not_spam'"
        elif task_name == "medium":
            self.emails = medium_emails()
            instructions = "Rate each email priority from 1 (low) to 5 (urgent)"
        else:
            self.emails = hard_emails()
            instructions = "Route to 'support', 'sales', or 'billing' and suggest a reply"

        return self._make_observation(instructions)

    def step(self, action: Action) -> StepResult:
        """Process one action with meaningful reward shaping"""
        self.step_count += 1
        email = self.emails[self.current_index]
        email_id = email["id"]

        # Grade the action
        if self.current_task == "easy":
            base_score = easy_grade(email_id, action.label, self.emails)
            reason = f"Label '{action.label}' was {'correct' if base_score == 1.0 else 'wrong'}"

        elif self.current_task == "medium":
            base_score = medium_grade(email_id, action.priority, self.emails)
            reason = f"Priority {action.priority} scored {base_score}"

        else:
            base_score = hard_grade(
                email_id,
                action.department,
                action.reply_suggestion or "",
                self.emails
            )
            reason = f"Department '{action.department}' routing scored {base_score}"

        # Reward shaping — partial progress signals
        shaped_score = self._shape_reward(base_score)

        self.total_reward += shaped_score
        self.current_index += 1
        done = self.current_index >= len(self.emails)

        # Bonus reward for completing all correctly
        if done:
            max_possible = len(self.emails)
            if self.total_reward >= max_possible * 0.9:
                shaped_score += 0.2  # Bonus for excellent performance
                reason += " | Excellent completion bonus!"
            elif self.total_reward >= max_possible * 0.6:
                shaped_score += 0.1  # Bonus for good performance
                reason += " | Good completion bonus!"

        if not done:
            instructions = self._get_instructions()
            next_obs = self._make_observation(instructions)
        else:
            next_obs = None

        reward = Reward(
            score=round(min(shaped_score, 1.0), 2),
            reason=reason,
            done=done
        )

        return StepResult(
            observation=next_obs,
            reward=reward,
            done=done,
            info={
                "session_id": self.session_id,
                "step": self.step_count,
                "total_reward": round(self.total_reward, 2),
                "emails_remaining": len(self.emails) - self.current_index,
                "consecutive_wrong": self.consecutive_wrong,
                "progress": round(self.current_index / len(self.emails), 2)
            }
        )

    def _shape_reward(self, base_score: float) -> float:
        """
        Shape reward to provide meaningful signal:
        - Reward correct actions fully
        - Penalize consecutive wrong answers
        - Provide partial credit where possible
        """
        if base_score == 0.0:
            self.consecutive_wrong += 1
            # Penalize repeated mistakes
            penalty = min(0.1 * self.consecutive_wrong, 0.3)
            return max(0.0, base_score - penalty)
        else:
            # Reset penalty counter on correct answer
            self.consecutive_wrong = 0
            return base_score

    def state(self) -> dict:
        """Return current state"""
        return {
            "session_id": self.session_id,
            "task": self.current_task,
            "step": self.step_count,
            "current_email_index": self.current_index,
            "total_emails": len(self.emails),
            "total_reward": round(self.total_reward, 2),
            "consecutive_wrong": self.consecutive_wrong,
            "progress": round(
                self.current_index / len(self.emails), 2
            ) if self.emails else 0.0
        }

    def _make_observation(self, instructions: str) -> Observation:
        email_data = self.emails[self.current_index]
        return Observation(
            email=Email(
                id=email_data["id"],
                subject=email_data["subject"],
                body=email_data["body"],
                sender=email_data["sender"],
                timestamp=email_data["timestamp"]
            ),
            task_name=self.current_task,
            step_number=self.step_count,
            max_steps=len(self.emails),
            instructions=instructions
        )

    def _get_instructions(self) -> str:
        if self.current_task == "easy":
            return "Label each email as 'spam' or 'not_spam'"
        elif self.current_task == "medium":
            return "Rate each email priority from 1 (low) to 5 (urgent)"
        return "Route to 'support', 'sales', or 'billing' and suggest a reply"