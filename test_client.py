from client import JobApplyEnvClient
from env.models import JobApplyAction

with JobApplyEnvClient("http://localhost:7860") as client:
    # Test health
    health = client.health()
    print(f"Health: {health}")

    # Test reset
    result = client.reset(task_id="resume_bullet")
    print(f"Reset OK: {result.observation.task_id}")

    # Test step
    step = client.step(JobApplyAction(
        response="Developed 15 RESTful APIs reducing latency by 40% for 10K users"
    ))
    print(f"Step OK: score={step.reward.score} done={step.done}")

    # Test state
    state = client.state()
    print(f"State OK: {state.task_id} step={state.step_number}")

    print("Client OK ✅")