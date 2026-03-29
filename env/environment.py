import uuid
import random
from env.models import (
    JobApplyObservation, JobApplyAction,
    StepResult, ResetResult, StateResult
)
from env.tasks.resume_tasks import RESUME_TASKS
from env.tasks.hr_tasks import HR_TASKS
from env.tasks.negotiation_tasks import NEGOTIATION_TASKS
from env.graders.resume_grader import grade_resume_bullet
from env.graders.hr_grader import grade_hr_answer
from env.graders.negotiation_grader import grade_negotiation_turn


class JobApplyEnv:

    TASK_IDS = ["resume_bullet", "hr_screening", "salary_negotiation"]

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
        # HR specific
        self.current_question_index = 0
        self.hr_scores = []
        # Negotiation specific
        self.negotiation_turn = 0

    # ─────────────────────────────────────────
    # RESET
    # ─────────────────────────────────────────
    def reset(self, task_id: str = None) -> ResetResult:
        self._reset_state()

        # Pick task
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
            self.max_steps = 3  # one per question
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
                market_rate_lpa=self.current_task["market_rate_lpa"]
            )

        self.step_number = 1

        return ResetResult(
            observation=JobApplyObservation(
                task_id=self.task_id,
                scenario=scenario,
                step_number=self.step_number,
                feedback="",
                max_steps=self.max_steps
            )
        )

    # ─────────────────────────────────────────
    # STEP
    # ─────────────────────────────────────────
    def step(self, action: JobApplyAction) -> StepResult:
        if self.done:
            raise RuntimeError("Episode is done. Call reset() to start a new episode.")

        if self.task_id == "resume_bullet":
            return self._step_resume(action)
        elif self.task_id == "hr_screening":
            return self._step_hr(action)
        elif self.task_id == "salary_negotiation":
            return self._step_negotiation(action)

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
            f"Your last attempt scored {reward.score}/1.0. Try again."
        ) if not self.done else "Episode complete."

        obs = JobApplyObservation(
            task_id=self.task_id,
            scenario=next_scenario,
            step_number=self.step_number,
            feedback=reward.feedback,
            max_steps=self.max_steps
        )

        self.step_number += 1

        return StepResult(
            observation=obs,
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
                f"Good. Next question:\n\n"
                f"❓ \"{next_q}\"\n\n"
                f"Answer in 60–150 words."
            )
        else:
            avg = round(sum(self.hr_scores) / len(self.hr_scores), 2)
            next_scenario = f"Interview complete. Average score: {avg}/1.0"
            # Override reward with average on final step
            from env.models import JobApplyReward
            reward = JobApplyReward(
                score=avg,
                breakdown={"average_of_3_questions": avg},
                feedback=f"Interview complete. Your average score was {avg}/1.0",
                is_best_so_far=avg > self.best_score
            )

        obs = JobApplyObservation(
            task_id=self.task_id,
            scenario=next_scenario,
            step_number=self.step_number,
            feedback=reward.feedback,
            max_steps=self.max_steps
        )

        self.step_number += 1

        return StepResult(
            observation=obs,
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

        # HR pushback response
        hr_reply = (
            self.current_task["hr_pushback_responses"][self.negotiation_turn]
            if self.negotiation_turn < len(self.current_task["hr_pushback_responses"])
            else "We'll consider your offer."
        )

        next_scenario = (
            f"HR says: \"{hr_reply}\"\n\nYour response?"
        ) if not self.done else f"Negotiation complete. Final score: {reward.score}/1.0"

        obs = JobApplyObservation(
            task_id=self.task_id,
            scenario=next_scenario,
            step_number=self.step_number,
            feedback=reward.feedback,
            max_steps=self.max_steps
        )

        self.negotiation_turn += 1
        self.step_number += 1

        return StepResult(
            observation=obs,
            reward=reward,
            done=self.done,
            info={"episode_id": self.episode_id, "negotiation_turn": self.negotiation_turn}
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