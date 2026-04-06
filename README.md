# BeliefSync

BeliefSync is a repository-state belief and sync layer for coding agents.

It helps agents stay reliable in dynamic repositories by turning implicit assumptions into explicit, version-scoped beliefs that can be checked, invalidated, and revalidated when the repository changes.

## Why BeliefSync

Coding agents are strong at localized patch generation, but they still break when the environment moves underneath them:

- a commit lands while the agent is planning a fix
- a test starts checking a different requirement
- an issue comment adds a new constraint
- a dependency bump invalidates an earlier hypothesis

Most agent stacks respond by rescanning more context. BeliefSync takes a different approach:

1. represent what the agent currently believes about the repository
2. attach evidence and version validity to each belief
3. detect which beliefs have likely gone stale
4. plan the cheapest high-value revalidation actions

That makes BeliefSync useful both as:

- a reliability layer for coding agents
- a debugging and introspection tool for agent failures
- a foundation for future stale-belief research

## Core Ideas

- `Repository-State Beliefs`
  - structured claims about the current state of the repository
- `Version Validity`
  - beliefs know when and where they were last valid
- `Stale Belief Detection`
  - repository updates are mapped to potentially invalidated beliefs
- `Targeted Revalidation`
  - instead of brute-force rescans, BeliefSync suggests focused actions such as reading a file, rerunning a test, or checking a specific comment

## What Ships in This Repository

- a lightweight Python package with no third-party runtime dependencies
- a CLI for extracting beliefs, detecting stale beliefs, and planning revalidation
- git-diff ingestion for repository change events
- one-shot repository scans that emit JSON, text, and Markdown reports
- optional OpenAI-compatible LLM support, including Kimi-compatible smoke testing and belief extraction
- a JSON-backed belief store
- a rule-based baseline implementation you can extend into a learned system
- adapter interfaces for coding-agent integration
- examples, tests, architecture docs, and open-source scaffolding

## Quick Start

### Install in editable mode

```bash
pip install -e .
```

### Run the demo

```bash
python -m beliefsync demo
```

### Initialize a local workspace

```bash
python -m beliefsync init
```

### Show workspace status

```bash
python -m beliefsync status
```

### Show active config

```bash
python -m beliefsync show-config
```

### Create a baseline snapshot

```bash
python -m beliefsync snapshot ^
  --repo-id demo/repo ^
  --repo-path . ^
  --issue-file examples/demo_issue.md ^
  --test-log examples/demo_test_log.txt
```

### Test a Kimi/OpenAI-compatible API connection

Set one of these environment variable sets first:

- `BELIEFSYNC_LLM_API_KEY`, `BELIEFSYNC_LLM_BASE_URL`, `BELIEFSYNC_LLM_MODEL`
- or `KIMI_API_KEY`, `KIMI_BASE_URL`, `KIMI_MODEL`

You can start from `.env.example`.

Then run:

```bash
python -m beliefsync llm-smoke-test
```

### Extract candidate beliefs with an LLM

```bash
python -m beliefsync llm-extract ^
  --repo-id demo/repo ^
  --issue-file examples/demo_issue.md ^
  --test-log examples/demo_test_log.txt ^
  --output .beliefsync/llm_beliefs.json
```

### Extract beliefs from issue and test inputs

```bash
python -m beliefsync extract ^
  --repo-id demo/repo ^
  --issue-file examples/demo_issue.md ^
  --test-log examples/demo_test_log.txt ^
  --output .beliefsync/beliefs.json
```

### Detect stale beliefs

```bash
python -m beliefsync detect ^
  --beliefs-file .beliefsync/beliefs.json ^
  --events-file examples/demo_events.json
```

### Plan targeted revalidation actions

```bash
python -m beliefsync plan ^
  --beliefs-file .beliefsync/beliefs.json ^
  --events-file examples/demo_events.json
```

### Ingest repository changes directly from git

```bash
python -m beliefsync ingest-git ^
  --repo-path . ^
  --base-ref HEAD~1 ^
  --head-ref HEAD ^
  --output .beliefsync/events.json
```

### Run a one-shot scan

```bash
python -m beliefsync scan ^
  --repo-id demo/repo ^
  --repo-path . ^
  --issue-file examples/demo_issue.md ^
  --test-log examples/demo_test_log.txt ^
  --base-ref HEAD~1 ^
  --head-ref HEAD ^
  --output-dir .beliefsync/scan-001
```

### Refresh from the latest workspace snapshot

```bash
python -m beliefsync refresh ^
  --repo-path . ^
  --head-ref HEAD ^
  --format markdown
```

## Example Output

```text
Detected 3 potentially stale beliefs.
Top revalidation actions:
1. run_targeted_test: tests/test_retry.py::test_retry_resets_state
2. read_file: src/retry_manager.py
3. read_issue_comment: demo-issue-1
```

## Project Layout

```text
beliefsync/
  .github/
  docs/
  examples/
  src/beliefsync/
  tests/
  README.md
  pyproject.toml
```

## Design Principles

- `Agent-agnostic`
  - BeliefSync should work with multiple coding-agent stacks.
- `Explicit over implicit`
  - assumptions should be inspectable, not buried in prompt history.
- `Cheap to adopt`
  - the baseline should run with standard Python only.
- `Project-first, research-ready`
  - the repo should be useful in practice while remaining structured enough for future paper work.

## Current Scope

BeliefSync currently ships a strong baseline implementation:

- belief extraction from issue text and test logs
- JSON belief persistence
- rule-based stale belief scoring
- cost-aware targeted revalidation planning
- git-based repository event ingestion
- text, JSON, and Markdown report generation

The next major milestones are:

- git-native diff ingestion
- richer symbol-level scope extraction
- learning-based stale-belief detectors
- OpenHands and SWE-agent adapters
- telemetry and replay tools for long-horizon coding sessions

See [ROADMAP.md](ROADMAP.md) and [docs/architecture.md](docs/architecture.md).

## CLI Overview

```text
python -m beliefsync init
python -m beliefsync status
python -m beliefsync show-config
python -m beliefsync snapshot
python -m beliefsync refresh
python -m beliefsync llm-smoke-test
python -m beliefsync llm-extract
python -m beliefsync demo
python -m beliefsync extract
python -m beliefsync detect
python -m beliefsync plan
python -m beliefsync report
python -m beliefsync ingest-git
python -m beliefsync scan
python -m beliefsync validate-beliefs
python -m beliefsync validate-events
```

## Integrating with a Coding Agent

BeliefSync can be inserted into a coding workflow like this:

1. the agent forms working hypotheses while reading the repository
2. BeliefSync stores those hypotheses as structured beliefs
3. repository updates arrive
4. BeliefSync marks stale beliefs
5. BeliefSync recommends targeted recovery actions
6. the agent resumes coding with a cleaner state

For more details, see [docs/integration.md](docs/integration.md).

## Documentation

- [Architecture](docs/architecture.md)
- [Integration Guide](docs/integration.md)
- [CLI Guide](docs/cli.md)
- [Belief Model](docs/belief_model.md)
- [Roadmap](ROADMAP.md)
- [Changelog](CHANGELOG.md)

## Kimi / OpenAI-Compatible Support

BeliefSync can optionally use an OpenAI-compatible API for smoke testing and richer belief extraction.

By default, if you only set `KIMI_API_KEY`, BeliefSync assumes:

- `KIMI_BASE_URL=https://api.moonshot.cn/v1`
- `KIMI_MODEL=moonshot-v1-8k`

You can override those with:

- `BELIEFSYNC_LLM_API_KEY`
- `BELIEFSYNC_LLM_BASE_URL`
- `BELIEFSYNC_LLM_MODEL`

## Open Source Readiness

This repository includes:

- CI
- issue templates
- contribution guide
- code of conduct
- tests
- example data
- architecture docs

## License

MIT. See [LICENSE](LICENSE).

## Status

BeliefSync is in early public development, but the repository is intentionally structured to become:

- a usable open-source reliability layer for coding agents
- a benchmark and experimentation harness for dynamic repository state tracking
- a foundation for future stale-belief research
