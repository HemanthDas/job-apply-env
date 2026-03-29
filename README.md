---
title: JobApply-Env
emoji: 🎯
colorFrom: blue
colorTo: green
sdk: gradio
sdk_version: 5.23.3
app_file: main.py
pinned: false
license: mit
tags:
  - openenv
  - job-application
  - hiring
  - india
  - nlp
  - career
---

# 🎯 JobApply-Env

An OpenEnv environment simulating the Indian job application process.
An AI agent navigates three real-world hiring tasks with increasing difficulty.

## 🌍 Motivation

Millions of Indian freshers struggle with resume writing, HR interviews, and
salary negotiation every year. This environment trains AI agents to master
these real-world career tasks — making it immediately useful for both agent
evaluation and career coaching tools.

## 📋 Tasks

| Task                 | Difficulty | Max Steps | Description                                           |
| -------------------- | ---------- | --------- | ----------------------------------------------------- |
| `resume_bullet`      | Easy       | 3         | Rewrite a weak resume bullet in STAR format           |
| `hr_screening`       | Medium     | 3         | Answer 3 classic HR interview questions               |
| `salary_negotiation` | Hard       | 5         | Multi-turn salary negotiation dialogue                |
| `linkedin_bio`       | Medium     | 3         | Rewrite a weak LinkedIn bio into a compelling summary |

## 📥 Observation Space

```json
{
  "task_id": "resume_bullet",
  "scenario": "Rewrite this weak bullet...",
  "step_number": 1,
  "feedback": "Previous attempt feedback",
  "max_steps": 3
}
```

## 📤 Action Space

```json
{
  "response": "Agent's text response"
}
```

## 🏆 Reward Space

```json
{
  "score": 0.85,
  "breakdown": {
    "action_verb": 0.25,
    "has_metric": 0.35,
    "business_impact": 0.25,
    "conciseness": 0.15
  },
  "feedback": "Strong bullet! Include business impact.",
  "is_best_so_far": true
}
```

## 🚀 Setup & Usage

### Local

```bash
git clone https://huggingface.co/spaces/your-username/job-apply-env
cd job-apply-env
pip install -r requirements.txt
uvicorn main:app --host 0.0.0.0 --port 7860
```

### Docker

```bash
docker build -t job-apply-env .
docker run -p 7860:7860 job-apply-env
```

### API Endpoints

| Method | Endpoint  | Description         |
| ------ | --------- | ------------------- |
| POST   | `/reset`  | Start new episode   |
| POST   | `/step`   | Submit agent action |
| GET    | `/state`  | Get current state   |
| GET    | `/health` | Health check        |

## 🤖 Baseline Script

```bash
pip install groq
export GROQ_API_KEY=your_key_here
python baseline.py
```

## 📊 Baseline Scores (Llama 3.1 8B via Groq)

| Task                | Difficulty | Score    |
| ------------------- | ---------- | -------- |
| resume_bullet       | Easy       | 1.00     |
| hr_screening        | Medium     | 0.85     |
| salary_negotiation  | Hard       | 0.95     |
| linkedin_bio        | Medium     | 0.86     |
| **Overall Average** |            | **0.92** |

## 📁 Project Structure

```
job-apply-env/
├── env/
│   ├── environment.py       # Main env class
│   ├── models.py            # Pydantic models
│   ├── graders/             # Task graders
│   └── tasks/               # Task scenarios
├── baseline.py              # Baseline inference script
├── main.py                  # FastAPI server
├── openenv.yaml             # OpenEnv spec
├── Dockerfile               # Container config
└── README.md
```

## 🏷️ Tags

`openenv` `job-application` `hiring` `india` `nlp` `career` `rl`
