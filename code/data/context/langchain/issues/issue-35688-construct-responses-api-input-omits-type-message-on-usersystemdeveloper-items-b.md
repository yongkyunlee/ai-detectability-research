# `_construct_responses_api_input` omits type: "message" on user/system/developer items, breaking Foundry Responses API  Body:

**Issue #35688** | State: closed | Created: 2026-03-09 | Updated: 2026-03-15
**Author:** santiagxf
**Labels:** bug, openai, external

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
- [x] langchain-openai
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

_No response_

### Reproduction Steps / Example Code (Python)

```python
from langchain_openai import ChatOpenAI  # or any subclass targeting Azure AI Foundry

model = ChatOpenAI(base_url="https://.services.ai.azure.com/openai/v1", ...)

model.invoke([
    {"role": "developer", "content": "Translate from English into Italian"},
    {"role": "user", "content": "hi!"},
])
```

### Error Message and Stack Trace (if applicable)

```shell
BadRequestError: Error code: 400 - {'error': {'message': "Invalid value: ''. Supported values are: 
'apply_patch_call', ..., 'message', ..., and 'web_search_call'.",
'type': 'invalid_request_error', 'param': 'input[1]', 'code': 'invalid_value'}}
```

### Description

`_construct_responses_api_input()` in langchain_openai/chat_models/base.py builds Responses API input items without explicitly setting `"type": "message"` on user, system, and developer message dicts. OpenAI's native endpoint silently infers the type, but other OpenAI-compatible endpoints (e.g. Microsoft Foundry) enforce the schema strictly and reject the request with a 400 Bad Request.

### System Info

System Information
------------------
> OS:  Linux
> OS Version:  #1 SMP PREEMPT_DYNAMIC Thu Jun  5 18:30:46 UTC 2025
> Python Version:  3.12.3 (main, Jan 22 2026, 20:57:42) [GCC 13.3.0]

Package Information
-------------------
> langchain_core: 1.2.17
> langchain: 1.2.10
> langsmith: 0.7.13
> langchain_azure_ai: 1.1.0
> langchain_openai: 1.1.10
> langgraph_sdk: 0.3.9

Optional packages not installed
-------------------------------
> deepagents
> deepagents-cli

Other Dependencies
------------------
> aiohttp: 3.13.3
> azure-ai-agents: 1.2.0b5
> azure-ai-documentintelligence: 1.0.2
> azure-ai-projects: 2.0.0
> azure-ai-textanalytics: 5.4.0
> azure-ai-vision-imageanalysis: 1.0.0
> azure-core: 1.38.2
> azure-cosmos: 4.15.0
> azure-identity: 1.25.2
> azure-mgmt-logic: 10.0.0
> azure-monitor-opentelemetry: 1.8.6
> azure-search-documents: 11.6.0
> httpx: 0.28.1
> jsonpatch: 1.33
> langgraph: 1.0.10
> numpy: 2.2.6
> openai: 2.26.0
> opentelemetry-api: 1.39.0
> opentelemetry-instrumentation: 0.60b0
> opentelemetry-instrumentation-threading: 0.60b0
> opentelemetry-sdk: 1.39.0
> opentelemetry-semantic-conventions: 0.60b0
> opentelemetry-semantic-conventions-ai: 0.4.15
> orjson: 3.11.7
> packaging: 26.0
> pydantic: 2.12.5
> pytest: 7.4.4
> pyyaml: 6.0.3
> requests: 2.32.5
> requests-toolbelt: 1.0.0
> six: 1.17.0
> tenacity: 9.1.4
> tiktoken: 0.12.0
> typing-extensions: 4.15.0
> uuid-utils: 0.14.1
> vcrpy: 8.1.1
> wrapt: 1.17.3
> xxhash: 3.6.0
> zstandard: 0.25.0

## Comments

**JiwaniZakir:**
Can I pick this up? I've been looking at the relevant code.

**giulio-leone:**
Hi! I already prepared and validated a fix for this in PR #35706, but the PR was auto-closed by the issue-assignment policy before review.

If this issue is still available, could I please be assigned so I can update/reopen that PR instead of duplicating the work? Happy to refresh the branch again if needed. Thanks!

**ccurme:**
@giulio-leone I've assigned you and re-opened the PR.

**weiguangli-io:**
## Root cause analysis

The issue is in `_construct_responses_api_input()` at [`libs/partners/openai/langchain_openai/chat_models/base.py` (lines 4380–4399)](https://github.com/langchain-ai/langchain/blob/master/libs/partners/openai/langchain_openai/chat_models/base.py#L4380-L4399).

For `user`, `system`, and `developer` messages, the function delegates to `_convert_message_to_dict(lc_msg, api="responses")`, which returns a dict containing only `role` and `content` — no `type` field. The dict is then appended directly to the input list:

```python
elif msg["role"] in ("user", "system", "developer"):
    # ... content block processing ...
    if msg["content"]:
        input_.append(msg)       # <-- no "type": "message" set
    else:
        input_.append(msg)       # <-- same here
```

In contrast, `assistant` messages already have `"type": "message"` correctly set (lines 4316–4322 and 4348–4360).

## Why it works on OpenAI but fails on Azure AI Foundry

OpenAI's native Responses API endpoint silently infers `"type": "message"` when the field is absent — it treats it as an optional default. Azure AI Foundry (and potentially other strict OpenAI-compatible providers) validates the schema strictly and rejects requests where `type` is missing, returning:

```
Invalid value: ''. Supported values are: 'apply_patch_call', ..., 'message', ...
```

This is analogous to the common pattern where the canonical API server is lenient about optional/default fields, but proxy implementations enforce the documented schema to the letter.

## Proposed fix

The fix is straightforward — explicitly set `"type": "message"` on user/system/developer dicts before appending them to the input list. This could be done either:

1. **At the append site** (lines ~4397/4399): add `msg["type"] = "message"` before `input_.append(msg)`, or
2. **In `_convert_message_to_dict`** when `api="responses"`: include `"type": "message"` in the returned dict for user/system/developer roles.

Option 1 is more surgical and keeps the change scoped to the Responses API path. Option 2 is cleaner architecturally but has a wider blast radius.

Either way, the fix should be safe since the `type` field is already set for assistant messages in the same function, and OpenAI's API accepts it explicitly — this just makes the implicit default explicit.

## Existing PR

I see that PR #35693 by @giulio-leone is already open and addresses this. The approach looks correct.

## Other places to audit

It may be worth checking whether similar `type` omissions exist for:
- The `ChatMessage` path (line 334 in `_convert_message_to_dict`, where `role` is set from `message.role` — if a ChatMessage with role "user" goes through the Responses path, it would hit the same issue)
- Any future message types added to the Responses API

A defensive approach would be to always set `msg["type"] = "message"` for *all* non-tool, non-function-call items in the `elif msg["role"] in (...)` branch, rather than only for the currently known roles.

**laniakea001:**
## Additional Context: Microsoft Azure AI Foundry Compatibility

This issue affects not just Azure AI Foundry but any OpenAI-compatible API that strictly validates the Responses API schema. The root cause is that the  field is optional in OpenAI's implementation but required by strict implementations.

### Technical Details

The fix in PR #35706 correctly adds the  field. Here's a more comprehensive approach:

**Option A: Fix at the message conversion level**
In , when , always include  for user/system/developer roles:

**Option B: Fix at the input construction level**
In , explicitly set the type before appending:

### Testing Recommendations

To ensure backward compatibility, test against:
1. OpenAI Responses API (should continue to work)
2. Azure AI Foundry (the reported failure case)
3. Other OpenAI-compatible endpoints (e.g., local vLLM, Ollama)

### Related Issues

This pattern of "lenient OpenAI vs strict compatible implementations" has appeared in other places. Consider auditing other API construction methods for similar schema validation issues.

Great that this is being fixed! The PR approach looks solid.
