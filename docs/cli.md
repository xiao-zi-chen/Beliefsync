# CLI Guide

## Commands

### `beliefsync init`

Initialize a `.beliefsync/` workspace in a repository.

### `beliefsync demo`

Run the bundled demo using example issue, test log, and repository events.

### `beliefsync extract`

Extract beliefs from issue and test inputs and write them to JSON.

### `beliefsync detect`

Run stale-belief detection over a belief file and an event file.

### `beliefsync plan`

Produce targeted revalidation actions from beliefs and events.

### `beliefsync report`

Generate a combined report in text, JSON, or Markdown.

### `beliefsync ingest-git`

Turn a git diff between two revisions into BeliefSync `ChangeEvent` objects.

### `beliefsync scan`

One-shot workflow:

1. extract beliefs from issue and test data
2. ingest repository change events from git
3. optionally merge additional external events
4. run stale-belief detection
5. plan targeted revalidation
6. emit a Markdown report

### `beliefsync snapshot`

Create a baseline workspace snapshot:

- extract beliefs from issue and test inputs
- save them to `.beliefsync/beliefs.json`
- record repository path and head ref in `.beliefsync/state.json`

### `beliefsync refresh`

Use the latest workspace snapshot as the baseline belief state, compare it against new repository events, emit reports, and refresh the stored baseline for the next cycle.

### `beliefsync llm-smoke-test`

Run a minimal OpenAI-compatible API smoke test.

BeliefSync reads credentials only from environment variables:

- `BELIEFSYNC_LLM_API_KEY` or `KIMI_API_KEY`
- `BELIEFSYNC_LLM_BASE_URL` or `KIMI_BASE_URL`
- `BELIEFSYNC_LLM_MODEL` or `KIMI_MODEL`

### `beliefsync llm-extract`

Use an OpenAI-compatible LLM to extract structured candidate beliefs from issue text and test logs.

### `beliefsync status`

Show whether a `.beliefsync/` workspace exists and summarize local workspace state.

### `beliefsync show-config`

Print the active config.

Config resolution order:

1. explicit `--config-file`
2. nearest `.beliefsync/config.json`
3. default built-in config

### `beliefsync validate-beliefs`

Validate a belief JSON file and report structural issues.

### `beliefsync validate-events`

Validate an event JSON file and report structural issues.

## Example

```bash
beliefsync scan ^
  --repo-id my/repo ^
  --repo-path . ^
  --issue-file issue.md ^
  --test-log failing_tests.txt ^
  --base-ref HEAD~1 ^
  --head-ref HEAD ^
  --output-dir .beliefsync\scan-001
```
