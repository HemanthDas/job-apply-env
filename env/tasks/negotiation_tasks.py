NEGOTIATION_TASKS = [
    {
        "id": "negotiation_1",
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
            "You have received an offer of ₹{initial_offer_lpa} LPA from {company} for the role of {role}. "
            "The market rate for this role in Hyderabad is ₹{market_rate_lpa} LPA. "
            "Your goal is to negotiate to at least ₹{target_lpa} LPA professionally. "
            "HR has just said: 'We're happy to offer you ₹{initial_offer_lpa} LPA. What do you think?'"
        ),
    },
    {
        "id": "negotiation_2",
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
            "You have received an offer of ₹{initial_offer_lpa} LPA from {company} for the role of {role}. "
            "The market rate for this role in Bangalore is ₹{market_rate_lpa} LPA. "
            "Your goal is to negotiate to at least ₹{target_lpa} LPA professionally. "
            "HR has just said: 'We're excited to offer you ₹{initial_offer_lpa} LPA. Shall we proceed?'"
        ),
    },
    {
        "id": "negotiation_3",
        "role": "Data Engineer",
        "company": "a Series A startup in Mumbai",
        "initial_offer_lpa": 8,
        "target_lpa": 12,
        "market_rate_lpa": 11,
        "hr_pushback_responses": [
            "That's quite a jump from what we had in mind.",
            "We're offering equity as part of the package too.",
            "Best we can offer is 9.5 LPA plus ESOPs.",
            "We can stretch to 10 LPA, that's our maximum.",
            "Final offer: 10.5 LPA with a 6-month review. Final answer.",
        ],
        "scenario_intro": (
            "You have received an offer of ₹{initial_offer_lpa} LPA from {company} for the role of {role}. "
            "The market rate for this role in Mumbai is ₹{market_rate_lpa} LPA. "
            "Your goal is to negotiate to at least ₹{target_lpa} LPA. "
            "HR says: 'We'd like to offer you ₹{initial_offer_lpa} LPA for this role. Thoughts?'"
        ),
    },
    {
        "id": "negotiation_4",
        "role": "DevOps Engineer",
        "company": "a product company in Pune",
        "initial_offer_lpa": 9,
        "target_lpa": 13,
        "market_rate_lpa": 12,
        "hr_pushback_responses": [
            "Our budget for this role is capped.",
            "We've already stretched for your profile.",
            "10.5 LPA is where we can land.",
            "We can do 11 LPA but that's truly our ceiling.",
            "Final: 11.5 LPA. We can't go higher.",
        ],
        "scenario_intro": (
            "You have received an offer of ₹{initial_offer_lpa} LPA from {company} for the role of {role}. "
            "Market rate in Pune for this role is ₹{market_rate_lpa} LPA. "
            "Negotiate professionally to ₹{target_lpa} LPA. "
            "HR says: 'We're pleased to offer ₹{initial_offer_lpa} LPA. Does that work for you?'"
        ),
    },
]