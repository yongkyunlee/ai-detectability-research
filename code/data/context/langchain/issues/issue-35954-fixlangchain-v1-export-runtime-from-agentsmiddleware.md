# fix(langchain_v1): export Runtime from agents.middleware

**Issue #35954** | State: closed | Created: 2026-03-16 | Updated: 2026-03-16
**Author:** november-pain
**Labels:** external

### Checked other resources

- [x] This is a bug, not a usage question.
- [x] I added a clear and descriptive title that summarizes this issue.
- [x] I used the GitHub search to find a similar question and didn't find it.
- [x] I am sure that this is a bug in LangChain rather than my code.
- [x] The bug is not resolved by updating to the latest stable version of LangChain (or the specific integration package).
- [x] This is not related to the langchain-community package.
- [x] I read what a minimal reproducible example is (https://stackoverflow.com/help/minimal-reproducible-example).
- [x] I posted a self-contained, minimal, reproducible example. A maintainer can copy it and run it AS IS.

### Example Code

### ❌ **Code that FAILS**

```python
from langchain.agents.middleware import after_model, AgentState, Runtime
# ImportError: cannot import name 'Runtime' from 'langchain.agents.middleware'
```

### ✅ **Code that WORKS** (workaround)

```python
from langgraph.runtime import Runtime  # direct import works
```

### Error Message and Stack Trace (if applicable)

```
Traceback (most recent call last):
  File "", line 1, in 
ImportError: cannot import name 'Runtime' from 'langchain.agents.middleware'
```

### Description

`Runtime` (from `langgraph.runtime`) is used in `after_model` callback signatures (`state: AgentState, runtime: Runtime`) but is not exported from `langchain.agents.middleware`.

Users implementing `@after_model` hooks need `Runtime` for the type annotation but must know to import it from `langgraph.runtime` directly — the natural import path `langchain.agents.middleware` doesn't re-export it.

This is the same class of issue as #33453 (which was about `ModelResponse`), fixed in #33454.

### Root Cause

`Runtime` is already imported at runtime in multiple middleware modules (`human_in_the_loop.py`, `summarization.py`), so there is no circular import concern. It is simply missing from the import list and `__all__` in `langchain/agents/middleware/__init__.py`.

### Suggested Fix

Add `from langgraph.runtime import Runtime` and `"Runtime"` to `__all__` in `langchain/agents/middleware/__init__.py`.

### System Info

```
System Information
------------------
> OS:  Darwin
> OS Version:  24.6.0
> Python Version:  3.11.9

Package Information
-------------------
> langchain_core: 0.3.78
> langchain: 0.3.27
> langsmith: 0.4.32
> pydantic: 2.11.9
```

## Comments

**november-pain:**
Closing to recreate via the bug report template for proper labeling.
