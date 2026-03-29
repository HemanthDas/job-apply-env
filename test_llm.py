from env.graders.llm_grader import llm_grade_resume, llm_grade_hr, llm_grade_negotiation

# Test LLM resume grader
r = llm_grade_resume(
    'Worked on backend APIs',
    'Developed 15 RESTful APIs reducing response latency by 40% for 10K daily users'
)
print(f'LLM Resume score: {r["total"]} | Feedback: {r["feedback"]}')

# Test LLM HR grader
h = llm_grade_hr(
    'Tell me about yourself.',
    'I am a backend engineer with 2 years of Java and Spring Boot experience. I have built REST APIs for fintech clients processing 10K daily transactions. I enjoy solving complex distributed systems problems and am excited to bring this expertise to a product-focused company like yours.'
)
print(f'LLM HR score: {h["total"]} | Feedback: {h["feedback"]}')

# Test LLM negotiation grader
n = llm_grade_negotiation(
    'Based on market research from AmbitionBox, the average for this role is 8.5 LPA. Given my 2 years in Java and distributed systems, I would like to propose 9.5 LPA.',
    6.0, 9.0, False
)
print(f'LLM Negotiation score: {n["total"]} | Feedback: {n["feedback"]}')
print('LLM Graders OK ✅')