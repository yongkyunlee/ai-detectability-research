# ChatAnthropic latest version 1.3.4(langchain-anthropic) streaming fails with No generation chunks were returned

**Issue #35442** | State: open | Created: 2026-02-25 | Updated: 2026-03-09
**Author:** GANAPS14
**Labels:** bug, anthropic, external

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
from langchain_anthropic import ChatAnthropic

BASE_URL = ""
API_KEY = ""
MODEL = "anthropic.claude-4-5-opus-v1:0"

model = ChatAnthropic(
    model=MODEL,
    api_key=API_KEY,
    streaming=True,
    base_url=BASE_URL,
)

for chunk in model.stream("Write a short 'Hello World' poem."):
    print(chunk.content, end="|", flush=True)
```

### Error Message and Stack Trace (if applicable)

```shell
Root cause: The Bedrock proxy sends SSE events with only data: lines (no event: field). The anthropic SDK v0.84.0 expects event: message_start, etc. Without those, sse.event is None and all events are silently skipped → 0 chunks → ValueError: No generation chunks were returned.

Traceback (most recent call last):
  File "/Applications/PyCharm CE.app/Contents/plugins/python-ce/helpers/pydev/pydevd.py", line 1570, in _exec
    pydev_imports.execfile(file, globals, locals)  # execute the script
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/Applications/PyCharm CE.app/Contents/plugins/python-ce/helpers/pydev/_pydev_imps/_pydev_execfile.py", line 18, in execfile
    exec(compile(contents+"\n", file, 'exec'), glob, loc)
  File "/chatanthropicexample.py", line 20, in 
    for chunk in model.stream("Write a short 'Hello World' poem."):
                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/.venv/lib/python3.12/site-packages/langchain_core/language_models/chat_models.py", line 601, in stream
    raise err
ValueError: No generation chunks were returned
```

### Description

model = ChatAnthropic(
    model=MODEL,
    api_key=API_KEY,
    streaming=True,
    base_url=BASE_URL,
)
is failing Version used 
anthropic="^0.84.0"
langchain-anthropic = "^1.3.4"

# Test : stream() fails
print("\n--- Test : model.stream() (streaming) ---")
try:
    for chunk in model.stream("Say hello in one sentence."):
        print(chunk.content, end="|", flush=True)
    print("\n✅ stream() OK")
except Exception as e:
    print(f"❌ stream() FAILED: {type(e).__name__}: {e}")
    print("\nFull stack trace:")
    traceback.print_exc()

### System Info

 python -m langchain_core.sys_info

System Information
------------------
> OS:  Darwin
> OS Version:  Darwin Kernel Version 24.6.0: Wed Nov  5 21:30:44 PST 2025; root:xnu-11417.140.69.705.2~1/RELEASE_ARM64_T6041
> Python Version:  3.12.9 (v3.12.9:fdb81425a9a, Feb  4 2025, 12:21:36) [Clang 13.0.0 (clang-1300.0.29.30)]

Package Information
-------------------
> langchain_core: 1.2.15
> langchain: 1.2.10
> langsmith: 0.7.6
> langchain_anthropic: 1.3.4
> langchain_openai: 1.1.10
> langchain_postgres: 0.0.16
> langgraph_sdk: 0.3.9

Optional packages not installed
-------------------------------
> deepagents
> deepagents-cli

Other Dependencies
------------------
> anthropic: 0.84.0
> asyncpg: 0.31.0
> httpx: 0.28.1
> jsonpatch: 1.33
> langgraph: 1.0.9
> numpy: 2.4.2
> openai: 2.24.0
> opentelemetry-api: 1.39.1
> opentelemetry-exporter-otlp-proto-http: 1.39.1
> opentelemetry-sdk: 1.39.1
> orjson: 3.11.7
> packaging: 25.0
> pgvector: 0.3.6
> psycopg: 3.3.3
> psycopg-pool: 3.3.0
> pydantic: 2.12.5
> pytest: 7.4.4
> pyyaml: 6.0.3
> requests: 2.32.5
> requests-toolbelt: 1.0.0
> rich: 14.3.3
> sqlalchemy: 2.0.47
> tenacity: 9.1.4
> tiktoken: 0.12.0
> typing-extensions: 4.15.0
> uuid-utils: 0.14.1
> wrapt: 1.17.3
> xxhash: 3.6.0
> zstandard: 0.25.0

## Comments

**keenborder786:**
@GANAPS14 
Since you are using Anthropic with Bedrock, can I recommend using [ChatAnthropicBedrock](https://reference.langchain.com/python/langchain-aws/chat_models/anthropic/ChatAnthropicBedrock), which was recently released.

**xXMrNidaXx:**
## Root Cause Analysis

This is a **Bedrock proxy SSE format mismatch** rather than a LangChain bug per se. The Anthropic SDK expects standard SSE with explicit event types:

```
event: message_start
data: {...}

event: content_block_delta  
data: {...}
```

Bedrock proxies typically send:
```
data: {...}
```

Without the `event:` field, `sse.event` is `None`, causing all event handlers to no-op.

## Workarounds

### Option 1: Patch the SSE parser (quick hack)

```python
from anthropic._streaming import ServerSentEvent
import json

original_parse = ServerSentEvent.parse

def patched_parse(raw):
    sse = original_parse(raw)
    if sse.event is None and sse.data:
        # Infer event type from data
        try:
            data = json.loads(sse.data)
            sse.event = data.get("type", "message")
        except:
            pass
    return sse

ServerSentEvent.parse = staticmethod(patched_parse)
```

### Option 2: Use the bedrock-runtime package directly

If your organization is on AWS Bedrock, use `langchain-aws` with `ChatBedrockConverse`:

```python
from langchain_aws import ChatBedrockConverse

model = ChatBedrockConverse(
    model="anthropic.claude-4-5-opus-v1:0",
    region_name="us-east-1",
)
```

This uses boto3's native streaming and sidesteps the SSE format issue entirely.

### Option 3: Disable streaming as a workaround

```python
model = ChatAnthropic(
    model=MODEL,
    api_key=API_KEY,
    streaming=False,  # Use non-streaming until proxy is fixed
    base_url=BASE_URL,
)

# Use invoke instead of stream
response = model.invoke("Write a short poem")
```

## The Real Fix

The Bedrock proxy should be updated to include `event:` fields in SSE responses, or `langchain-anthropic` could add a `bedrock_compat=True` flag that parses event types from the data payload instead of the SSE field.

Happy to help debug further if you can share a sanitized example of the raw SSE output from your proxy!

**xXMrNidaXx:**
## Root Cause Analysis

This is a compatibility issue between the Anthropic SDK v0.84.0+ SSE event parsing and AWS Bedrock's streaming proxy format.

### What's Happening

The Bedrock Runtime streaming endpoint sends SSE events with a different structure than the native Anthropic API:

**Bedrock format:**
```
data: {"type":"message_start",...}
```

**Native Anthropic format:**
```
event: message_start
data: {"type":"message_start",...}
```

In `anthropic._streaming.Stream._iter_events()`, the SDK checks `sse.event` to route messages. When `event:` is absent (Bedrock), `sse.event` is `None`, causing all events to be silently dropped → zero chunks → the error.

### Workaround Options

**1. Use `langchain-aws` with BedrockChat instead**
```python
from langchain_aws import ChatBedrock

model = ChatBedrock(
    model_id="anthropic.claude-4-5-opus-v1:0",
    region_name="us-east-1",
    streaming=True
)
```
This uses AWS's native SDK which handles Bedrock streaming correctly.

**2. Patch the anthropic SDK (not recommended for production)**
If you must use ChatAnthropic with Bedrock, you could monkey-patch the event parser to fall back to `data["type"]` when `sse.event` is None.

**3. Use invoke() instead of stream() temporarily**
```python
response = model.invoke("Write a short Hello World poem.")
```

### Suggested Fix

The `langchain-anthropic` package could detect Bedrock base URLs and either:
1. Warn users to use `langchain-aws` instead
2. Add a `bedrock_mode=True` flag that handles the SSE format difference

Happy to contribute a PR if the maintainers want to go that route.

---
*Revolution AI - AI Implementation Specialists*

**xXMrNidaXx:**
The root cause analysis here is spot-on. This is a classic SSE format incompatibility between Bedrock's proxy format and what the Anthropic SDK expects.

**Quick Workaround Until Fixed:**

If you need streaming now and can't wait for an SDK update, you have a couple options:

1. **Downgrade anthropic SDK** to pre-0.84.0 if the older parsing was more lenient
2. **Use invoke() with callbacks** instead of stream():
```python
from langchain_core.callbacks import StreamingStdOutCallbackHandler

for chunk in model.invoke(
    "Write a short 'Hello World' poem.",
    config={"callbacks": [StreamingStdOutCallbackHandler()]}
):
    pass  # Callback handles output
```

3. **Direct Bedrock client** (bypass LangChain for streaming):
```python
import boto3
import json

bedrock = boto3.client('bedrock-runtime')
response = bedrock.invoke_model_with_response_stream(
    modelId='anthropic.claude-4-5-opus-v1:0',
    body=json.dumps({
        'anthropic_version': 'bedrock-2023-05-31',
        'messages': [{'role': 'user', 'content': 'Hello World poem'}],
        'max_tokens': 1024
    })
)
for event in response['body']:
    chunk = json.loads(event['chunk']['bytes'])
    if chunk['type'] == 'content_block_delta':
        print(chunk['delta'].get('text', ''), end='')
```

**The Fix:**

The proper fix needs to happen in `langchain-anthropic` to handle SSE events that lack the `event:` field. The SDK should treat `event=None` with valid `data:` as a content event rather than skipping it entirely.

I'd be happy to help test a PR if the maintainers want to tackle this — we run Claude on Bedrock proxies in production too.

**GANAPS14:**
None of the options worked for me I added this monkey patch can you review .. 

`

"""
ChatAnthropic streaming example with monkey-patch for Bedrock proxy.

The Bedrock proxy sends SSE events without an 'event:' field, e.g.:
    data: {"type":"content_block_delta", ...}

But the anthropic SDK expects both 'event:' and 'data:' fields:
    event: content_block_delta
    data: {"type":"content_block_delta", ...}

Without the 'event:' field, sse.event is None and the SDK's Stream.__stream__
silently yields 0 events -> LangChain raises "No generation chunks were returned".

The monkey-patch below fixes the SSE decoder to infer the event type from the
JSON payload's "type" field when the SSE 'event:' field is missing.
"""
import json as _json
from anthropic._streaming import Stream, ServerSentEvent
from typing import cast as _cast, Any, Iterator

# ── Monkey-patch: fix SSE event type for Bedrock proxy ──────────────────────
_original__stream__ = Stream.__stream__

def _patched__stream__(self) -> Iterator:
    """Wrap the original __stream__ to inject sse.event from data['type']."""
    cast_to = _cast(Any, self._cast_to)
    response = self.response
    process_data = self._client._process_response_data

    try:
        for sse in self._iter_events():
            # If the proxy omitted the 'event:' field, infer it from the JSON body
            if sse.event is None and sse.data:
                try:
                    payload = _json.loads(sse.data)
                    if isinstance(payload, dict) and "type" in payload:
                        sse = ServerSentEvent(
                            event=payload["type"],
                            data=sse.data,
                            id=sse.id,
                            retry=sse.retry,
                        )
                except (ValueError, KeyError):
                    pass

            if sse.event == "completion":
                yield process_data(data=sse.json(), cast_to=cast_to, response=response)

            if sse.event in (
                "message_start", "message_delta", "message_stop",
                "content_block_start", "content_block_delta", "content_block_stop",
            ):
                data = sse.json()
                if isinstance(data, dict) and "type" not in data:
                    data["type"] = sse.event
                yield process_data(data=data, cast_to=cast_to, response=response)

            if sse.event == "ping":
                continue

            if sse.event == "error":
                body = sse.data
                try:
                    body = sse.json()
                    err_msg = f"{body}"
                except Exception:
                    err_msg = sse.data or f"Error code: {response.status_code}"
                raise self._client._make_status_error(
                    err_msg, body=body, response=self.response,
                )
    finally:
        response.close()

Stream.__stream__ = _patched__stream__
print("✅ Monkey-patch applied: SSE event type inference for Bedrock proxy\n")
# ── End monkey-patch 

from langchain_anthropic import ChatAnthropic

base_url="",
API_KEY=""

MODEL = "anthropic.claude-4-5-opus-v1:0"

model = ChatAnthropic(
    model=MODEL,
    api_key=API_KEY,
    streaming=True,
    base_url=BASE_URL
)

#Use .stream() to get an iterator — now works with the monkey-patch!
for chunk in model.stream("Write a short 'Hello World' poem."):
    print(chunk.content, end="|", flush=True)
 print()  # newline at end`

**keenborder786:**
@GANAPS14
Did you try https://reference.langchain.com/python/langchain-aws/chat_models/anthropic/ChatAnthropicBedrock.
From the look of your stack trace it seems you are still using `ChatAnthropic `.

**xXMrNidaXx:**
The root cause identified is correct — the Bedrock proxy is sending raw SSE data without `event:` type prefixes, and the anthropic SDK relies on `sse.event` to dispatch to the right handler.

**Where the mismatch occurs:**

The anthropic SDK's SSE parser expects:
```
event: message_start
data: {"type": "message_start", ...}

event: content_block_delta
data: {"type": "content_block_delta", ...}
```

But Bedrock proxies often send just:
```
data: {"type": "message_start", ...}
data: {"type": "content_block_delta", ...}
```

Without `event:`, the SDK's `sse.event` is `None`, so chunks are dropped.

**Workarounds:**

1. **If you control the proxy**: Add `event: message` (or the actual event type) before each `data:` line.

2. **Patch at the langchain level**: In `langchain_anthropic`, override `_stream()` to parse `data["type"]` directly instead of relying on `sse.event`:
```python
# Pseudo-fix in _convert_message_chunk
if sse.event is None and sse.data:
    data = json.loads(sse.data)
    event_type = data.get("type")  # Use embedded type
```

3. **Use Bedrock client directly**: If using AWS Bedrock, use `langchain_aws.ChatBedrock` instead of routing through a custom proxy to `ChatAnthropic`.

**The SDK side**: This might be worth raising with Anthropic too — making the SDK resilient to `event: None` by falling back to `data.type` would help with non-standard proxies.

**xXMrNidaXx:**
This is a protocol mismatch issue, not a langchain-anthropic bug per se.

**Root cause:** You're pointing `ChatAnthropic` (which uses the native Anthropic SDK) at a Bedrock-compatible proxy endpoint. Bedrock's streaming format differs from Anthropic's native SSE:

| Format | Event field | Data structure |
|--------|-------------|----------------|
| Anthropic native | `event: message_start`, `event: content_block_delta`, etc. | Nested JSON with `type` field |
| Bedrock proxy | No `event:` line | Flat `data:` lines only |

The Anthropic SDK v0.84.0+ parses `sse.event` to route events—when it's `None`, every chunk is skipped.

**Solutions:**

1. **Use `ChatBedrockConverse`** instead — it's designed for Bedrock endpoints:
```python
from langchain_aws import ChatBedrockConverse

model = ChatBedrockConverse(
    model="anthropic.claude-4-5-opus-v1:0",
    region_name="us-east-1",  # or your region
    # credentials_profile_name="your-profile"
)
```

2. **If you must use ChatAnthropic** with a custom proxy, the proxy needs to transform responses to native Anthropic SSE format (add `event:` lines).

3. **Non-streaming workaround** — set `streaming=False` and use `.invoke()` instead of `.stream()` while you sort out the proxy format.

The error message could be clearer—"No generation chunks" is downstream of the actual problem (SSE parsing yielding zero valid events).
