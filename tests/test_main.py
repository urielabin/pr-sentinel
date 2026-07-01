import json
from unittest.mock import MagicMock

import pytest
from crewai.crews.crew_output import CrewOutput
from crewai.tasks.task_output import TaskOutput

from pr_sentinel.main import _load_pr_number, review_pull_request, run


def test_load_pr_number_reads_event_file(tmp_path) -> None:
    event_path = tmp_path / "event.json"
    event_path.write_text(json.dumps({"pull_request": {"number": 42}}))

    assert _load_pr_number(str(event_path)) == 42


def test_load_pr_number_rejects_non_pr_events(tmp_path) -> None:
    event_path = tmp_path / "event.json"
    event_path.write_text(json.dumps({"push": {}}))

    with pytest.raises(SystemExit):
        _load_pr_number(str(event_path))


def _fake_crew_result() -> CrewOutput:
    return CrewOutput(
        raw="ignored",
        tasks_output=[
            TaskOutput(description="summarize", agent="Diff Summarizer", raw="- Added a login form."),
            TaskOutput(description="risk", agent="Risk & Test Coverage Analyst", raw="No concerns found."),
        ],
    )


def test_review_pull_request_posts_rendered_comment(mocker) -> None:
    client = MagicMock()
    client.get_pr_diff.return_value = "diff --git a/x b/x"
    client.get_pr_files.return_value = [{"filename": "x.py", "additions": 1, "deletions": 0}]

    fake_crew = MagicMock()
    fake_crew.kickoff.return_value = _fake_crew_result()
    mocker.patch("pr_sentinel.main.build_review_crew", return_value=fake_crew)

    comment = review_pull_request(client, pr_number=7, model="anthropic/claude-sonnet-5")

    fake_crew.kickoff.assert_called_once_with(
        inputs={"diff": "diff --git a/x b/x", "files": "- x.py (+1/-0)"}
    )
    client.post_comment.assert_called_once_with(7, comment)
    assert "Added a login form." in comment
    assert "No concerns found." in comment


def test_run_wires_env_vars_into_review(mocker, tmp_path, monkeypatch) -> None:
    event_path = tmp_path / "event.json"
    event_path.write_text(json.dumps({"pull_request": {"number": 3}}))

    monkeypatch.setenv("GITHUB_TOKEN", "fake-token")
    monkeypatch.setenv("GITHUB_REPOSITORY", "urielabin/demo")
    monkeypatch.setenv("GITHUB_EVENT_PATH", str(event_path))
    monkeypatch.setenv("PR_SENTINEL_MODEL", "anthropic/claude-opus-4-8")

    fake_client_instance = MagicMock()
    fake_client_cls = mocker.patch("pr_sentinel.main.GitHubClient")
    fake_client_cls.return_value.__enter__.return_value = fake_client_instance

    fake_review = mocker.patch("pr_sentinel.main.review_pull_request")

    run()

    fake_client_cls.assert_called_once_with(token="fake-token", repo="urielabin/demo")
    fake_review.assert_called_once_with(fake_client_instance, 3, "anthropic/claude-opus-4-8")
