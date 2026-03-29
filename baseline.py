import os
from groq import Groq
from dotenv import load_dotenv
from env.environment import JobApplyEnv
from env.models import JobApplyAction

load_dotenv()

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

SYSTEM_PROMPT = """You are an expert job applicant helping a fresher navigate
the Indian job market. You write strong resume bullets, answer HR questions
clearly and concisely, and negotiate salary professionally using market data.
Always be specific, structured, and professional."""


def run_task(env: JobApplyEnv, task_id: str) -> float:
    print(f"\n{'='*50}")
    print(f"TASK: {task_id.upper()}")
    print(f"{'='*50}")

    result = env.reset(task_id=task_id)
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    final_score = 0.0
    done = False

    while not done:
        obs = result.observation if hasattr(result, "observation") else result
        scenario = obs.scenario
        feedback = obs.feedback

        user_content = scenario
        if feedback:
            user_content += f"\n\n💡 Previous feedback: {feedback}"

        print(f"\n[Step {obs.step_number}]")
        print(f"Scenario: {scenario[:120]}...")

        messages.append({"role": "user", "content": user_content})

        # Call Groq (Llama 3 — free)
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=messages,
            max_tokens=300,
            temperature=0.7
        )

        agent_response = response.choices[0].message.content.strip()
        messages.append({"role": "assistant", "content": agent_response})

        print(f"Agent: {agent_response[:120]}...")

        # Step environment
        step_result = env.step(JobApplyAction(response=agent_response))

        print(f"Score: {step_result.reward.score} | Feedback: {step_result.reward.feedback[:80]}...")

        final_score = step_result.reward.score
        done = step_result.done
        result = step_result

    print(f"\n✅ Final Score for {task_id}: {final_score}")
    return final_score


def main():
    print("🚀 JobApply-Env Baseline Inference Script")
    print("Model: Llama 3 8B via Groq (Free)")
    print("==========================================")

    if not os.environ.get("GROQ_API_KEY"):
        print("❌ GROQ_API_KEY not set in .env file")
        print("Get a free key at: console.groq.com")
        return

    env = JobApplyEnv()
    scores = {}

    for task_id in ["resume_bullet", "hr_screening", "salary_negotiation", "linkedin_bio"]:
        try:
            scores[task_id] = run_task(env, task_id)
        except Exception as e:
            print(f"❌ Task {task_id} failed: {e}")
            scores[task_id] = 0.0

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