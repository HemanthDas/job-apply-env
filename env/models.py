from pydantic import BaseModel
from typing import Optional


# ─────────────────────────────────────────
# OBSERVATION — what the agent sees
# ─────────────────────────────────────────
class JobApplyObservation(BaseModel):
    task_id: str
    scenario: str
    step_number: int
    feedback: str
    max_steps: int
    conversation_history: list[dict] = []  # NEW — full turn history
    context_summary: str = ""              # NEW — running summary of episode so far


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