# core: _parse_google_docstring mishandles continuation lines containing colons

**Issue #35679** | State: open | Created: 2026-03-09 | Updated: 2026-03-09
**Author:** alvinttang
**Labels:** external

## Bug Description

`_parse_google_docstring` in `langchain_core/utils/function_calling.py` incorrectly parses multi-line argument descriptions when a continuation line contains a colon. The continuation line is treated as a new argument definition instead of being appended to the current argument's description.

## Reproduction

```python
from langchain_core.utils.function_calling import _parse_google_docstring

def search(query: str, top_k: int = 5) -> str:
    """Search the knowledge base.

    Args:
        query: The search query to use
            for finding things: important ones
        top_k: Number of results to return
    """

result = _parse_google_docstring(search.__doc__, ["query", "top_k"])
print(result)
```

**Expected:** 2 args: `query` (description: "The search query to use for finding things: important ones"), `top_k`

**Actual:** 3 args: `query`, `for finding things` (treated as a new arg name), `top_k`

## Root Cause

The parser uses `if ":" in line` to detect new argument lines without considering indentation. In Google-style docstrings, continuation lines have deeper indentation than argument definition lines, but the parser doesn't distinguish between them.

## Proposed Fix

Detect the base indentation level from the first argument line and treat any line with deeper indentation as a continuation of the current argument's description, regardless of whether it contains a colon.
