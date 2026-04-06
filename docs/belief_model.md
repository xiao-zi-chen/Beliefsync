# Belief Model

## What a Belief Represents

A BeliefSync belief is a structured claim about the current state of a repository.

Each belief should answer:

- what the agent currently believes
- where that belief applies
- what evidence supports it
- under what repository version it was last known to be valid

## Core Belief Types

- `bug_localization`
- `api_contract`
- `test_expectation`
- `requirement`
- `dependency`

## Why This Matters

The core idea behind BeliefSync is that agent failures in dynamic repositories often come from stale assumptions, not only missing context.

That means a useful state layer must model:

- the belief itself
- the evidence behind it
- the repository region it touches
- the events that may invalidate it
