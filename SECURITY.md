# Security Policy

## Scope

BeliefSync is an early-stage open-source developer tool. Security reports are especially helpful when they relate to:

- command execution risks
- unsafe handling of repository paths
- unexpected file writes
- malformed event ingestion
- adapter integrations that may expose sensitive repository data

## Reporting

Please report security issues privately to the maintainers instead of opening a public issue.

## Expectations

BeliefSync is designed to inspect and analyze repository state. It should not:

- upload repository contents by default
- execute arbitrary shell commands from untrusted event files
- mutate repositories during read-only analysis commands

If you discover behavior that violates those expectations, please report it.
