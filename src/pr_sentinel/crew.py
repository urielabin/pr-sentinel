"""CrewAI agents that turn a PR diff into a structured review comment."""

from __future__ import annotations

from crewai import Agent, Crew, Process, Task

DEFAULT_MODEL = "anthropic/claude-sonnet-5"


def build_review_crew(model: str = DEFAULT_MODEL) -> Crew:
    """Wire up the two-agent review crew: a summarizer and a risk/test-coverage analyst."""
    summarizer = Agent(
        role="Diff Summarizer",
        goal="Explain what a pull request changes in plain language",
        backstory="A senior engineer who reads diffs for a living and writes concise, accurate summaries.",
        llm=model,
        verbose=False,
    )

    risk_analyst = Agent(
        role="Risk & Test Coverage Analyst",
        goal="Identify risky changes and gaps in test coverage",
        backstory=(
            "A quality engineer who has shipped hundreds of releases and knows which kinds of changes "
            "tend to break production: large diffs with no accompanying tests, changes to auth/payment/"
            "config code, and removed error handling."
        ),
        llm=model,
        verbose=False,
    )

    summarize_task = Task(
        description=(
            "Summarize what this pull request changes, in 3-5 bullet points. "
            "Be specific about which files or areas changed.\n\nDiff:\n{diff}"
        ),
        expected_output="A short bullet-point summary of the change.",
        agent=summarizer,
    )

    risk_task = Task(
        description=(
            "Given the diff and the list of changed files below, flag:\n"
            "1. Any risky changes (large diffs, auth/payment/config code, removed error handling)\n"
            "2. Changed source files that have no corresponding test file changes\n"
            "Be concise — respond with exactly 'No concerns found.' if nothing stands out.\n\n"
            "Diff:\n{diff}\n\nChanged files:\n{files}"
        ),
        expected_output="A short list of risk/test-coverage flags, or 'No concerns found.'",
        agent=risk_analyst,
    )

    return Crew(
        agents=[summarizer, risk_analyst],
        tasks=[summarize_task, risk_task],
        process=Process.sequential,
        verbose=False,
    )


def render_comment(summary: str, risk: str) -> str:
    """Format the crew's outputs into a single markdown PR comment."""
    return (
        "## 🤖 PR Sentinel Review\n\n"
        "### Summary\n"
        f"{summary}\n\n"
        "### Risk & Test Coverage\n"
        f"{risk}\n\n"
        "<sub>Generated automatically by "
        "[PR Sentinel](https://github.com/urielabin/pr-sentinel) — "
        "an AI reviewer, not a substitute for human review.</sub>"
    )
