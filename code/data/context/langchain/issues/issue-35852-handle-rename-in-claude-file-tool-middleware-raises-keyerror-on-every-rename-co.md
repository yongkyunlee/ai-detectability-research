# _handle_rename in Claude file tool middleware raises KeyError on every rename command

**Issue #35852** | State: open | Created: 2026-03-13 | Updated: 2026-03-18
**Author:** keenborder786
**Labels:** bug, anthropic, external, trusted-contributor

### Checked other resources

- [x] This is a bug, not a usage question.
- [x] I added a clear and descriptive title that summarizes this issue.
- [x] I used the GitHub search to find a similar question and didn't find it.
- [x] I am sure that this is a bug in LangChain rather than my code.
- [x] The bug is not resolved by updating to the latest stable version of LangChain (or the specific integration package).
- [x] This is not related to the langchain-community package.
- [x] I posted a self-contained, minimal, reproducible example. A maintainer can copy it and run it AS IS.

### Package (Required)

- [ ] langchain
- [ ] langchain-openai
- [x] langchain-anthropic
- [ ] langchain-classic
- [ ] langchain-core
- [ ] langchain-model-profiles
- [ ] langchain-tests
- [ ] langchain-text-splitters
- [ ] langchain-chroma
- [ ] langchain-deepseek
- [ ] langchain-exa
- [ ] langchain-fireworks
- [ ] langchain-groq
- [ ] langchain-huggingface
- [ ] langchain-mistralai
- [ ] langchain-nomic
- [ ] langchain-ollama
- [ ] langchain-openrouter
- [ ] langchain-perplexity
- [ ] langchain-qdrant
- [ ] langchain-xai
- [ ] Other / not sure / general

### Related Issues / PRs

_No response_

### Reproduction Steps / Example Code (Python)

```python
from langchain_anthropic.middleware.anthropic_tools import (
    StateClaudeTextEditorMiddleware,
    AnthropicToolsState,
)

middleware = StateClaudeTextEditorMiddleware()

# Simulate the args dict as built internally by the tool dispatch (line 218)
# The dispatch puts the source path under key "path", not "old_path"
args = {"path": "old_name.txt", "new_path": "new_name.txt"}

state: AnthropicToolsState = {
    "messages": [],
    "text_editor_files": {
        "old_name.txt": {"content": "hello", "modified_at": "2024-01-01T00:00:00+00:00"}
    },
}

# This raises KeyError: 'old_path'
middleware._handle_rename(args, state, tool_call_id="abc123")
```

### Error Message and Stack Trace (if applicable)

```shell
File "/Users/mohtashim/langchain/test.py", line 70, in 
    middleware._handle_rename(args, state, tool_call_id="abc123")
  File "/Users/mohtashim/langchain/libs/partners/anthropic/langchain_anthropic/middleware/anthropic_tools.py", line 533, in _handle_rename
    old_path = args["old_path"]
               ~~~~^^^^^^^^^^^^
KeyError: 'old_path'
```

### Description

- I'm trying to use `StateClaudeFileToolMiddleware` (or `FilesystemClaudeTextEditorMiddleware`) and ask Claude to rename a file.
- I expect the file to be renamed and a success `ToolMessage` to be returned.
- Instead, it raises `KeyError: 'old_path'` every single time the `rename` command is invoked.

The bug is in both `_StateClaudeFileToolMiddleware._handle_rename` (line 533) and `_FilesystemClaudeFileToolMiddleware._handle_rename` (line 1035) in `middleware/anthropic_tools.py`.

The tool dispatch function builds the `args` dict with the source path stored under the key `"path"`:

```python
# line 218 in anthropic_tools.py
args: dict[str, Any] = {"path": path}
```

But both `_handle_rename` implementations read it as `args["old_path"]`, which never exists. The fix is a one-line change in both methods:

```python
# Before (broken):
old_path = args["old_path"]

# After (correct):
old_path = args["path"]
```
Please assign this issue to me so I can patch a fix for it.

### System Info

System Information
------------------
> OS:  Darwin
> OS Version:  Darwin Kernel Version 24.5.0: Tue Apr 22 19:54:29 PDT 2025; root:xnu-11417.121.6~2/RELEASE_ARM64_T6030
> Python Version:  3.11.11 (main, Feb  5 2025, 18:58:27) [Clang 19.1.6 ]

Package Information
-------------------
> langchain_core: 1.2.17
> langchain: 1.2.10
> langsmith: 0.6.3
> langchain_anthropic: 1.3.4
> langchain_tests: 1.1.5
> langgraph_sdk: 0.3.3

Optional packages not installed
-------------------------------
> deepagents
> deepagents-cli

Other Dependencies
------------------
> anthropic: 0.78.0
> httpx: 0.28.1
> jsonpatch: 1.33
> langgraph: 1.0.8
> numpy: 2.3.5
> orjson: 3.11.5
> packaging: 25.0
> pydantic: 2.12.4
> pytest: 7.4.4
> pytest-asyncio: 0.23.8
> pytest-benchmark: 5.0.1
> pytest-codspeed: 4.2.0
> pytest-recording: 0.13.4
> pytest-socket: 0.7.0
> pyyaml: 6.0.3
> requests: 2.32.5
> requests-toolbelt: 1.0.0
> rich: 14.2.0
> syrupy: 4.9.1
> tenacity: 9.1.2
> typing-extensions: 4.15.0
> uuid-utils: 0.12.0
> vcrpy: 8.1.1
> zstandard: 0.25.0

## Comments

**gitbalaji:**
Hi, I'd like to work on this. Could a maintainer please assign it to me?

**keenborder786:**
Hi @gitbalaji, thanks for your interest! I have already identified the fix, it's a straightforward one-line change in both _handle_rename methods. I'd love to take this one since I have full context on the bug. I've already requested assignment from a maintainer above.

**passionworkeer:**
PR opened: https://github.com/langchain-ai/langchain/pull/35886

The fix changes args old_path to args path in both _handle_rename implementations, since the tool dispatch builds args with the path key.

**passionworkeer:**
This is a clear bug with a straightforward fix! The issue is that _handle_rename tries to read args[old_path] but the dispatch function actually stores it under args[path]. Happy to submit a PR to fix this.

**passionworkeer:**
Hi, I'd like to work on this issue. Could you please assign it to me? I've already prepared a fix in PR #35891.

**passionworkeer:**
Could you please assign this issue to me? I have a fix ready in PR #35891 that addresses this bug (the _handle_rename methods incorrectly use args['old_path'] but the dispatch function stores the source path under args['path']).

**passionworkeer:**
I'd like to work on this fix. The issue is clear: both `_handle_rename` implementations use `args[old_path]` but the tool dispatch actually passes `args[path]`.   I'll submit a PR with the fix (changing `args[old_path]` to `args[path]` in both methods). Please assign this to me.

**passionworkeer:**
Hi maintainers, I'd like to work on this bug. The fix is ready in PR #35891 (which was auto-closed due to the require-issue-link rule). Could you please assign me to this issue so I can reopen the PR? Thanks!

**passionworkeer:**
Hi! I'd like to work on this issue. I already have a fix ready in PR #35891. Could you please assign this issue to me?

**gitbalaji:**
Hi @keenborder786 — no worries, happy to collaborate! Just wanted to mention that I already have a fix ready on branch `fix/anthropic-handle-rename-keyerror` and am all set to open a PR as soon as a maintainer assigns me. Whoever gets assigned, hope we get this fixed quickly for the community!
