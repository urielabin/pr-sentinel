# PR Sentinel

[![CI](https://github.com/urielabin/pr-sentinel/actions/workflows/ci.yml/badge.svg)](https://github.com/urielabin/pr-sentinel/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Multi-agent AI code review for pull requests. Two [CrewAI](https://www.crewai.com/) agents backed by Claude read the diff on every PR and post a single structured comment:

- **Diff Summarizer** — what changed, in plain language
- **Risk & Test Coverage Analyst** — risky changes (auth/payment/config code, large diffs, removed error handling) and source files changed without corresponding test changes

No code generation, no auto-merge, no inline suggestions — just a fast second opinion before a human reviews the PR.

## Usage

Add to a workflow in the target repo:

```yaml
name: PR Sentinel

on:
  pull_request:

jobs:
  review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: urielabin/pr-sentinel@main
        with:
          anthropic-api-key: ${{ secrets.ANTHROPIC_API_KEY }}
```

### Inputs

| Input | Required | Default | Description |
|---|---|---|---|
| `anthropic-api-key` | yes | — | Anthropic API key |
| `github-token` | no | `${{ github.token }}` | Used to read the diff and post the comment |
| `model` | no | `anthropic/claude-sonnet-5` | LiteLLM-style model string passed to CrewAI |

## How it works

1. Reads the PR's unified diff and changed-file list via the GitHub REST API (`src/pr_sentinel/github_client.py`).
2. Runs a two-agent, sequential [CrewAI](https://docs.crewai.com/) crew over that context (`src/pr_sentinel/crew.py`).
3. Posts the combined output as one PR comment.

## Development

Requires [uv](https://docs.astral.sh/uv/).

```bash
uv sync --all-extras --dev
uv run pytest --cov=pr_sentinel
uv run ruff check .
uv run mypy src
```

All tests mock the GitHub API (via `respx`) and CrewAI's `kickoff()` (via `unittest.mock`) — the suite never calls a real LLM or spends API credits. This repo's own `.github/workflows/self-review.yml` dogfoods the action on its own PRs, but only runs once an `ANTHROPIC_API_KEY` secret is added — no key, no cost, no failing CI in the meantime.

## Roadmap

- v1 (current): summary + risk/test-coverage comment
- v2: suggested test cases as a draft diff, not just a flag
