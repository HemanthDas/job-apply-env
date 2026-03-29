from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from env.environment import JobApplyEnv
from env.models import JobApplyAction, StepResult, ResetResult, StateResult
from pydantic import BaseModel
from typing import Optional
import uvicorn

app = FastAPI(
    title="JobApply-Env",
    description="An OpenEnv environment for Indian job application coaching",
    version="0.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# One env instance per server (stateful)
env = JobApplyEnv()


# ─────────────────────────────────────────
# REQUEST MODELS
# ─────────────────────────────────────────
class ResetRequest(BaseModel):
    task_id: Optional[str] = None


class StepRequest(BaseModel):
    response: str


# ─────────────────────────────────────────
# ROUTES
# ─────────────────────────────────────────
@app.get("/")
def root():
    return {
        "name": "JobApply-Env",
        "version": "0.1.0",
        "tasks": ["resume_bullet", "hr_screening", "salary_negotiation"],
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
    return {"status": "ok"}


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=7860, reload=True)