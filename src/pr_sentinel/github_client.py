"""Minimal GitHub REST client for reading PR diffs and posting review comments."""

from __future__ import annotations

from typing import Any

import httpx

API_BASE = "https://api.github.com"


class GitHubClient:
    """Thin wrapper around the GitHub REST API endpoints PR Sentinel needs."""

    def __init__(self, token: str, repo: str) -> None:
        self._repo = repo
        self._client = httpx.Client(
            base_url=API_BASE,
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
            },
            timeout=30.0,
        )

    def get_pr_diff(self, pr_number: int) -> str:
        """Return the unified diff for a pull request."""
        resp = self._client.get(
            f"/repos/{self._repo}/pulls/{pr_number}",
            headers={"Accept": "application/vnd.github.v3.diff"},
        )
        resp.raise_for_status()
        return resp.text

    def get_pr_files(self, pr_number: int) -> list[dict[str, Any]]:
        """Return the list of changed files (filename, additions, deletions, ...)."""
        resp = self._client.get(f"/repos/{self._repo}/pulls/{pr_number}/files", params={"per_page": 100})
        resp.raise_for_status()
        result: list[dict[str, Any]] = resp.json()
        return result

    def post_comment(self, pr_number: int, body: str) -> None:
        """Post a review comment on the pull request's conversation thread."""
        resp = self._client.post(f"/repos/{self._repo}/issues/{pr_number}/comments", json={"body": body})
        resp.raise_for_status()

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> GitHubClient:
        return self

    def __exit__(self, *_exc_info: object) -> None:
        self.close()
