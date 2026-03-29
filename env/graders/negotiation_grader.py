import re
from env.models import JobApplyReward
from env.graders.llm_grader import llm_grade_negotiation

MARKET_DATA_PHRASES = [
    "market rate", "industry standard", "glassdoor", "linkedin salary",
    "ambitionbox", "average salary", "research", "data shows",
    "comparable role", "similar companies", "industry average"
]

UNPROFESSIONAL_PHRASES = [
    "that's ridiculous", "this is unfair", "i deserve more",
    "take it or leave it", "final answer", "you're wrong",
    "that's insulting", "other companies pay", "i'll leave"
]

def extract_salary_from_text(text: str) -> float:
    """Extract highest LPA number mentioned in text."""
    matches = re.findall(r'(\d+(?:\.\d+)?)\s*(?:lpa|l\.p\.a|lakhs?|lac)', text.lower())
    if matches:
        return max(float(m) for m in matches)
    return 0.0

def grade_negotiation_turn(
    agent_response: str,
    turn_number: int,
    max_turns: int,
    initial_offer: float,
    target_lpa: float,
    best_score_so_far: float,
    is_final_turn: bool
) -> JobApplyReward:
    score = 0.0
    breakdown = {}
    feedback_parts = []
    response_lower = agent_response.lower()

    # Criterion 1: Salary outcome — only meaningful on final turn (0.50)
    mentioned_salary = extract_salary_from_text(agent_response)
    if is_final_turn:
        if mentioned_salary >= target_lpa:
            salary_score = 0.50
        elif mentioned_salary >= target_lpa - 1:
            salary_score = 0.40
        elif mentioned_salary >= initial_offer + 1.5:
            salary_score = 0.25
        elif mentioned_salary > initial_offer:
            salary_score = 0.10
        else:
            salary_score = 0.0
            feedback_parts.append(f"Push for a higher number. Target is ₹{target_lpa} LPA.")
        breakdown["salary_outcome"] = salary_score
        score += salary_score
    else:
        # Partial signal on non-final turns — reward counter-offering
        if mentioned_salary > initial_offer:
            breakdown["salary_outcome"] = 0.15
            score += 0.15
        else:
            breakdown["salary_outcome"] = 0.0
            feedback_parts.append("Make a concrete counter-offer with a specific number.")

    # Criterion 2: Used market data or justification (0.25)
    has_market_data = any(phrase in response_lower for phrase in MARKET_DATA_PHRASES)
    if has_market_data:
        breakdown["market_data"] = 0.25
        score += 0.25
    else:
        breakdown["market_data"] = 0.0
        feedback_parts.append("Back your ask with market data (e.g. 'Industry average for this role is ₹X LPA')")

    # Criterion 3: Professional tone (0.25)
    is_unprofessional = any(phrase in response_lower for phrase in UNPROFESSIONAL_PHRASES)
    if not is_unprofessional:
        breakdown["professional_tone"] = 0.25
        score += 0.25
    else:
        breakdown["professional_tone"] = 0.0
        feedback_parts.append("Maintain a professional and collaborative tone.")

    score = round(score, 2)
    is_best = score > best_score_so_far

    feedback = (
        "Strong negotiation move! " + " | ".join(feedback_parts)
        if score >= 0.60
        else "Needs improvement: " + " | ".join(feedback_parts)
        if feedback_parts
        else "Perfect negotiation response!"
    )
    llm_result = llm_grade_negotiation(
        agent_response, initial_offer, target_lpa, is_final_turn
    )
    if llm_result and isinstance(llm_result.get("total"), (int, float)):
        score = round(min(float(llm_result["total"]), 1.0), 2)
        breakdown = {
            "salary_outcome": llm_result.get("salary_outcome", 0),
            "market_data": llm_result.get("market_data", 0),
            "professional_tone": llm_result.get("professional_tone", 0),
            "grader": "llm"
        }
        feedback = llm_result.get("feedback", feedback)
        is_best = score > best_score_so_far
        return JobApplyReward(
            score=score,
            breakdown=breakdown,
            feedback=feedback,
            is_best_so_far=is_best
        )
    return JobApplyReward(
        score=score,
        breakdown=breakdown,
        feedback=feedback,
        is_best_so_far=is_best
    )