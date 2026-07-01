"""Entry point for running PR Sentinel inside a GitHub Actions workflow."""

from __future__ import annotations

import json
import os

from crewai.crews.crew_output import CrewOutput

from pr_sentinel.crew import build_review_crew, render_comment
from pr_sentinel.github_client import GitHubClient


def _load_pr_number(event_path: str) -> int:
    with open(event_path) as f:
        event = json.load(f)
    pr = event.get("pull_request")
    if not pr:
        raise SystemExit("PR Sentinel only supports pull_request events.")
    return int(pr["number"])


def review_pull_request(client: GitHubClient, pr_number: int, model: str) -> str:
    """Fetch the diff, run the review crew, post the comment, and return it (for logging/tests)."""
    diff = client.get_pr_diff(pr_number)
    files = client.get_pr_files(pr_number)
    file_list = "\n".join(f"- {f['filename']} (+{f['additions']}/-{f['deletions']})" for f in files)

    crew = build_review_crew(model=model)
    result = crew.kickoff(inputs={"diff": diff, "files": file_list})
    if not isinstance(result, CrewOutput):
        raise TypeError(f"Expected a CrewOutput (non-streaming crew), got {type(result).__name__}")

    summary = str(result.tasks_output[0].raw)
    risk = str(result.tasks_output[1].raw)

    comment = render_comment(summary=summary, risk=risk)
    client.post_comment(pr_number, comment)
    return comment


def run() -> None:
    token = os.environ["GITHUB_TOKEN"]
    repo = os.environ["GITHUB_REPOSITORY"]
    event_path = os.environ["GITHUB_EVENT_PATH"]
    model = os.environ.get("PR_SENTINEL_MODEL", "anthropic/claude-sonnet-5")
    pr_number = _load_pr_number(event_path)

    with GitHubClient(token=token, repo=repo) as client:
        review_pull_request(client, pr_number, model)


if __name__ == "__main__":
    run()
