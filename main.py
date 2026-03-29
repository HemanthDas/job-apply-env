import gradio as gr
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from env.environment import JobApplyEnv
from env.models import JobApplyAction, StepResult, ResetResult, StateResult
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
import uvicorn

# ─────────────────────────────────────────
# FASTAPI APP
# ─────────────────────────────────────────
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

env = JobApplyEnv()
leaderboard: dict[str, dict] = {}
episode_log: list[dict] = []


class ResetRequest(BaseModel):
    task_id: Optional[str] = None
    agent_id: Optional[str] = "anonymous"
    
    model_config = {"extra": "allow"}


class StepRequest(BaseModel):
    response: str
    agent_id: Optional[str] = "anonymous"


@app.get("/")
def root():
    return {
        "name": "JobApply-Env",
        "version": "2.0.0",
        "tasks": [
            {"id": "resume_bullet",      "difficulty": "easy",   "max_steps": 3},
            {"id": "hr_screening",       "difficulty": "medium", "max_steps": 3},
            {"id": "salary_negotiation", "difficulty": "hard",   "max_steps": 5},
            {"id": "linkedin_bio",       "difficulty": "medium", "max_steps": 3},
        ],
        "endpoints": ["/reset", "/step", "/state", "/health", "/leaderboard", "/history"],
        "status": "ready"
    }


@app.post("/reset", response_model=ResetResult)
async def reset(request: Request):
    try:
        # Handle empty body, null body, or proper JSON
        try:
            body = await request.json()
        except Exception:
            body = {}
        
        task_id = body.get("task_id", None) if body else None
        result = env.reset(task_id=task_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/step", response_model=StepResult)
def step(request: StepRequest):
    try:
        action = JobApplyAction(response=request.response)
        result = env.step(action)
        if result.done:
            agent_id = request.agent_id or "anonymous"
            task_id = env.task_id
            score = result.reward.score
            if agent_id not in leaderboard:
                leaderboard[agent_id] = {}
            if score > leaderboard[agent_id].get(task_id, 0.0):
                leaderboard[agent_id][task_id] = score
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
    return {
        "episodes": episode_log[-limit:],
        "total": len(episode_log)
    }


# ─────────────────────────────────────────
# GRADIO UI
# ─────────────────────────────────────────
def gradio_step(task_id: str, agent_response: str):
    """Single function that handles reset + step for Gradio UI."""
    try:
        if not agent_response.strip():
            result = env.reset(task_id=task_id)
            obs = result.observation
            return (
                obs.scenario,
                "0.0",
                "Start your response above and click Submit.",
                f"Step: {obs.step_number} | Task: {obs.task_id}"
            )

        action = JobApplyAction(response=agent_response)
        result = env.step(action)
        obs = result.observation
        reward = result.reward

        status = "✅ Episode Complete!" if result.done else f"Step: {obs.step_number}/{obs.max_steps}"

        return (
            obs.scenario,
            str(reward.score),
            reward.feedback,
            status
        )
    except RuntimeError:
        result = env.reset(task_id=task_id)
        obs = result.observation
        return (
            obs.scenario,
            "0.0",
            "New episode started.",
            f"Step: {obs.step_number} | Task: {obs.task_id}"
        )
    except Exception as e:
        return ("Error: " + str(e), "0.0", "", "Error")


def gradio_reset(task_id: str):
    result = env.reset(task_id=task_id)
    obs = result.observation
    return (
        obs.scenario,
        "0.0",
        "Episode reset. Enter your response below.",
        f"Step: {obs.step_number} | Task: {obs.task_id} | Max Steps: {obs.max_steps}"
    )


with gr.Blocks(
    title="JobApply-Env",
    theme=gr.themes.Soft(),
    css=".gradio-container {max-width: 900px !important}"
) as demo:
    gr.Markdown("""
    # 🎯 JobApply-Env
    ### OpenEnv Reinforcement Learning Environment — Indian Job Application Process
    
    An AI agent learns to navigate 4 real-world hiring tasks with increasing difficulty.
    Uses **LLM-powered graders** (Llama 3.1) for semantic evaluation.
    
    **API Endpoints:** `/reset` · `/step` · `/state` · `/health` · `/leaderboard` · `/history`
    """)

    with gr.Row():
        task_dropdown = gr.Dropdown(
            choices=["resume_bullet", "hr_screening", "salary_negotiation", "linkedin_bio"],
            value="resume_bullet",
            label="Select Task",
        )
        reset_btn = gr.Button("🔄 Reset Episode", variant="secondary")

    with gr.Row():
        scenario_box = gr.Textbox(
            label="📋 Scenario (what the agent sees)",
            lines=6,
            interactive=False,
            value="Select a task and click Reset to start."
        )

    with gr.Row():
        response_box = gr.Textbox(
            label="✍️ Agent Response",
            lines=4,
            placeholder="Type your response here..."
        )

    submit_btn = gr.Button("▶️ Submit Response", variant="primary")

    with gr.Row():
        score_box = gr.Textbox(label="🏆 Score (0.0 - 1.0)", interactive=False)
        status_box = gr.Textbox(label="📊 Status", interactive=False)

    feedback_box = gr.Textbox(
        label="💡 Grader Feedback",
        lines=2,
        interactive=False
    )

    gr.Markdown("""
    ---
    **Tasks:** `resume_bullet` (Easy) · `hr_screening` (Medium) · `salary_negotiation` (Hard) · `linkedin_bio` (Medium)
    
    **Graders:** LLM-powered (Llama 3.1 8B) with rule-based fallback · **16 tests passing** · Deterministic & reproducible
    """)

    reset_btn.click(
        gradio_reset,
        inputs=[task_dropdown],
        outputs=[scenario_box, score_box, feedback_box, status_box]
    )

    submit_btn.click(
        gradio_step,
        inputs=[task_dropdown, response_box],
        outputs=[scenario_box, score_box, feedback_box, status_box]
    )

# ─────────────────────────────────────────
# MOUNT GRADIO ON FASTAPI
# ─────────────────────────────────────────
app = gr.mount_gradio_app(app, demo, path="/ui")

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=7860, reload=False)