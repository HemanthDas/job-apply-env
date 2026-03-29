import pytest
from env.environment import JobApplyEnv
from env.models import JobApplyAction, JobApplyObservation, JobApplyReward


@pytest.fixture
def env():
    return JobApplyEnv()


# ─────────────────────────────────────────
# RESET TESTS
# ─────────────────────────────────────────
def test_reset_resume(env):
    result = env.reset(task_id="resume_bullet")
    assert result.observation.task_id == "resume_bullet"
    assert result.observation.step_number == 1
    assert result.observation.max_steps == 3
    assert result.observation.feedback == ""
    assert len(result.observation.conversation_history) == 1


def test_reset_hr(env):
    result = env.reset(task_id="hr_screening")
    assert result.observation.task_id == "hr_screening"
    assert result.observation.max_steps == 3


def test_reset_negotiation(env):
    result = env.reset(task_id="salary_negotiation")
    assert result.observation.task_id == "salary_negotiation"
    assert result.observation.max_steps == 5


def test_reset_linkedin(env):
    result = env.reset(task_id="linkedin_bio")
    assert result.observation.task_id == "linkedin_bio"
    assert result.observation.max_steps == 3


def test_reset_random(env):
    result = env.reset()
    assert result.observation.task_id in env.TASK_IDS


# ─────────────────────────────────────────
# STEP TESTS
# ─────────────────────────────────────────
def test_step_resume_returns_reward(env):
    env.reset(task_id="resume_bullet")
    result = env.step(JobApplyAction(
        response="Developed 15 RESTful APIs reducing latency by 40% for 10K daily users"
    ))
    assert isinstance(result.reward.score, float)
    assert 0.0 <= result.reward.score <= 1.0
    assert isinstance(result.reward.breakdown, dict)
    assert isinstance(result.done, bool)


def test_step_hr_advances_questions(env):
    env.reset(task_id="hr_screening")
    result = env.step(JobApplyAction(
        response="I am a software engineer with 2 years of Java experience building REST APIs for fintech clients. I enjoy solving complex backend problems and am excited to contribute to scalable products at a product company."
    ))
    assert result.observation.step_number == 2
    assert not result.done  # 3 questions, only 1 answered


def test_step_negotiation_tracks_turns(env):
    env.reset(task_id="salary_negotiation")
    result = env.step(JobApplyAction(
        response="Thank you for the offer. Based on AmbitionBox market data, the average for this role is 8.5 LPA. I would like to propose 9.5 LPA given my experience."
    ))
    assert result.observation.step_number == 2
    assert "negotiation_turn" in result.info


def test_episode_ends_after_max_steps(env):
    env.reset(task_id="resume_bullet")
    for _ in range(3):
        if not env.done:
            env.step(JobApplyAction(response="weak response with no metrics"))
    assert env.done


def test_step_after_done_raises(env):
    env.reset(task_id="resume_bullet")
    for _ in range(3):
        if not env.done:
            env.step(JobApplyAction(response="weak response"))
    with pytest.raises(RuntimeError):
        env.step(JobApplyAction(response="should fail"))


# ─────────────────────────────────────────
# STATE TESTS
# ─────────────────────────────────────────
def test_state_after_reset(env):
    env.reset(task_id="resume_bullet")
    state = env.state()
    assert state.task_id == "resume_bullet"
    assert state.step_number == 1
    assert state.best_score == 0.0
    assert not state.done
    assert state.episode_id != ""


def test_state_updates_after_step(env):
    env.reset(task_id="resume_bullet")
    env.step(JobApplyAction(
        response="Developed 15 RESTful APIs reducing latency by 40% for 10K daily users"
    ))
    state = env.state()
    assert state.step_number == 2
    assert state.best_score > 0.0


# ─────────────────────────────────────────
# GRADER TESTS
# ─────────────────────────────────────────
def test_resume_grader_perfect_score():
    from env.graders.resume_grader import grade_resume_bullet
    reward = grade_resume_bullet(
        "Worked on backend APIs",
        "Developed 15 RESTful APIs reducing response latency by 40% for 10K daily users",
        0.0
    )
    assert reward.score >= 0.75


def test_resume_grader_strips_prefix():
    from env.graders.resume_grader import grade_resume_bullet
    reward = grade_resume_bullet(
        "Worked on backend APIs",
        "✅ STRONG: Developed 15 RESTful APIs reducing latency by 40% for 10K users",
        0.0
    )
    assert reward.score >= 0.75


def test_negotiation_grader_scores_market_data():
    from env.graders.negotiation_grader import grade_negotiation_turn
    reward = grade_negotiation_turn(
        "Based on AmbitionBox market research, average is 8.5 LPA. I propose 9.5 LPA.",
        0, 5, 6.0, 9.0, 0.0, False
    )
    assert reward.score > 0.0


def test_reward_score_always_in_range(env):
    for task_id in env.TASK_IDS:
        env.reset(task_id=task_id)
        result = env.step(JobApplyAction(response="test response for scoring"))
        assert 0.0 <= result.reward.score <= 1.0