NEGOTIATION_TASKS = [
    {
        "id": "negotiation_hard_1",
        "role": "Software Engineer",
        "company": "a mid-size product company in Hyderabad",
        "initial_offer_lpa": 6,
        "target_lpa": 9,
        "market_rate_lpa": 8.5,
        "hr_pushback_responses": [
            "That's above our budget for this role.",
            "We have other candidates at this offer level.",
            "The best we can do is 7 LPA.",
            "Let me check with the team, but I can't promise more than 7.5 LPA.",
            "Final offer: 8 LPA. Take it or leave it.",
        ],
        "scenario_intro": (
            "You have received an offer of ₹6 LPA from {company} for the role of {role}. "
            "The market rate for this role in Hyderabad is ₹{market_rate_lpa} LPA. "
            "Your goal is to negotiate to at least ₹9 LPA professionally and confidently. "
            "HR has just said: 'We're happy to offer you ₹6 LPA. What do you think?'"
        ),
    },
    {
        "id": "negotiation_hard_2",
        "role": "Frontend Developer",
        "company": "a funded startup in Bangalore",
        "initial_offer_lpa": 7,
        "target_lpa": 10,
        "market_rate_lpa": 9.5,
        "hr_pushback_responses": [
            "That seems high for your experience level.",
            "We're a startup, our budgets are tight.",
            "Maximum we can go is 8 LPA.",
            "We could offer 8.5 LPA with a performance review in 6 months.",
            "Final answer: 9 LPA. This is our best offer.",
        ],
        "scenario_intro": (
            "You have received an offer of ₹7 LPA from {company} for the role of {role}. "
            "The market rate for this role in Bangalore is ₹{market_rate_lpa} LPA. "
            "Your goal is to negotiate to at least ₹10 LPA professionally and confidently. "
            "HR has just said: 'We're excited to offer you ₹7 LPA. Shall we proceed?'"
        ),
    },
]