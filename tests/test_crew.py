from pr_sentinel.crew import build_review_crew, render_comment


def test_build_review_crew_wires_two_agents_and_tasks() -> None:
    crew = build_review_crew(model="anthropic/claude-sonnet-5")

    assert len(crew.agents) == 2
    assert len(crew.tasks) == 2
    assert crew.agents[0].role == "Diff Summarizer"
    assert crew.agents[1].role == "Risk & Test Coverage Analyst"


def test_build_review_crew_uses_requested_model() -> None:
    crew = build_review_crew(model="anthropic/claude-opus-4-8")

    assert all(agent.llm.model == "claude-opus-4-8" for agent in crew.agents)


def test_render_comment_includes_summary_and_risk() -> None:
    comment = render_comment(summary="Added a login form.", risk="No concerns found.")

    assert "Added a login form." in comment
    assert "No concerns found." in comment
    assert "PR Sentinel" in comment
