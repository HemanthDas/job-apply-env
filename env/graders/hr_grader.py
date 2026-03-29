import re
from env.models import JobApplyReward
from env.graders.llm_grader import llm_grade_hr
RED_FLAG_PHRASES = [
    "i don't know", "i have no weaknesses", "i work too hard",
    "my previous company was terrible", "i just want money",
    "i hate", "i don't care", "whatever", "i don't have any"
]

STRUCTURE_MARKERS = {
    "intro": ["i am", "i'm", "my name", "i have", "i've", "currently", "i work"],
    "body": ["because", "specifically", "for example", "such as", "in my experience", "i believe", "i feel"],
    "close": ["therefore", "that's why", "which is why", "i look forward", "i'm excited", "i hope", "in conclusion"]
}

def grade_hr_answer(question: str, answer: str, best_score_so_far: float) -> JobApplyReward:
    score = 0.0
    breakdown = {}
    feedback_parts = []
    answer_lower = answer.lower()

    # Criterion 1: Relevance to question (0.30)
    question_lower = question.lower()
    relevance_score = 0.0
    if "yourself" in question_lower and any(w in answer_lower for w in ["experience", "background", "skills", "work", "engineer", "developer"]):
        relevance_score = 0.30
    elif "weakness" in question_lower and any(w in answer_lower for w in ["working on", "improving", "learning", "sometimes", "tend to"]):
        relevance_score = 0.30
    elif "company" in question_lower and any(w in answer_lower for w in ["product", "mission", "growth", "team", "work", "opportunity"]):
        relevance_score = 0.30
    elif "5 years" in question_lower or "five years" in question_lower:
        if any(w in answer_lower for w in ["grow", "lead", "senior", "contribute", "skill", "role"]):
            relevance_score = 0.30
    elif "hire you" in question_lower and any(w in answer_lower for w in ["skill", "experience", "contribute", "value", "bring"]):
        relevance_score = 0.30
    else:
        relevance_score = 0.10  # partial credit for attempting
        feedback_parts.append("Answer feels off-topic — address the question more directly")

    breakdown["relevance"] = round(relevance_score, 2)
    score += relevance_score

    # Criterion 2: Structured response (0.30)
    has_intro = any(m in answer_lower for m in STRUCTURE_MARKERS["intro"])
    has_body = any(m in answer_lower for m in STRUCTURE_MARKERS["body"])
    has_close = any(m in answer_lower for m in STRUCTURE_MARKERS["close"])
    structure_score = round((has_intro * 0.10) + (has_body * 0.10) + (has_close * 0.10), 2)
    breakdown["structure"] = structure_score
    score += structure_score
    if structure_score < 0.20:
        feedback_parts.append("Structure your answer: intro → main point → closing thought")

    # Criterion 3: No red flag phrases (0.20)
    has_red_flag = any(phrase in answer_lower for phrase in RED_FLAG_PHRASES)
    if not has_red_flag:
        breakdown["no_red_flags"] = 0.20
        score += 0.20
    else:
        breakdown["no_red_flags"] = 0.0
        feedback_parts.append("Avoid negative or cliché phrases")

    # Criterion 4: Appropriate length — 60 to 150 words (0.20)
    word_count = len(answer.strip().split())
    if 60 <= word_count <= 150:
        breakdown["length"] = 0.20
        score += 0.20
    elif word_count < 60:
        breakdown["length"] = 0.05
        score += 0.05
        feedback_parts.append(f"Too short ({word_count} words). Aim for 60–150 words.")
    else:
        breakdown["length"] = 0.05
        score += 0.05
        feedback_parts.append(f"Too long ({word_count} words). Keep it under 150 words.")

    score = round(score, 2)
    is_best = score > best_score_so_far

    feedback = (
        "Strong answer! " + " | ".join(feedback_parts)
        if score >= 0.70
        else "Needs work: " + " | ".join(feedback_parts)
        if feedback_parts
        else "Excellent HR answer!"
    )
    
    llm_result = llm_grade_hr(question, answer)
    if llm_result and isinstance(llm_result.get("total"), (int, float)):
        score = round(min(float(llm_result["total"]), 1.0), 2)
        breakdown = {
            "relevance": llm_result.get("relevance", 0),
            "structure": llm_result.get("structure", 0),
            "no_red_flags": llm_result.get("no_red_flags", 0),
            "length": llm_result.get("length", 0),
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