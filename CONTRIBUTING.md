# Contributing to BeliefSync

Thanks for considering a contribution.

## What We Need Most

The highest-value contributions right now are:

- real-world coding-agent integration feedback
- stale-belief failure cases
- repository event parsers
- better belief extraction heuristics
- learning-based stale-belief detectors
- evaluation harnesses and replay tooling

## Development Setup

### 1. Create a virtual environment

```bash
python -m venv .venv
```

### 2. Activate it

On Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

### 3. Install the project in editable mode

```bash
pip install -e .
```

### 4. Run tests

```bash
python -m unittest discover -s tests -t .
```

### 5. Try the demo

```bash
python -m beliefsync demo
```

## Design Boundaries

BeliefSync is not trying to be:

- a full coding agent
- a patch generation framework
- a general-purpose orchestration layer

BeliefSync is trying to be:

- a state layer
- a stale-belief detection layer
- a targeted recovery layer
