import re
from env.models import JobApplyReward

STRONG_ACTION_VERBS = [
    "developed", "built", "designed", "implemented", "optimized",
    "automated", "reduced", "increased", "improved", "delivered",
    "architected", "migrated", "refactored", "deployed", "integrated",
    "created", "launched", "established", "streamlined", "engineered"
]

IMPACT_WORDS = [
    "revenue", "efficiency", "performance", "users", "time", "cost",
    "latency", "throughput", "accuracy", "coverage", "reliability",
    "scalability", "downtime", "errors", "bugs", "requests", "traffic"
]

def grade_resume_bullet(original: str, rewritten: str, best_score_so_far: float) -> JobApplyReward:
    score = 0.0
    breakdown = {}
    feedback_parts = []

    # Criterion 1: Starts with a strong action verb (0.25)
    first_word = rewritten.strip().split()[0].lower().rstrip(".,") if rewritten.strip() else ""
    if first_word in STRONG_ACTION_VERBS:
        breakdown["action_verb"] = 0.25
        score += 0.25
    else:
        breakdown["action_verb"] = 0.0
        feedback_parts.append(f"Start with a strong action verb like 'Developed' or 'Optimized' (got '{first_word}')")

    # Criterion 2: Contains a number or metric (0.35)
    has_metric = bool(re.search(r'\d+\s*(%|x|X|ms|s|hrs?|days?|LPA|K|M|GB|TB)?', rewritten))
    if has_metric:
        breakdown["has_metric"] = 0.35
        score += 0.35
    else:
        breakdown["has_metric"] = 0.0
        feedback_parts.append("Include a specific number or metric (e.g. '40%', '3x', '200ms')")

    # Criterion 3: Mentions business impact (0.25)
    has_impact = any(word in rewritten.lower() for word in IMPACT_WORDS)
    if has_impact:
        breakdown["business_impact"] = 0.25
        score += 0.25
    else:
        breakdown["business_impact"] = 0.0
        feedback_parts.append("Mention business impact (e.g. 'reduced latency', 'improved efficiency')")

    # Criterion 4: Concise — under 25 words (0.15)
    word_count = len(rewritten.strip().split())
    if word_count <= 25:
        breakdown["conciseness"] = 0.15
        score += 0.15
    else:
        breakdown["conciseness"] = 0.0
        feedback_parts.append(f"Too long ({word_count} words). Keep it under 25 words.")

    score = round(score, 2)
    is_best = score > best_score_so_far

    feedback = (
        "Great bullet! " + " ".join(feedback_parts)
        if score >= 0.75
        else "Needs improvement: " + " | ".join(feedback_parts)
        if feedback_parts
        else "Perfect resume bullet!"
    )

    return JobApplyReward(
        score=score,
        breakdown=breakdown,
        feedback=feedback,
        is_best_so_far=is_best
    )