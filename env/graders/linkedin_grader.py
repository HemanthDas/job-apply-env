import re
from env.models import JobApplyReward
from env.graders.llm_grader import get_client, _parse_json_response

HOOK_WORDS = [
    "passionate", "building", "engineer", "helping", "solving",
    "creating", "scaling", "shipping", "driving", "transforming"
]

WEAK_PHRASES = [
    "open to work", "looking for opportunities", "i like coding",
    "i do both", "i work with", "i manage", "i build websites",
    "looking for jobs", "i am a"
]


def llm_grade_linkedin(weak_bio: str, rewritten_bio: str, role: str, goal: str) -> dict | None:
    client = get_client()
    if not client:
        return None

    prompt = f"""You are an expert LinkedIn profile coach grading a rewritten LinkedIn bio/summary.

ROLE: {role}
GOAL: {goal}

ORIGINAL WEAK BIO:
"{weak_bio}"

REWRITTEN BIO:
"{rewritten_bio}"

Grade the rewritten bio on these 4 criteria. Return ONLY a JSON object:

{{
  "hook": <0.0 to 0.25, does it open with a compelling hook that grabs attention in the first line?>,
  "value_proposition": <0.0 to 0.35, does it clearly state what the person does and the value they bring?>,
  "keywords": <0.0 to 0.25, does it include relevant technical skills and industry keywords naturally?>,
  "call_to_action": <0.0 to 0.15, does it end with a clear call to action or invitation to connect?>,
  "feedback": "<one sentence of constructive feedback>",
  "total": <sum of all 4 scores rounded to 2 decimal places>
}}"""

    try:
        client_obj = get_client()
        from groq import Groq
        response = client_obj.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=300,
            temperature=0.1
        )
        return _parse_json_response(response.choices[0].message.content)
    except Exception:
        return None


def grade_linkedin_bio(
    weak_bio: str,
    rewritten_bio: str,
    role: str,
    goal: str,
    best_score_so_far: float
) -> JobApplyReward:
    # Penalty for garbage/very short responses
    if len(rewritten_bio.strip().split()) < 10:
        return JobApplyReward(
            score=0.0,
            breakdown={"penalty": "response too short"},
            feedback="Bio is too short. Write 3-5 compelling sentences.",
            is_best_so_far=False
        )
    score = 0.0
    breakdown = {}
    feedback_parts = []
    bio_lower = rewritten_bio.lower()

    # Criterion 1: Strong opening hook (0.25)
    first_sentence = rewritten_bio.split(".")[0].lower()
    has_hook = any(w in first_sentence for w in HOOK_WORDS)
    if has_hook:
        breakdown["hook"] = 0.25
        score += 0.25
    else:
        breakdown["hook"] = 0.0
        feedback_parts.append("Open with a strong hook (e.g. 'Passionate about building...')")

    # Criterion 2: Clear value proposition (0.35)
    has_value = any(w in bio_lower for w in ["engineer", "developer", "build", "scale", "deliver", "specialize"])
    has_impact = bool(re.search(r'\d+', rewritten_bio))
    value_score = 0.20 if has_value else 0.0
    value_score += 0.15 if has_impact else 0.0
    breakdown["value_proposition"] = round(value_score, 2)
    score += value_score
    if value_score < 0.20:
        feedback_parts.append("State clearly what you do and include at least one metric.")

    # Criterion 3: Technical keywords (0.25)
    has_keywords = len([w for w in bio_lower.split() if len(w) > 4]) > 10
    no_weak = not any(p in bio_lower for p in WEAK_PHRASES)
    keyword_score = 0.15 if has_keywords else 0.0
    keyword_score += 0.10 if no_weak else 0.0
    breakdown["keywords"] = round(keyword_score, 2)
    score += keyword_score
    if not no_weak:
        feedback_parts.append("Remove weak phrases like 'open to work' or 'I like coding'.")

    # Criterion 4: Call to action (0.15)
    cta_phrases = ["reach out", "connect with me", "let's connect", "feel free", "dm me", "contact me", "open to", "happy to chat"]
    has_cta = any(p in bio_lower for p in cta_phrases)
    if has_cta:
        breakdown["call_to_action"] = 0.15
        score += 0.15
    else:
        breakdown["call_to_action"] = 0.0
        feedback_parts.append("End with a call to action (e.g. 'Feel free to reach out!')")

    score = round(score, 2)

    # LLM override
    llm_result = llm_grade_linkedin(weak_bio, rewritten_bio, role, goal)
    if llm_result and isinstance(llm_result.get("total"), (int, float)):
        score = round(min(float(llm_result["total"]), 1.0), 2)
        breakdown = {
            "hook": llm_result.get("hook", 0),
            "value_proposition": llm_result.get("value_proposition", 0),
            "keywords": llm_result.get("keywords", 0),
            "call_to_action": llm_result.get("call_to_action", 0),
            "grader": "llm"
        }
        feedback_parts = [llm_result.get("feedback", "")]

    is_best = score > best_score_so_far
    feedback = " | ".join(feedback_parts) if feedback_parts else "Excellent LinkedIn bio!"

    return JobApplyReward(
        score=score,
        breakdown=breakdown,
        feedback=feedback,
        is_best_so_far=is_best
    )