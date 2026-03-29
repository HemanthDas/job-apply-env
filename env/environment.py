import uuid
import random
from env.models import (
    JobApplyObservation, JobApplyAction,
    StepResult, ResetResult, StateResult
)
from env.tasks.linkedin_tasks import LINKEDIN_TASKS
from env.graders.linkedin_grader import grade_linkedin_bio
from env.tasks.resume_tasks import RESUME_TASKS
from env.tasks.hr_tasks import HR_TASKS
from env.tasks.negotiation_tasks import NEGOTIATION_TASKS
from env.graders.resume_grader import grade_resume_bullet
from env.graders.hr_grader import grade_hr_answer
from env.graders.negotiation_grader import grade_negotiation_turn


class JobApplyEnv:

    TASK_IDS = ["resume_bullet", "hr_screening", "salary_negotiation", "linkedin_bio"]

    def __init__(self):
        self._reset_state()

    def _reset_state(self):
        self.episode_id = str(uuid.uuid4())
        self.task_id = None
        self.step_number = 0
        self.max_steps = 0
        self.done = False
        self.best_score = 0.0
        self.current_task = None
        self.conversation_history = []      # tracks full dialogue
        self.context_summary = ""           # running summary
        # HR specific
        self.current_question_index = 0
        self.hr_scores = []
        # Negotiation specific
        self.negotiation_turn = 0

    def _add_to_history(self, role: str, content: str):
        self.conversation_history.append({"role": role, "content": content})
        # Keep summary updated
        if role == "agent":
            self.context_summary += f"Turn {self.step_number}: Agent said: {content[:100]}... "

    # ─────────────────────────────────────────
    # RESET
    # ─────────────────────────────────────────
    def reset(self, task_id: str = None) -> ResetResult:
        self._reset_state()

        self.task_id = task_id if task_id in self.TASK_IDS else random.choice(self.TASK_IDS)

        if self.task_id == "resume_bullet":
            self.current_task = random.choice(RESUME_TASKS)
            self.max_steps = 3
            scenario = (
                f"You are applying for: {self.current_task['role_context']}.\n\n"
                f"Rewrite this weak resume bullet using STAR format "
                f"(Action verb + What you did + Metric + Impact):\n\n"
                f"❌ WEAK: \"{self.current_task['weak_bullet']}\"\n\n"
                f"Write a single improved bullet point."
            )

        elif self.task_id == "hr_screening":
            self.current_task = random.choice(HR_TASKS)
            self.max_steps = 3
            self.current_question_index = 0
            scenario = (
                f"You are interviewing for: {self.current_task['role']} "
                f"at {self.current_task['company_context']}.\n\n"
                f"Answer this HR question in 60–150 words:\n\n"
                f"❓ \"{self.current_task['questions'][0]}\""
            )

        elif self.task_id == "salary_negotiation":
            self.current_task = random.choice(NEGOTIATION_TASKS)
            self.max_steps = 5
            self.negotiation_turn = 0
            scenario = self.current_task["scenario_intro"].format(
                company=self.current_task["company"],
                role=self.current_task["role"],
                market_rate_lpa=self.current_task["market_rate_lpa"],
                initial_offer_lpa=self.current_task["initial_offer_lpa"],
                target_lpa=self.current_task["target_lpa"]
            )
        elif self.task_id == "linkedin_bio":
            self.current_task = random.choice(LINKEDIN_TASKS)
            self.max_steps = 3
            scenario = (
                f"You are helping a {self.current_task['experience_years']}-year experienced "
                f"{self.current_task['role']} at {self.current_task['current_company']}.\n\n"
                f"Goal: {self.current_task['goal']}\n"
                f"Skills: {', '.join(self.current_task['skills'])}\n\n"
                f"Rewrite this weak LinkedIn bio into a compelling 3-5 sentence summary:\n\n"
                f"❌ WEAK: \"{self.current_task['weak_bio']}\"\n\n"
                f"Write the improved LinkedIn bio."
            )
        self.step_number = 1
        self._add_to_history("env", scenario)

        return ResetResult(
            observation=JobApplyObservation(
                task_id=self.task_id,
                scenario=scenario,
                step_number=self.step_number,
                feedback="",
                max_steps=self.max_steps,
                conversation_history=self.conversation_history.copy(),
                context_summary=self.context_summary
            )
        )

    # ─────────────────────────────────────────
    # STEP
    # ─────────────────────────────────────────
    def step(self, action: JobApplyAction) -> StepResult:
        if self.done:
            raise RuntimeError("Episode is done. Call reset() to start a new episode.")

        self._add_to_history("agent", action.response)

        if self.task_id == "resume_bullet":
            return self._step_resume(action)
        elif self.task_id == "hr_screening":
            return self._step_hr(action)
        elif self.task_id == "salary_negotiation":
            return self._step_negotiation(action)
        elif self.task_id == "linkedin_bio":
            return self._step_linkedin(action)
    # ─────────────────────────────────────────
    # STEP — RESUME
    # ─────────────────────────────────────────
    def _step_resume(self, action: JobApplyAction) -> StepResult:
        reward = grade_resume_bullet(
            original=self.current_task["weak_bullet"],
            rewritten=action.response,
            best_score_so_far=self.best_score
        )

        if reward.score > self.best_score:
            self.best_score = reward.score

        self.done = self.step_number >= self.max_steps or reward.score == 1.0

        next_scenario = (
            f"Rewrite this weak resume bullet:\n\n"
            f"❌ WEAK: \"{self.current_task['weak_bullet']}\"\n\n"
            f"Your last attempt scored {reward.score}/1.0. Try again.\n\n"
            f"💡 Feedback: {reward.feedback}"
        ) if not self.done else "Episode complete. Well done!"

        self._add_to_history("env", next_scenario)
        self.step_number += 1

        return StepResult(
            observation=JobApplyObservation(
                task_id=self.task_id,
                scenario=next_scenario,
                step_number=self.step_number,
                feedback=reward.feedback,
                max_steps=self.max_steps,
                conversation_history=self.conversation_history.copy(),
                context_summary=self.context_summary
            ),
            reward=reward,
            done=self.done,
            info={"episode_id": self.episode_id, "best_score": self.best_score}
        )
    def _step_linkedin(self, action: JobApplyAction) -> StepResult:
        reward = grade_linkedin_bio(
            weak_bio=self.current_task["weak_bio"],
            rewritten_bio=action.response,
            role=self.current_task["role"],
            goal=self.current_task["goal"],
            best_score_so_far=self.best_score
        )

        if reward.score > self.best_score:
            self.best_score = reward.score

        self.done = self.step_number >= self.max_steps or reward.score >= 0.95

        next_scenario = (
            f"Rewrite this weak LinkedIn bio:\n\n"
            f"❌ WEAK: \"{self.current_task['weak_bio']}\"\n\n"
            f"Your last attempt scored {reward.score}/1.0. Try again.\n\n"
            f"💡 Feedback: {reward.feedback}"
        ) if not self.done else "Episode complete. Great LinkedIn bio!"

        self._add_to_history("env", next_scenario)
        self.step_number += 1

        return StepResult(
            observation=JobApplyObservation(
                task_id=self.task_id,
                scenario=next_scenario,
                step_number=self.step_number,
                feedback=reward.feedback,
                max_steps=self.max_steps,
                conversation_history=self.conversation_history.copy(),
                context_summary=self.context_summary
            ),
            reward=reward,
            done=self.done,
            info={"episode_id": self.episode_id, "best_score": self.best_score}
        )
    # ─────────────────────────────────────────
    # STEP — HR SCREENING
    # ─────────────────────────────────────────
    def _step_hr(self, action: JobApplyAction) -> StepResult:
        current_question = self.current_task["questions"][self.current_question_index]

        reward = grade_hr_answer(
            question=current_question,
            answer=action.response,
            best_score_so_far=self.best_score
        )

        self.hr_scores.append(reward.score)
        if reward.score > self.best_score:
            self.best_score = reward.score

        self.current_question_index += 1
        self.done = self.current_question_index >= len(self.current_task["questions"])

        if not self.done:
            next_q = self.current_task["questions"][self.current_question_index]
            next_scenario = (
                f"Good answer. Moving to question {self.current_question_index + 1} of "
                f"{len(self.current_task['questions'])}:\n\n"
                f"❓ \"{next_q}\"\n\n"
                f"Answer in 60–150 words.\n\n"
                f"📝 Previous answers so far: {len(self.hr_scores)} question(s) answered."
            )
        else:
            avg = round(sum(self.hr_scores) / len(self.hr_scores), 2)
            next_scenario = (
                f"Interview complete!\n\n"
                f"📊 Your scores: {self.hr_scores}\n"
                f"🏆 Average: {avg}/1.0"
            )
            from env.models import JobApplyReward
            reward = JobApplyReward(
                score=avg,
                breakdown={"q1": self.hr_scores[0], "q2": self.hr_scores[1] if len(self.hr_scores) > 1 else 0, "q3": self.hr_scores[2] if len(self.hr_scores) > 2 else 0},
                feedback=f"Interview complete. Average score: {avg}/1.0",
                is_best_so_far=avg > self.best_score
            )

        self._add_to_history("env", next_scenario)
        self.step_number += 1

        return StepResult(
            observation=JobApplyObservation(
                task_id=self.task_id,
                scenario=next_scenario,
                step_number=self.step_number,
                feedback=reward.feedback,
                max_steps=self.max_steps,
                conversation_history=self.conversation_history.copy(),
                context_summary=self.context_summary
            ),
            reward=reward,
            done=self.done,
            info={"episode_id": self.episode_id, "hr_scores": self.hr_scores}
        )

    # ─────────────────────────────────────────
    # STEP — SALARY NEGOTIATION
    # ─────────────────────────────────────────
    def _step_negotiation(self, action: JobApplyAction) -> StepResult:
        is_final = self.negotiation_turn >= self.max_steps - 1

        reward = grade_negotiation_turn(
            agent_response=action.response,
            turn_number=self.negotiation_turn,
            max_turns=self.max_steps,
            initial_offer=self.current_task["initial_offer_lpa"],
            target_lpa=self.current_task["target_lpa"],
            best_score_so_far=self.best_score,
            is_final_turn=is_final
        )

        if reward.score > self.best_score:
            self.best_score = reward.score

        self.done = is_final

        hr_reply = (
            self.current_task["hr_pushback_responses"][self.negotiation_turn]
            if self.negotiation_turn < len(self.current_task["hr_pushback_responses"])
            else "We'll consider your offer."
        )

        next_scenario = (
            f"HR says: \"{hr_reply}\"\n\n"
            f"📊 Negotiation progress: Turn {self.negotiation_turn + 1}/{self.max_steps}\n"
            f"💰 Initial offer: ₹{self.current_task['initial_offer_lpa']} LPA | "
            f"🎯 Your target: ₹{self.current_task['target_lpa']} LPA\n\n"
            f"Your response?"
        ) if not self.done else (
            f"Negotiation complete!\n"
            f"📊 Final score: {reward.score}/1.0\n"
            f"💬 Full negotiation: {len(self.conversation_history)} turns"
        )

        self._add_to_history("env", f"HR: {hr_reply}")
        self.negotiation_turn += 1
        self.step_number += 1

        return StepResult(
            observation=JobApplyObservation(
                task_id=self.task_id,
                scenario=next_scenario,
                step_number=self.step_number,
                feedback=reward.feedback,
                max_steps=self.max_steps,
                conversation_history=self.conversation_history.copy(),
                context_summary=self.context_summary
            ),
            reward=reward,
            done=self.done,
            info={
                "episode_id": self.episode_id,
                "negotiation_turn": self.negotiation_turn,
                "best_score": self.best_score
            }
        )

    # ─────────────────────────────────────────
    # STATE
    # ─────────────────────────────────────────
    def state(self) -> StateResult:
        return StateResult(
            task_id=self.task_id or "none",
            step_number=self.step_number,
            max_steps=self.max_steps,
            best_score=self.best_score,
            done=self.done,
            episode_id=self.episode_id
        )