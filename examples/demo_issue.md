# Issue: retry state is not reset after a failed request

The retry manager should clear transient request state before a new retry cycle begins.

Observed behavior:

- after a failed request, a new retry cycle reuses the previous backoff state
- this causes later retries to exceed the expected limit

Likely affected area:

- `RetryManager`
- `reset_retry_state`
- `src/retry_manager.py`
