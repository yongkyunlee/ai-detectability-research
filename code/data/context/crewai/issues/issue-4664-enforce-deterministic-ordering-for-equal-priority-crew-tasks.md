# Enforce deterministic ordering for equal-priority crew tasks

**Issue #4664** | State: open | Created: 2026-03-01 | Updated: 2026-03-01
**Author:** davidahmann

## Problem
Equal-priority crew tasks can execute in non-deterministic order, which makes behavior and debugging inconsistent across runs.

## Why now
Reproducibility is essential for multi-agent workflows and regression triage.

## Current behavior is insufficient
Execution order for same-priority tasks lacks a locked deterministic tie-break contract.

## Expected behavior
Define and enforce deterministic task ordering for equal-priority tasks (for example stable insertion order or documented tie-break key).

## Acceptance / Validation
- Add/adjust execution ordering logic where needed.
- Add regression tests that run same-priority fixtures multiple times and assert identical order.
- Keep behavior scoped to equal-priority tie-break semantics.

## Evidence packet
- Commit under test: `1ac58015` (`origin/main`)
- Runtime environment: macOS arm64, Python `3.14.0`
- Minimal repro:
  1. Build crew with multiple same-priority tasks.
  2. Execute repeatedly under same seed/config.
  3. Observe task dispatch order.
- Expected: stable deterministic order.
- Actual: order contract is not explicitly guaranteed by tests.

## Likely codepaths
`lib/crewai/src/crewai/crews`, `lib/crewai/src/crewai/tasks`.
