import json

import httpx
import pytest
import respx
from httpx import Response

from pr_sentinel.github_client import GitHubClient

REPO = "urielabin/demo"


@respx.mock
def test_get_pr_diff_returns_diff_text() -> None:
    respx.get(f"https://api.github.com/repos/{REPO}/pulls/1").mock(
        return_value=Response(200, text="diff --git a/x b/x\n+added line")
    )
    with GitHubClient(token="fake-token", repo=REPO) as client:
        diff = client.get_pr_diff(1)

    assert "diff --git" in diff


@respx.mock
def test_get_pr_files_returns_parsed_json() -> None:
    respx.get(f"https://api.github.com/repos/{REPO}/pulls/1/files").mock(
        return_value=Response(200, json=[{"filename": "src/x.py", "additions": 5, "deletions": 1}])
    )
    with GitHubClient(token="fake-token", repo=REPO) as client:
        files = client.get_pr_files(1)

    assert files == [{"filename": "src/x.py", "additions": 5, "deletions": 1}]


@respx.mock
def test_post_comment_sends_expected_body() -> None:
    route = respx.post(f"https://api.github.com/repos/{REPO}/issues/1/comments").mock(
        return_value=Response(201, json={"id": 1})
    )
    with GitHubClient(token="fake-token", repo=REPO) as client:
        client.post_comment(1, "hello world")

    assert route.called
    assert json.loads(route.calls.last.request.content) == {"body": "hello world"}


@respx.mock
def test_raises_on_http_error() -> None:
    respx.get(f"https://api.github.com/repos/{REPO}/pulls/404").mock(return_value=Response(404))
    with GitHubClient(token="fake-token", repo=REPO) as client, pytest.raises(httpx.HTTPStatusError):
        client.get_pr_diff(404)
