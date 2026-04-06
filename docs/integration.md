# Integration Guide

## BeliefSync in a Coding-Agent Loop

BeliefSync works best as a sidecar layer around an existing coding agent.

## Recommended Integration Pattern

1. Agent reads issue and repository context.
2. Agent or wrapper emits candidate beliefs.
3. BeliefSync stores beliefs with scope, evidence, and version metadata.
4. New repository events arrive.
5. BeliefSync detects stale beliefs.
6. BeliefSync recommends low-cost revalidation actions.
7. Agent resumes coding with updated state.

## Minimal Integration

You can integrate BeliefSync even if your agent does not emit structured traces yet.

Start with:

- issue text
- failing test logs
- changed file paths
- recent comments

## Suggested Adapter Responsibilities

An adapter should:

- translate agent observations into `Belief` objects
- translate repository updates into `ChangeEvent` objects
- feed stale-belief reports back into the agent
