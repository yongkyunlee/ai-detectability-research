# core, anthropic: bare raise ValueError provides no debugging context

**Issue #35727** | State: open | Created: 2026-03-10 | Updated: 2026-03-12
**Author:** alvinttang
**Labels:** external

**Description**

Several locations use bare `raise ValueError` without an error message, making it hard for users to understand what went wrong.

**Affected files**
- `libs/core/langchain_core/prompts/few_shot_with_templates.py` — missing examples/example_selector
- `libs/core/langchain_core/prompts/loading.py` — unsupported template file format
- `libs/core/langchain_core/document_loaders/langsmith.py` — conflicting client args
- `libs/partners/anthropic/langchain_anthropic/middleware/file_search.py` — malformed brace expansion

**Suggested fix**
Add descriptive error messages to each `raise ValueError` describing the condition that triggered it. No functional behavior change.

## Comments

**ajbermudezh22:**
Hi, I'd like to be assigned to this issue. I've already prepared a fix in #35792 that adds descriptive error messages to all the bare `raise ValueError` calls listed in the issue. Thanks\!
