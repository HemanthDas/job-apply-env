from pydantic import BaseModel
from typing import Optional


# ─────────────────────────────────────────
# OBSERVATION — what the agent sees
# ─────────────────────────────────────────
class JobApplyObservation(BaseModel):
    task_id: str                        # "resume_bullet" | "hr_screening" | "salary_negotiation"
    scenario: str                       # the actual problem given to the agent
    step_number: int                    # which turn we're on (starts at 1)
    feedback: str                       # what was wrong last time (empty on first step)
    max_steps: int                      # how many attempts allowed


# ─────────────────────────────────────────
# ACTION — what the agent sends back
# ─────────────────────────────────────────
class JobApplyAction(BaseModel):
    response: str                       # agent's text output


# ─────────────────────────────────────────
# REWARD — returned after each step
# ─────────────────────────────────────────
class JobApplyReward(BaseModel):
    score: float                        # 0.0 to 1.0
    breakdown: dict                     # per-criterion scores
    feedback: str                       # human-readable explanation
    is_best_so_far: bool                # did this beat previous best?


# ─────────────────────────────────────────
# STEP RESULT — full response from step()
# ─────────────────────────────────────────
class StepResult(BaseModel):
    observation: JobApplyObservation
    reward: JobApplyReward
    done: bool                          # is episode over?
    info: dict                          # extra metadata


# ─────────────────────────────────────────
# RESET RESULT — response from reset()
# ─────────────────────────────────────────
class ResetResult(BaseModel):
    observation: JobApplyObservation


# ─────────────────────────────────────────
# STATE RESULT — response from state()
# ─────────────────────────────────────────
class StateResult(BaseModel):
    task_id: str
    step_number: int
    max_steps: int
    best_score: float
    done: bool
    episode_id: str                     # unique ID per episode