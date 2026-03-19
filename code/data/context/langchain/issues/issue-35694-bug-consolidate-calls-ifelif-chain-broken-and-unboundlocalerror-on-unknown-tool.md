# Bug: _consolidate_calls if/elif chain broken and UnboundLocalError on unknown tool names

**Issue #35694** | State: open | Created: 2026-03-09 | Updated: 2026-03-11
**Author:** umut-polat
**Labels:** external

### Checked other resources

- [x] I searched existing issues
- [x] I searched the LangChain documentation
- [x] I searched the LangChain discussion forum

### Example Code

```python
# in libs/partners/openai/langchain_openai/chat_models/_compat.py
# _consolidate_calls function
```

### Description

Two issues in `_consolidate_calls`:

1. the `file_search` branch uses a bare `if` instead of `elif`, so it's evaluated even after `web_search` already matched — and the downstream `elif`/`else` chain attaches to `file_search` rather than the full dispatch.

2. when a `server_tool_call` has a name that doesn't match any known tool (`web_search`, `file_search`, `code_interpreter`, etc.), the `else` branch does `pass` and falls through to `yield collapsed` where `collapsed` was never assigned, causing an `UnboundLocalError`.

### System Info

langchain-openai latest

## Comments

**umut-polat:**
hey, i opened this issue along with a fix in #35482 — could i get assigned?

**NIK-TIGER-BILL:**
Hi! I have identified and fixed both issues described here:

1. The `file_search` branch uses a bare `if` instead of `elif` — this breaks the dispatch chain so `code_interpreter`, `remote_mcp`, and `mcp_list_tools` branches become unreachable when `web_search` matches.
2. The `else: pass` branch causes `UnboundLocalError: local variable 'collapsed' referenced before assignment` for unknown tool names.

I have a ready fix in my fork ([branch here](https://github.com/NIK-TIGER-BILL/langchain/tree/fix/consolidate-calls-v2)). Could a maintainer please assign me to this issue so I can reopen the PR? Thank you!

**saschabuehrle:**
Repro makes sense. A defensive fallback path for unknown tool names would help here so consolidation does not enter branches with uninitialized locals.\n\nA regression test with one valid tool call plus one unknown tool call in the same response could verify deterministic behavior and clearer error surfacing.

**mvanhorn:**
I've submitted a fix for this in PR #35741. Changed the bare `if` to `elif` on the `file_search` branch and added proper handling for unknown tool names in the `else` branch to prevent the `UnboundLocalError`.

**mvanhorn:**
I'd like to work on this issue. Could I be assigned?
