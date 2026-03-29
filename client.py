import httpx
from env.models import (
    JobApplyObservation,
    JobApplyAction,
    JobApplyReward,
    StepResult,
    ResetResult,
    StateResult,
)


class JobApplyEnvClient:
    """
    HTTP client for interacting with the JobApply-Env server.
    Compatible with OpenEnv multi-mode deployment spec.
    """

    def __init__(self, base_url: str = "http://localhost:7860"):
        self.base_url = base_url.rstrip("/")
        self.client = httpx.Client(timeout=30.0)

    def reset(self, task_id: str = None, agent_id: str = "anonymous") -> ResetResult:
        payload = {}
        if task_id:
            payload["task_id"] = task_id
        if agent_id:
            payload["agent_id"] = agent_id
        response = self.client.post(f"{self.base_url}/reset", json=payload)
        response.raise_for_status()
        return ResetResult(**response.json())

    def step(self, action: JobApplyAction, agent_id: str = "anonymous") -> StepResult:
        payload = {
            "response": action.response,
            "agent_id": agent_id
        }
        response = self.client.post(f"{self.base_url}/step", json=payload)
        response.raise_for_status()
        return StepResult(**response.json())

    def state(self) -> StateResult:
        response = self.client.get(f"{self.base_url}/state")
        response.raise_for_status()
        return StateResult(**response.json())

    def health(self) -> dict:
        response = self.client.get(f"{self.base_url}/health")
        response.raise_for_status()
        return response.json()

    def close(self):
        self.client.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()