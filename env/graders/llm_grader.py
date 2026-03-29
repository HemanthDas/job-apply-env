import os
import json
import re
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

_client = None

def get_client():
    global _client
    if _client is None:
        api_key = os.environ.get("GROQ_API_KEY")
        if api_key:
            _client = Groq(api_key=api_key)
    return _client


def _parse_json_response(text: str) -> dict | None:
    """Safely extract JSON from LLM response."""
    try:
        # Try direct parse first
        return json.loads(text)
    except Exception:
        pass
    try:
        # Extract JSON block if wrapped in markdown
        match = re.search(r'\{.*\}', text, re.DOTALL)
        if match:
            return json.loads(match.group())
    except Exception:
        pass
    return None


def llm_grade_resume(original: str, rewritten: str) -> dict | None:
    """
    Use LLM to grade a resume bullet. Returns dict with scores or None if failed.
    """
    client = get_client()
    if not client:
        return None

    prompt = f"""You are an expert resume coach grading a rewritten resume bullet.

ORIGINAL WEAK BULLET:
"{original}"

REWRITTEN BULLET:
"{rewritten}"

Grade the rewritten bullet on these 4 criteria. Return ONLY a JSON object, no explanation:

{{
  "action_verb": <0.0 to 0.25, does it start with a strong action verb like Developed/Built/Optimized?>,
  "has_metric": <0.0 to 0.35, does it contain specific numbers or metrics?>,
  "business_impact": <0.0 to 0.25, does it mention clear business impact or outcome?>,
  "conciseness": <0.0 to 0.15, is it concise and under 25 words?>,
  "feedback": "<one sentence of constructive feedback>",
  "total": <sum of all 4 scores rounded to 2 decimal places>
}}"""

    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=300,
            temperature=0.1
        )
        return _parse_json_response(response.choices[0].message.content)
    except Exception:
        return None


def llm_grade_hr(question: str, answer: str) -> dict | None:
    """
    Use LLM to grade an HR answer. Returns dict with scores or None if failed.
    """
    client = get_client()
    if not client:
        return None

    prompt = f"""You are an expert HR interviewer grading a candidate's answer.

QUESTION: "{question}"
ANSWER: "{answer}"

Grade this answer on 4 criteria. Return ONLY a JSON object, no explanation:

{{
  "relevance": <0.0 to 0.30, how directly does it answer the question?>,
  "structure": <0.0 to 0.30, does it have clear intro, body, and closing?>,
  "no_red_flags": <0.0 or 0.20, does it avoid cliche or negative phrases?>,
  "length": <0.0 to 0.20, is it 60-150 words? Give full marks if yes, partial if close>,
  "feedback": "<one sentence of constructive feedback>",
  "total": <sum of all 4 scores rounded to 2 decimal places>
}}"""

    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=300,
            temperature=0.1
        )
        return _parse_json_response(response.choices[0].message.content)
    except Exception:
        return None


def llm_grade_negotiation(
    agent_response: str,
    initial_offer: float,
    target_lpa: float,
    is_final_turn: bool
) -> dict | None:
    """
    Use LLM to grade a salary negotiation response. Returns dict or None if failed.
    """
    client = get_client()
    if not client:
        return None

    prompt = f"""You are an expert salary negotiation coach grading a candidate's response.

CONTEXT:
- Initial offer: ₹{initial_offer} LPA
- Candidate's target: ₹{target_lpa} LPA  
- Is this the final turn: {is_final_turn}

CANDIDATE'S RESPONSE:
"{agent_response}"

Grade this response. Return ONLY a JSON object, no explanation:

{{
  "salary_outcome": <0.0 to 0.50, did they make a strong counter-offer? Higher if closer to target. On final turn, score based on final number achieved.>,
  "market_data": <0.0 to 0.25, did they cite market data or research to justify their ask?>,
  "professional_tone": <0.0 to 0.25, was the tone confident yet collaborative and professional?>,
  "feedback": "<one sentence of constructive feedback>",
  "total": <sum of all 3 scores rounded to 2 decimal places>
}}"""

    try:
        response = client.chat.completions.create(
            model="llama-3.1-8b-instant",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=300,
            temperature=0.1
        )
        return _parse_json_response(response.choices[0].message.content)
    except Exception:
        return None