# Architecture

## Project Goal

BeliefSync adds a repository-state belief layer to coding agents.

Instead of relying on prompt history alone, it tracks what the agent currently believes about:

- likely bug locations
- API contracts
- test expectations
- repository requirements
- dependency relationships

## High-Level Flow

```text
Repository events
   |
   v
Belief Constructor ---> Belief Store
                           |
                           v
                  Stale Belief Detector
                           |
                           v
                   Revalidation Planner
                           |
                           v
                       Task Agent
```

## Main Components

### `models.py`

Defines the core domain model:

- beliefs
- evidence references
- scope
- version validity
- change events
- revalidation actions

### `store.py`

Persists beliefs and reports as JSON.

### `extractors.py`

Builds initial beliefs from issue text and test logs.

### `detector.py`

Scores beliefs against repository events and marks them active or stale-suspected.

### `planner.py`

Turns stale beliefs into targeted recovery actions.

### `engine.py`

Combines extraction, detection, and planning into one workflow.

### `adapters/`

Integration points for coding-agent frameworks.
