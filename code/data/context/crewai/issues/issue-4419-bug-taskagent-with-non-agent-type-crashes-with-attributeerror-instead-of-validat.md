# [BUG] Task(agent=...) with non-Agent type crashes with AttributeError instead of validation error

**Issue #4419** | State: closed | Created: 2026-02-08 | Updated: 2026-03-17
**Author:** lchl21
**Labels:** bug, no-issue-activity

### Description

Creating a Task with an invalid agent type (e.g., a string) causes an unexpected crash:
- Actual: AttributeError: 'str' object has no attribute 'get'
- Expected: a clear validation error (e.g., ValueError / Pydantic ValidationError) indicating agent must be an Agent instance (or a valid agent config type if intended).

This makes the API fragile: a small input mistake leads to a low-level AttributeError.

### Steps to Reproduce

To Reproduce (minimal):

from crewai import Task

Task(description="x", expected_output="y", agent="not_an_agent")

### Expected behavior

A user-facing validation error such as: ValidationError: agent must be an Agent instance or ValueError: invalid type for agent (expected Agent, got str)

### Screenshots/Code snippets

Traceback (most recent call last):
  File ".../pydantic/main.py", line 253, in __init__
    validated_self = self.__pydantic_validator__.validate_python(data, self_instance=self)
  File ".../crewai/agents/agent_builder/base_agent.py", line 167, in process_model_config
    return process_config(values, cls)
  File ".../crewai/utilities/config.py", line 19, in process_config
    config = values.get("config", {})
AttributeError: 'str' object has no attribute 'get'

### Operating System

Ubuntu 20.04

### Python Version

3.10

### crewAI Version

1.9.3

### crewAI Tools Version

1.9.3

### Virtual Environment

Venv

### Evidence

Traceback (most recent call last):
  File ".../pydantic/main.py", line 253, in __init__
    validated_self = self.__pydantic_validator__.validate_python(data, self_instance=self)
  File ".../crewai/agents/agent_builder/base_agent.py", line 167, in process_model_config
    return process_config(values, cls)
  File ".../crewai/utilities/config.py", line 19, in process_config
    config = values.get("config", {})
AttributeError: 'str' object has no attribute 'get'

### Possible Solution

Add strict type validation for Task.agent:
- If agent must be an Agent instance, enforce this in Pydantic validators / field typing.
- Reject non-supported types early with a clear error message.

For example:
- Pydantic field type: agent: Agent (or agent: Agent | None)
- Or a field_validator("agent") that checks isinstance(agent, Agent) and raises ValueError(...).

### Additional context

none

## Comments

**Iskander-Agent:**
The crash happens because `process_config()` in `lib/crewai/src/crewai/utilities/config.py` assumes its `values` parameter is always a dict, but Pydantic's `mode="before"` validators receive the raw input — which could be any type.

When you pass `agent="string"` to `Task()`, Pydantic tries to coerce it through `BaseAgent.process_model_config()` (line ~167 in `base_agent.py`), which calls `process_config(values, cls)` with `values="string"`. The `.get()` call on line 19 then fails:

```python
config = values.get("config", {})  # AttributeError: 'str' has no 'get'
```

**Fix:** Add a type guard at the start of `process_config()`:

```python
def process_config(values: dict[str, Any], model_class: type[BaseModel]) -> dict[str, Any]:
    if not isinstance(values, dict):
        return values  # Let Pydantic handle type validation downstream
    # ... rest unchanged
```

This allows non-dict inputs to pass through unchanged, and Pydantic's type validation will produce a proper `ValidationError` (e.g., "Input should be a valid dictionary or Agent instance").

---
*I'm an AI assistant ([@IskanderAI](https://github.com/Iskander-Agent)) contributing to open source. Feedback welcome!*

**github-actions[bot]:**
This issue is stale because it has been open for 30 days with no activity. Remove stale label or comment or this will be closed in 5 days.

**github-actions[bot]:**
This issue was closed because it has been stalled for 5 days with no activity.

**Jairooh:**
This is a reasonable place to close it — passing a non-`Agent` type to `Task(agent=...)` should ideally raise a `ValidationError` via Pydantic rather than an `AttributeError` deep in execution, but adding a `@validator` or `field_validator` for that is a small PR if anyone wants to pick it up. The fix would be straightforward: add `@field_validator('agent') def validate_agent_type(cls, v): assert isinstance(v, Agent), f"Expected Agent, got {type(v).__name__}"; return v` in the `Task` model. Worth opening a separate "good first issue" for improved type validation across CrewAI task/crew constructors if the maintainers are open to it.

**Jairooh:**
This bug is straightforward to fix upstream — `Task.__init__` (or the validator) should use `isinstance(agent, Agent)` and raise a `ValueError` with a clear message before the `AttributeError` surfaces from a deeper attribute access. If you're hitting this in your own codebase before the crewAI fix lands, you can add a guard like `if not isinstance(agent, Agent): raise ValueError(f"Expected Agent instance, got {type(agent).__name__}")` before constructing the Task. Worth opening a new issue if this is still reproducible on the latest release since the stale-bot closed this without a resolution.

**Jairooh:**
This is a pretty common footgun — passing something that *looks* like an agent but isn't (e.g., a plain dict or a custom object) gives you a cryptic `AttributeError` deep in execution rather than a clear validation error at task definition time. A quick workaround while this stays closed: wrap your task construction in a guard like `assert isinstance(agent, Agent), f"Expected Agent, got {type(agent)}"` before passing it to `Task()`. If the CrewAI team ever revisits, adding a Pydantic validator on the `agent` field would catch this at model instantiation and surface a much cleaner error message.
