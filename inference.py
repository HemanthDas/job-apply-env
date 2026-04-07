import os
import httpx
from dotenv import load_dotenv

load_dotenv()

# Use live HF Space URL or localhost
BASE_URL = os.environ.get("OPENENV_BASE_URL", "https://hemanthdas-job-apply-env.hf.space")

TASK_IDS = ["resume_bullet", "hr_screening", "salary_negotiation", "linkedin_bio"]

SAMPLE_RESPONSES = {
    "resume_bullet": (
        "Developed 15 RESTful APIs reducing response latency by 40% "
        "for 10K daily users using Java and Spring Boot."
    ),
    "hr_screening": (
        "I am a software engineer with 2 years of experience in Java and Spring Boot. "
        "I have built REST APIs for fintech clients processing 10K daily transactions. "
        "I enjoy solving complex backend problems and am excited to bring this expertise "
        "to a product-focused company like yours. That is why I am here today."
    ),
    "salary_negotiation": (
        "Thank you for the offer. Based on market research from AmbitionBox, "
        "the average salary for this role is significantly higher. "
        "Given my 2 years of experience in Java and distributed systems, "
        "I would like to propose a salary of 9.5 LPA. "
        "I am confident I can bring immediate value to the team."
    ),
    "linkedin_bio": (
        "Passionate about building scalable backend systems that handle millions of requests. "
        "Software Engineer with 2 years at a fintech startup, specializing in Java, "
        "Spring Boot and REST APIs. Reduced API latency by 40% across 10K daily users. "
        "Feel free to reach out if you are looking for a backend engineer who ships fast."
    ),
}

def run_task(client: httpx.Client, task_id: str) -> float:
    print(f"[START] task={task_id}", flush=True)

    try:
        reset_resp = client.post(f"{BASE_URL}/reset", json={"task_id": task_id})
        reset_resp.raise_for_status()
        result = reset_resp.json()

        final_score = 0.0
        done = False
        step_num = 0

        while not done and step_num < 10:
            response_text = SAMPLE_RESPONSES.get(task_id, "I am responding to this task professionally.")

            step_resp = client.post(
                f"{BASE_URL}/step",
                json={"response": response_text, "agent_id": "baseline"}
            )
            step_resp.raise_for_status()
            step_result = step_resp.json()

            score = step_result["reward"]["score"]
            done = step_result["done"]
            final_score = score
            step_num += 1

            print(f"[STEP] step={step_num} reward={score}", flush=True)

    except Exception as e:
        print(f"[END] task={task_id} score=0.0 steps=0", flush=True)
        return 0.0

    print(f"[END] task={task_id} score={final_score} steps={step_num}", flush=True)
    return final_score


def main():
    print("🚀 JobApply-Env Inference Script")
    print(f"Connecting to: {BASE_URL}")
    print("==========================================")

    scores = {}

    with httpx.Client(timeout=60.0) as client:
        # Health check first
        try:
            health = client.get(f"{BASE_URL}/health")
            health.raise_for_status()
            print(f"Health check: {health.json()}")
        except Exception as e:
            print(f"❌ Health check failed: {e}")
            return

        for task_id in TASK_IDS:
            scores[task_id] = run_task(client, task_id)

    print(f"\n{'='*50}")
    print("📊 BASELINE RESULTS")
    print(f"{'='*50}")
    for task_id, score in scores.items():
        bar = "█" * int(score * 20) + "░" * (20 - int(score * 20))
        print(f"{task_id:<25} [{bar}] {score:.2f}")
    print(f"\nOverall Average: {sum(scores.values()) / len(scores):.2f}")
    print(f"{'='*50}")


if __name__ == "__main__":
    main()