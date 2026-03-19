# [BUG] TaskOutput.pydantic is None on first guardrail attempt but parsed on retries

**Issue #4369** | State: closed | Created: 2026-02-04 | Updated: 2026-03-17
**Author:** KGuzikowski
**Labels:** bug, no-issue-activity

### Description

When a task has a guardrail configured, `TaskOutput.pydantic` is None on the first guardrail invocation, but correctly parsed on retry attempts. This inconsistency makes it difficult to write guardrail functions that need to access the structured Pydantic output.

The root cause is in `task.py`:
- First attempt (lines 677-680): When guardrails exist, `_export_output()` is intentionally skipped, setting `pydantic_output = None`
- Retry attempts (line 1151): `_export_output()` is always called, properly parsing the Pydantic model
This creates inconsistent behavior where the same guardrail function receives different `TaskOutput` structures depending on whether it's the first or subsequent attempt.

### Steps to Reproduce

1. Create a Task with `output_pydantic` set to a Pydantic model
2. Add a guardrail function that accesses `task_output.pydantic`
3. Run the crew
4. Observe that on the first guardrail call, `task_output.pydantic` is `None`
5. Force a retry (return `False` from guardrail)
6. Observe that on subsequent calls, `task_output.pydantic` is correctly populated

### Expected behavior

`TaskOutput.pydantic` should be consistently parsed and available on all guardrail invocations, including the first attempt. The guardrail function should receive the same `TaskOutput` structure regardless of whether it's the first attempt or a retry.

### Screenshots/Code snippets

Minimal reproduction:
```
from crewai import Agent, Crew, Task, TaskOutput
from pydantic import BaseModel

class MyOutput(BaseModel):
    message: str
    status: str

def my_guardrail(task_output: TaskOutput) -> tuple[bool, TaskOutput]:
    print(f"Pydantic value: {task_output.pydantic}")  # None on first call!
    print(f"Raw value: {task_output.raw}")            # Has the JSON string
    
    if task_output.pydantic is None:
        # First attempt - pydantic not parsed!
        return False, "Pydantic was None"
    
    return True, task_output

agent = Agent(role="Test", goal="Test", backstory="Test")
task = Task(
    description="Return a message",
    expected_output="JSON with message and status",
    output_pydantic=MyOutput,
    guardrail=my_guardrail,
    agent=agent,
)
```

### Operating System

Ubuntu 24.04

### Python Version

3.12

### crewAI Version

1.9.3

### crewAI Tools Version

1.9.3

### Virtual Environment

Venv

### Evidence

First attempt (`_execute_core`, lines 677-680):
```
if not self._guardrails and not self._guardrail:
    pydantic_output, json_output = self._export_output(result)
else:
    pydantic_output, json_output = None, None  # ← SKIPPED!

task_output = TaskOutput(
    ...
    pydantic=pydantic_output,  # ← None on first attempt
    ...
)
```

Retry attempts (`_invoke_guardrail_function`, line 1151):
```
# After retry, parsing IS done:
pydantic_output, json_output = self._export_output(result)  # ← ALWAYS CALLED

task_output = TaskOutput(
    ...
    pydantic=pydantic_output,  # ← Properly parsed on retries
    ...
)
```

### Possible Solution

Remove the conditional skip of `_export_output()` on the first attempt. The parsing should always occur before the guardrail is invoked:
```
# Lines 677-680 should be changed from:
if not self._guardrails and not self._guardrail:
    pydantic_output, json_output = self._export_output(result)
else:
    pydantic_output, json_output = None, None

# To simply:
pydantic_output, json_output = self._export_output(result)
```

This ensures consistent behavior across all attempts and allows guardrail functions to reliably access the structured Pydantic output.

### Additional context

Additional Context:
- This inconsistency forces workarounds in guardrail functions, such as manually parsing `task_output.raw` with JSON on the first attempt
- The current behavior seems intentional (perhaps for performance?), but it breaks the contract that `output_pydantic` should provide structured access in guardrails
- Affects both single guardrail (`guardrail=`) and multiple guardrails (`guardrails=[]`) configurations
- The async version (`_ainvoke_guardrail_function`) likely has the same issue

## Comments

**Chase-Xuu:**
I've identified and fixed this issue. PR incoming!

**Root Cause:**
In both `_execute_core()` and `_aexecute_core()`, when guardrails are configured, `_export_output()` was intentionally skipped:

```python
if not self._guardrails and not self._guardrail:
    pydantic_output, json_output = self._export_output(result)
else:
    pydantic_output, json_output = None, None  # ← SKIPPED!
```

This meant `task_output.pydantic` was `None` on the first guardrail invocation. However, on retry attempts (inside `_invoke_guardrail_function`), `_export_output()` was always called, properly parsing the Pydantic model.

**Fix:**
Removed the conditional skip - `_export_output()` is now always called so that pydantic/json output is available to guardrails on the first attempt:

```python
# Always parse pydantic/json output so it's available to guardrails
pydantic_output, json_output = self._export_output(result)
```

**Testing:**
Added regression tests for both sync and async execution paths to ensure `TaskOutput.pydantic` is properly populated on the first guardrail invocation.

**github-actions[bot]:**
This issue is stale because it has been open for 30 days with no activity. Remove stale label or comment or this will be closed in 5 days.

**github-actions[bot]:**
This issue was closed because it has been stalled for 5 days with no activity.

**Jairooh:**
Shame this got closed without resolution — the `TaskOutput.pydantic` being `None` on the first guardrail attempt but populated on retries is a known timing issue in CrewAI where the output parsing pipeline hasn't fully materialized the Pydantic model before the guardrail callback fires. A reliable workaround is to check `task_output.raw` directly in your guardrail and manually invoke your Pydantic model's `.model_validate_json()` on it as a fallback when `.pydantic` is `None`. If you're still hitting this, dropping a minimal repro in a new issue with your CrewAI version and guardrail code would help get it triaged faster.
