# ModelRequest.override(messages=...) rejects list[BaseMessage] due to list invariance

**Issue #35971** | State: open | Created: 2026-03-16 | Updated: 2026-03-18
**Author:** november-pain
**Labels:** bug, langchain, external

### Checked other resources

- [x] This is a bug, not a usage question.
- [x] I added a clear and descriptive title that summarizes this issue.
- [x] I used the GitHub search to find a similar question and didn't find it.
- [x] I am sure that this is a bug in LangChain rather than my code.
- [x] The bug is not resolved by updating to the latest stable version of LangChain (or the specific integration package).
- [x] This is not related to the langchain-community package.
- [x] I posted a self-contained, minimal, reproducible example. A maintainer can copy it and run it AS IS.

### Package (Required)

- [x] langchain
- [ ] langchain-openai
- [ ] langchain-anthropic
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

#35429 - same `list` invariance problem for `_InputAgentState.messages`
#33732 - `list` invariance in `AgentMiddleware` state typing

### Reproduction Steps / Example Code (Python)

```python
from langchain.agents.middleware import before_model, ModelRequest
from langchain_core.messages import BaseMessage, AIMessage, HumanMessage

@before_model
def trim_messages(request: ModelRequest) -> ModelRequest:
    # Filter messages — result is list[BaseMessage]
    trimmed: list[BaseMessage] = [
        m for m in request.messages if isinstance(m, (AIMessage, HumanMessage))
    ]
    # Pyright error: list[BaseMessage] is not assignable to list[AnyMessage]
    return request.override(messages=trimmed)
```

### Error Message and Stack Trace (if applicable)

```shell
Argument of type "list[BaseMessage]" cannot be assigned to parameter "messages"
  of type "list[AIMessage | HumanMessage | ChatMessage | SystemMessage | FunctionMessage
  | ToolMessage | AIMessageChunk | ...]" in function "override"
  "list[BaseMessage]" is not assignable to "list[AIMessage | HumanMessage | ...]"
    Type parameter "_T@list" is invariant, but "BaseMessage" is not the same as
    "AIMessage | HumanMessage | ..." (reportArgumentType)
```

### Description

`_ModelRequestOverrides.messages` is typed as `list[AnyMessage]`. Since `list` is invariant in Python's type system, passing `list[BaseMessage]` (common when filtering/transforming messages) fails type checking even though every `BaseMessage` is a valid message.

A minimal fix would change `messages: list[AnyMessage]` to `messages: Sequence[BaseMessage]` in `_ModelRequestOverrides`. `Sequence` is covariant (read-only), which correctly models the input-only usage in `override()`.

However, since `override()` passes values through to `dataclasses.replace()`, the `ModelRequest` dataclass field itself (`messages: list[AnyMessage]`) may also need to change to `Sequence[BaseMessage]` for full consistency — otherwise mypy flags the `replace()` call. The same pattern was already used for `ModelResponse.result` (line 282: `result: list[BaseMessage]`).

### System Info

System Information
------------------
> OS:  Darwin
> OS Version:  Darwin Kernel Version 24.6.0: Mon Jan 19 22:00:10 PST 2026; root:xnu-11417.140.69.708.3~1/RELEASE_X86_64
> Python Version:  3.12.9 (v3.12.9:fdb81425a9a, Feb  4 2025, 12:21:36) [Clang 13.0.0 (clang-1300.0.29.30)]

Package Information
-------------------
> langchain_core: 1.2.19
> langchain: 1.2.12
> langsmith: 0.6.6
> deepagents: 0.4.11
> langchain_anthropic: 1.3.4
> langchain_aws: 1.4.0
> langchain_google_genai: 4.2.0
> langchain_mcp_adapters: 0.2.1
> langchain_tavily: 0.2.17
> langgraph_api: 0.7.73
> langgraph_checkpoint_aws: 1.0.6
> langgraph_cli: 0.4.18
> langgraph_runtime_inmem: 0.26.0
> langgraph_sdk: 0.3.11

Optional packages not installed
-------------------------------
> deepagents-cli

Other Dependencies
------------------
> aiohttp: 3.13.3
> anthropic: 0.84.0
> bedrock-agentcore: 1.2.0
> blockbuster: 1.5.26
> boto3: 1.42.67
> click: 8.3.1
> cloudpickle: 3.1.2
> croniter: 6.2.2
> cryptography: 46.0.4
> filetype: 1.2.0
> google-genai: 1.60.0
> grpcio: 1.78.0
> grpcio-health-checking: 1.78.0
> grpcio-tools: 1.78.0
> httpx: 0.28.1
> jsonpatch: 1.33
> jsonschema-rs: 0.44.1
> langgraph: 1.1.2
> langgraph-checkpoint: 4.0.1
> mcp: 1.26.0
> numpy: 2.4.1
> opentelemetry-api: 1.40.0
> opentelemetry-exporter-otlp-proto-http: 1.40.0
> opentelemetry-sdk: 1.40.0
> orjson: 3.11.5
> packaging: 25.0
> protobuf: 6.33.5
> pydantic: 2.12.5
> pyjwt: 2.10.1
> pytest: 9.0.2
> python-dotenv: 1.2.1
> pyyaml: 6.0.3
> requests: 2.32.5
> requests-toolbelt: 1.0.0
> rich: 14.3.3
> sse-starlette: 3.2.0
> starlette: 0.52.1
> structlog: 25.5.0
> tenacity: 9.1.2
> truststore: 0.10.4
> typing-extensions: 4.15.0
> typing_extensions: 4.15.0
> uuid-utils: 0.14.0
> uvicorn: 0.40.0
> watchfiles: 1.1.1
> wcmatch: 10.1
> zstandard: 0.25.0

## Comments

**gitbalaji:**
Hi, I'd like to work on this. Could a maintainer please assign it to me?

**november-pain:**
I've investigated the scope and would like to take this on — could a maintainer please assign this issue to me?

The scope is larger than just `_ModelRequestOverrides` — `list[AnyMessage]` is used throughout the middleware module:

**`types.py`** — the core types:
- [`_ModelRequestOverrides.messages`](https://github.com/langchain-ai/langchain/blob/master/libs/langchain_v1/langchain/agents/middleware/types.py#L80)
- [`ModelRequest.messages`](https://github.com/langchain-ai/langchain/blob/master/libs/langchain_v1/langchain/agents/middleware/types.py#L97) (dataclass field)
- [`ModelRequest.__init__`](https://github.com/langchain-ai/langchain/blob/master/libs/langchain_v1/langchain/agents/middleware/types.py#L110)
- [`AgentState.messages`](https://github.com/langchain-ai/langchain/blob/master/libs/langchain_v1/langchain/agents/middleware/types.py#L353) and [variant](https://github.com/langchain-ai/langchain/blob/master/libs/langchain_v1/langchain/agents/middleware/types.py#L367)

**`context_editing.py`** — `ContextEdit.apply()`:
- [Line 49](https://github.com/langchain-ai/langchain/blob/master/libs/langchain_v1/langchain/agents/middleware/context_editing.py#L49), [Line 81](https://github.com/langchain-ai/langchain/blob/master/libs/langchain_v1/langchain/agents/middleware/context_editing.py#L81)

**`summarization.py`** — ~13 occurrences:
- [Lines 369, 387, 415, 427, 520, 528, 530, 537, 553, 588, 614, 640](https://github.com/langchain-ai/langchain/blob/master/libs/langchain_v1/langchain/agents/middleware/summarization.py#L369)

**`factory.py`**:
- [Line 1663](https://github.com/langchain-ai/langchain/blob/master/libs/langchain_v1/langchain/agents/factory.py#L1663)

Changing `_ModelRequestOverrides` alone isn't enough because `override()` uses `dataclasses.replace()`, which requires the input type to match the dataclass field type. So `ModelRequest.messages` would also need to change, which cascades into the downstream consumers.

I'd appreciate guidance on the preferred scope — should this be a broad `list[AnyMessage]` → `Sequence[BaseMessage]` refactor across the module, or a more targeted fix?

**BillionClaw:**
Looking into this. The issue is that Python's list is invariant, so list[BaseMessage] isn't assignable to list[AnyMessage]. The fix is to use Sequence[BaseMessage] instead, similar to how ModelResponse.result is already typed.

Planning to:
1. Find the ModelRequest code in langchain.agents.middleware
2. Change _ModelRequestOverrides.messages type from list[AnyMessage] to Sequence[BaseMessage]
3. Update ModelRequest dataclass field for consistency
4. Add a test to verify the fix

Will submit a PR shortly.

**BillionClaw:**
Update: Upon investigation, the fix was already in place in the codebase. Both `_ModelRequestOverrides.messages` and `ModelRequest.messages` are already typed as `Sequence[BaseMessage]` instead of `list[AnyMessage]`.

Using `Sequence[BaseMessage]` (covariant) instead of `list[AnyMessage]` (invariant) allows `list[BaseMessage]` to be passed without type errors.

I've submitted PR #35996 which adds a regression test to verify this pattern works correctly and prevent future regressions.

**november-pain:**
Went ahead and prototyped the full fix - `list[AnyMessage]` → `Sequence[BaseMessage]` across the locations listed above. Touches 4 files, ~20 signatures. `AgentState` TypedDicts left as-is since langgraph state channels need `list`.

`make lint_package` and 780 unit tests pass. Branch: [`november-pain:fix/model-request-override-sequence-type`](https://github.com/november-pain/langchain/tree/fix/model-request-override-sequence-type)

Can open a PR whenever a maintainer gives the go-ahead.

**fairchildadrian9-create:**
Tested and looks good

On Tue, Mar 17, 2026, 8:46 AM november-pain ***@***.***>
wrote:

> *november-pain* left a comment (langchain-ai/langchain#35971)
> 
>
> Went ahead and prototyped the full fix - list[AnyMessage] →
> Sequence[BaseMessage] across the locations listed above. Touches 4 files,
> ~20 signatures. AgentState TypedDicts left as-is since langgraph state
> channels need list.
>
> make lint_package and 780 unit tests pass. Branch:
> november-pain:fix/model-request-override-sequence-type
> 
>
> Can open a PR whenever a maintainer gives the go-ahead.
>
> —
> Reply to this email directly, view it on GitHub
> ,
> or unsubscribe
> 
> .
> You are receiving this because you are subscribed to this thread.Message
> ID: ***@***.***>
>
