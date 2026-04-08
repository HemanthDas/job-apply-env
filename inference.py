import os
import httpx
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

# Use their injected proxy — fallback to direct OpenAI
API_BASE_URL = os.environ.get("API_BASE_URL", "https://api.openai.com/v1")
API_KEY = os.environ.get("API_KEY", os.environ.get("OPENAI_API_KEY", ""))
BASE_URL = os.environ.get("OPENENV_BASE_URL", "https://hemanthdas-job-apply-env.hf.space")

TASK_IDS = ["resume_bullet", "hr_screening", "salary_negotiation", "linkedin_bio"]

SYSTEM_PROMPT = """You are an expert job applicant helping a fresher navigate
the Indian job market. You write strong resume bullets, answer HR questions
clearly and concisely, and negotiate salary professionally using market data.
Always be specific, structured, and professional."""


def get_llm_response(client: OpenAI, messages: list) -> str:
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            max_tokens=300,
            temperature=0.7
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"LLM error: {e}", flush=True)
        return "I am responding professionally to this task with relevant experience and skills."


def run_task(http_client: httpx.Client, llm_client: OpenAI, task_id: str) -> float:
    print(f"[START] task={task_id}", flush=True)

    try:
        # Reset
        reset_resp = http_client.post(f"{BASE_URL}/reset", json={"task_id": task_id})
        reset_resp.raise_for_status()
        result = reset_resp.json()

        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        final_score = 0.0
        done = False
        step_num = 0

        while not done and step_num < 10:
            obs = result.get("observation", result)
            scenario = obs.get("scenario", "")
            feedback = obs.get("feedback", "")

            user_content = scenario
            if feedback:
                user_content += f"\n\n💡 Previous feedback: {feedback}"

            messages.append({"role": "user", "content": user_content})

            # Use their LLM proxy
            agent_response = get_llm_response(llm_client, messages)
            messages.append({"role": "assistant", "content": agent_response})

            # Step environment
            step_resp = http_client.post(
                f"{BASE_URL}/step",
                json={"response": agent_response, "agent_id": "baseline"}
            )
            step_resp.raise_for_status()
            step_result = step_resp.json()

            score = step_result["reward"]["score"]
            done = step_result["done"]
            final_score = score
            step_num += 1
            result = step_result

            print(f"[STEP] step={step_num} reward={score}", flush=True)

    except Exception as e:
        print(f"Error in task {task_id}: {e}", flush=True)
        print(f"[END] task={task_id} score=0.0 steps=0", flush=True)
        return 0.0

    print(f"[END] task={task_id} score={final_score} steps={step_num}", flush=True)
    return final_score


def main():
    print("🚀 JobApply-Env Inference Script", flush=True)
    print(f"API Base URL: {API_BASE_URL}", flush=True)
    print(f"Environment URL: {BASE_URL}", flush=True)
    print("==========================================", flush=True)

    # Initialize OpenAI client with their proxy
    llm_client = OpenAI(
        api_key=API_KEY,
        base_url=API_BASE_URL
    )

    scores = {}

    with httpx.Client(timeout=60.0) as http_client:
        # Health check
        try:
            health = http_client.get(f"{BASE_URL}/health")
            health.raise_for_status()
            print(f"Health check: {health.json()}", flush=True)
        except Exception as e:
            print(f"❌ Health check failed: {e}", flush=True)
            return

        for task_id in TASK_IDS:
            scores[task_id] = run_task(http_client, llm_client, task_id)

    print(f"\n{'='*50}", flush=True)
    print("📊 BASELINE RESULTS", flush=True)
    print(f"{'='*50}", flush=True)
    for task_id, score in scores.items():
        bar = "█" * int(score * 20) + "░" * (20 - int(score * 20))
        print(f"{task_id:<25} [{bar}] {score:.2f}", flush=True)
    print(f"\nOverall Average: {sum(scores.values()) / len(scores):.2f}", flush=True)
    print(f"{'='*50}", flush=True)


if __name__ == "__main__":
    main()