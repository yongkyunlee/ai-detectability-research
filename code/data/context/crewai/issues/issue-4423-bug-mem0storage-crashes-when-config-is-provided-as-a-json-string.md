# [BUG] Mem0Storage crashes when config is provided as a JSON string

**Issue #4423** | State: closed | Created: 2026-02-09 | Updated: 2026-03-17
**Author:** ChenglinLi21
**Labels:** bug, no-issue-activity

### Description

Hi! I ran into a crash when using Mem0Storage with an external config. This is a pretty common situation in real projects, since configs are often loaded from: environment variables, config files, CLI arguments which are usually strings.

### Steps to Reproduce

Here is a simple way to reproduce this crash:

from crewai.memory.storage.mem0_storage import Mem0Storage

config = '{"agent_id":"agent-123","user_id":"user-123"}'

Mem0Storage(
    type="external",
    config=config,
)

### Expected behavior

One of the following would be much clearer / safer:
Automatically parse JSON strings (e.g. json.loads(config)), or
Raise a clear error early, e.g.
TypeError: config must be a dict, got str

Right now the raw AttributeError is a bit confusing for users.

### Screenshots/Code snippets

### Operating System

macOS Sonoma

### Python Version

3.10

### crewAI Version

1.9.3

### crewAI Tools Version

mem0ai-1.0.3

### Virtual Environment

Venv

### Evidence

Traceback (most recent call last):
  File "/Users/macbook/wlnwun3/mem0_config.py", line 30, in 
    main()
    ~~~~^^
  File "/Users/macbook/wlnwun3/mem0_config.py", line 26, in main
    Mem0Storage(type="external", config=config_raw)
    ~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Users/macbook/miniconda3/lib/python3.13/site-packages/crewai/memory/storage/mem0_storage.py", line 29, in __init__
    self._extract_config_values()
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~^^
  File "/Users/macbook/miniconda3/lib/python3.13/site-packages/crewai/memory/storage/mem0_storage.py", line 41, in _extract_config_values
    self.mem0_run_id = self.config.get("run_id")
                       ^^^^^^^^^^^^^^^
AttributeError: 'str' object has no attribute 'get'

### Possible Solution

In Mem0Storage.__init__ or _extract_config_values(): Check isinstance(config, str) and try json.loads or validate type and raise a friendly error

Happy to help test a fix if needed. Thanks for the great project! 🙌

### Additional context

-

## Comments

**Chase-Xuu:**
I've identified and fixed this issue. PR incoming!

**Root Cause:**
The `Mem0Storage.__init__` method stores `config` directly and then calls `_extract_config_values()` which uses `self.config.get()`. When `config` is a JSON string, `.get()` fails because strings don't have that method.

**Fix:**
Added a `_parse_config()` method that:
1. Returns `{}` for `None`
2. Passes through dicts unchanged
3. Parses JSON strings using `json.loads()`
4. Raises a clear `TypeError` with helpful messages for invalid inputs

This handles the common case where configs are loaded from environment variables or config files as strings.

**github-actions[bot]:**
This issue is stale because it has been open for 30 days with no activity. Remove stale label or comment or this will be closed in 5 days.

**github-actions[bot]:**
This issue was closed because it has been stalled for 5 days with no activity.

**Jairooh:**
This issue got auto-closed but the bug is still valid — `Mem0Storage` likely expects a dict for the config param but doesn't deserialize the string before passing it to the `Memory` client, so a quick workaround is to manually parse it with `json.loads()` before passing config to your crew. If you're still hitting this, it's worth reopening with a minimal repro and tagging it as a regression so it gets prioritized.

**Jairooh:**
This issue being closed as "not planned" is a bit frustrating when it's a clear config parsing bug — if you still need a workaround, you can deserialize the JSON string manually before passing it to `Mem0Storage` by wrapping it with `json.loads()` in your crew setup code. Alternatively, checking whether the config value is a string instance and parsing it conditionally in your initialization logic should sidestep the crash entirely.

**Jairooh:**
This issue got auto-closed but the underlying bug is worth fixing — `Mem0Storage` should handle JSON string configs by deserializing them before passing to the Mem0 client, likely with a `json.loads()` check in the constructor (e.g., `if isinstance(config, str): config = json.loads(config)`). If you're still hitting this, you can reopen or submit a minimal reproduction so the maintainers can pick it up — stale-bot closures don't mean the bug is resolved.
