from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from env.environment import JobApplyEnv
from env.models import JobApplyAction, StepResult, ResetResult, StateResult
from pydantic import BaseModel
from typing import Optional
import uvicorn
from datetime import datetime

app = FastAPI(
    title="JobApply-Env",
    description=(
        "An OpenEnv reinforcement learning environment simulating the Indian "
        "job application process. Supports 4 tasks: Resume Bullet Rewriting, "
        "HR Screening Q&A, Salary Negotiation, and LinkedIn Bio Writing."
    ),
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─────────────────────────────────────────
# STATE
# ─────────────────────────────────────────
env = JobApplyEnv()

# In-memory leaderboard and episode history
leaderboard: dict[str, dict] = {}   # agent_id -> best scores per task
episode_log: list[dict] = []        # all completed episodes


# ─────────────────────────────────────────
# REQUEST MODELS
# ─────────────────────────────────────────
class ResetRequest(BaseModel):
    task_id: Optional[str] = None
    agent_id: Optional[str] = "anonymous"


class StepRequest(BaseModel):
    response: str
    agent_id: Optional[str] = "anonymous"


# ─────────────────────────────────────────
# ROUTES
# ─────────────────────────────────────────
@app.get("/")
def root():
    return {
        "name": "JobApply-Env",
        "version": "2.0.0",
        "tasks": [
            {"id": "resume_bullet",       "difficulty": "easy",   "max_steps": 3},
            {"id": "hr_screening",        "difficulty": "medium", "max_steps": 3},
            {"id": "salary_negotiation",  "difficulty": "hard",   "max_steps": 5},
            {"id": "linkedin_bio",        "difficulty": "medium", "max_steps": 3},
        ],
        "endpoints": ["/reset", "/step", "/state", "/health", "/leaderboard", "/history"],
        "status": "ready"
    }


@app.post("/reset", response_model=ResetResult)
def reset(request: ResetRequest):
    try:
        result = env.reset(task_id=request.task_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/step", response_model=StepResult)
def step(request: StepRequest):
    try:
        action = JobApplyAction(response=request.response)
        result = env.step(action)

        # Log completed episodes to leaderboard
        if result.done:
            agent_id = request.agent_id or "anonymous"
            task_id = env.task_id
            score = result.reward.score

            # Update leaderboard
            if agent_id not in leaderboard:
                leaderboard[agent_id] = {}
            prev_best = leaderboard[agent_id].get(task_id, 0.0)
            if score > prev_best:
                leaderboard[agent_id][task_id] = score

            # Log episode
            episode_log.append({
                "episode_id": env.episode_id,
                "agent_id": agent_id,
                "task_id": task_id,
                "final_score": score,
                "steps_taken": env.step_number,
                "timestamp": datetime.utcnow().isoformat()
            })

        return result
    except RuntimeError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/state", response_model=StateResult)
def state():
    try:
        return env.state()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
def health():
    return {"status": "ok", "version": "2.0.0"}


@app.get("/leaderboard")
def get_leaderboard():
    """Returns best scores per agent per task. Live updated."""
    ranked = []
    for agent_id, scores in leaderboard.items():
        avg = round(sum(scores.values()) / len(scores), 2) if scores else 0.0
        ranked.append({
            "agent_id": agent_id,
            "scores": scores,
            "average": avg,
            "tasks_completed": len(scores)
        })
    ranked.sort(key=lambda x: x["average"], reverse=True)
    return {
        "leaderboard": ranked,
        "total_episodes": len(episode_log),
        "total_agents": len(leaderboard)
    }


@app.get("/history")
def get_history(limit: int = 20):
    """Returns recent episode history."""
    return {
        "episodes": episode_log[-limit:],
        "total": len(episode_log)
    }


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=7860, reload=True)