# Streaming bypasses guardrails/middleware

**Issue #35011** | State: open | Created: 2026-02-04 | Updated: 2026-03-17
**Author:** Ashton-Sidhu
**Labels:** bug, core, langchain, external

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
- [x] langchain-core
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
- [ ] langchain-perplexity
- [ ] langchain-prompty
- [ ] langchain-qdrant
- [ ] langchain-xai
- [ ] Other / not sure / general

### Related Issues / PRs

_No response_

### Reproduction Steps / Example Code (Python)

```python
agent = create_agent(
        model="gpt-4o-mini",
        middleware=[
            PIIMiddleware(
                "email",
                strategy="block",
                apply_to_input=False,
                apply_to_output=True,
            ),
        ],
    )

    output = ""
    for msg, metadata in agent.stream(
        {
            "messages": [
                {
                    "role": "user",
                    "content": "My email is john.doe@example.com? Can you write a funny greeting with my email?",
                },
            ]
        },
        stream_mode="messages",
    ):
        if msg.content:
            print(msg.content, flush=True, end="")
```

### Error Message and Stack Trace (if applicable)

```shell
Sure! Here's a funny greeting incorporating your email:

---

🎉 Hey there, awesome human! 🎉

Just popping in to say, if you ever need a digital superhero, you can reach me at my secret lair: **john.doe@example.com**! But beware, sending a message may result in spontaneous laughter and a 100% increase in good vibes!

Chirp, chirp, and let the email adventures begin! 🦸‍♂️💻

---

Feel free to tweak it however you like!Traceback (most recent call last):
  File "/Users/sidhu/hiddenlayer-langchain-guardrails/tests/test_hiddenlayer.py", line 79, in 
    test_streaming_malicious()
  File "/Users/sidhu/hiddenlayer-langchain-guardrails/tests/test_hiddenlayer.py", line 64, in test_streaming_malicious
    for msg, metadata in agent.stream(
  File "/Users/sidhu/hiddenlayer-langchain-guardrails/.venv/lib/python3.10/site-packages/langgraph/pregel/main.py", line 2646, in stream
    for _ in runner.tick(
  File "/Users/sidhu/hiddenlayer-langchain-guardrails/.venv/lib/python3.10/site-packages/langgraph/pregel/_runner.py", line 258, in tick
    _panic_or_proceed(
  File "/Users/sidhu/hiddenlayer-langchain-guardrails/.venv/lib/python3.10/site-packages/langgraph/pregel/_runner.py", line 520, in _panic_or_proceed
    raise exc
  File "/Users/sidhu/hiddenlayer-langchain-guardrails/.venv/lib/python3.10/site-packages/langgraph/pregel/_executor.py", line 80, in done
    task.result()
  File "/opt/homebrew/Cellar/python@3.10/3.10.16/Frameworks/Python.framework/Versions/3.10/lib/python3.10/concurrent/futures/_base.py", line 451, in result
    return self.__get_result()
  File "/opt/homebrew/Cellar/python@3.10/3.10.16/Frameworks/Python.framework/Versions/3.10/lib/python3.10/concurrent/futures/_base.py", line 403, in __get_result
    raise self._exception
  File "/opt/homebrew/Cellar/python@3.10/3.10.16/Frameworks/Python.framework/Versions/3.10/lib/python3.10/concurrent/futures/thread.py", line 58, in run
    result = self.fn(*self.args, **self.kwargs)
  File "/Users/sidhu/hiddenlayer-langchain-guardrails/.venv/lib/python3.10/site-packages/langgraph/pregel/_retry.py", line 42, in run_with_retry
    return task.proc.invoke(task.input, config)
  File "/Users/sidhu/hiddenlayer-langchain-guardrails/.venv/lib/python3.10/site-packages/langgraph/_internal/_runnable.py", line 656, in invoke
    input = context.run(step.invoke, input, config, **kwargs)
  File "/Users/sidhu/hiddenlayer-langchain-guardrails/.venv/lib/python3.10/site-packages/langgraph/_internal/_runnable.py", line 400, in invoke
    ret = self.func(*args, **kwargs)
  File "/Users/sidhu/hiddenlayer-langchain-guardrails/.venv/lib/python3.10/site-packages/langchain/agents/middleware/pii.py", line 321, in after_model
    new_content, matches = self._process_content(content)
  File "/Users/sidhu/hiddenlayer-langchain-guardrails/.venv/lib/python3.10/site-packages/langchain/agents/middleware/pii.py", line 160, in _process_content
    sanitized = apply_strategy(content, matches, self.strategy)
  File "/Users/sidhu/hiddenlayer-langchain-guardrails/.venv/lib/python3.10/site-packages/langchain/agents/middleware/_redaction.py", line 334, in apply_strategy
    raise PIIDetectionError(matches[0]["type"], matches)
langchain.agents.middleware._redaction.PIIDetectionError: Detected 1 instance(s) of email in text content

```

### Description

If streaming the tokens is enabled, the middleware runs after the stream has been consumed. This means any guardrails or middleware is applied after the tokens have been consumed by the user. This leaks any information that would be should have been caught by the guardrails.

Is there anyway to control streaming so that content is scanned first/periodically then streamed to the user?

### System Info

System Information
------------------
> OS:  Darwin
> OS Version:  Darwin Kernel Version 25.1.0: Mon Oct 20 19:33:00 PDT 2025; root:xnu-12377.41.6~2/RELEASE_ARM64_T6020
> Python Version:  3.10.16 (main, Dec  3 2024, 17:27:57) [Clang 16.0.0 (clang-1600.0.26.4)]

Package Information
-------------------
> langchain_core: 1.2.8
> langchain: 1.2.8
> langsmith: 0.6.8
> langchain_openai: 1.1.7
> langgraph_sdk: 0.3.3

Optional packages not installed
-------------------------------
> langserve

Other Dependencies
------------------
> httpx: 0.28.1
> jsonpatch: 1.33
> langgraph: 1.0.7
> openai: 2.16.0
> orjson: 3.11.7
> packaging: 26.0
> pydantic: 2.12.5
> pytest: 9.0.2
> pyyaml: 6.0.3
> requests: 2.32.5
> requests-toolbelt: 1.0.0
> tenacity: 9.1.2
> tiktoken: 0.12.0
> typing-extensions: 4.15.0
> uuid-utils: 0.14.0
> xxhash: 3.6.0
> zstandard: 0.25.0

## Comments

**keenborder786:**
@Ashton-Sidhu , Unfortunately, the `Middleware` node is only executed once the entire stream has been yielded back to the user, which you print directly, and I see no direct way of executing the middleware token by token under the current Middleware architecture.

However, what I found, you can short of fake streaming while making sure you only stream text one PII middleware has been executed:

```python

from langchain.agents import create_agent
from langchain.agents.middleware import PIIMiddleware
import tiktoken
import time
agent = create_agent(
        model="gpt-4o-mini",
        middleware=[
            PIIMiddleware(
                "email",
                strategy="block",
                apply_to_input=False,
                apply_to_output=True,
            ),
        ],
    )
enc = tiktoken.encoding_for_model("gpt-4o-mini")  # use your model

def stream_tokens(token_ids):
    for tid in token_ids:
        yield enc.decode([tid])  # preserves spaces/punctuation
output = ""
try:
    output = agent.invoke({
            "messages": [
                {
                    "role": "user",
                    "content": "My email is john.doe@example.com? Can you write a funny greeting with my email?",
                },
            ]
        })
    last_message = output["messages"][-1]
    token_ids = enc.encode(last_message.content)
    for chunk in stream_tokens(token_ids):
        print(chunk, end="", flush=True)
        time.sleep(0.001)
except:
    print("ERROR")

```

Essentially:
We wait for the entire node execution in a non-streaming way, without directly yielding the tokens. And then do fake streaming from the last message. This achieves the result what you want while making sure entire text has been passed through PII Middleware.

**darfaz:**
This is a critical issue — streaming that bypasses guardrails essentially negates the security layer entirely. The data is already exposed to the user before the middleware can block it.

The fake-streaming workaround above works but sacrifices the UX benefit of streaming. A more robust pattern is to scan content in a buffered window during streaming — accumulate N tokens, scan the buffer, flush if clean, block if flagged.

[ClawMoat](https://github.com/darfaz/clawmoat) supports incremental/buffered scanning which could work well here — you can feed it chunks as they arrive and it maintains state across the stream, flagging as soon as a pattern is detected rather than waiting for the full response. This lets you preserve real streaming while still catching PII/injection mid-stream.

This is a broader architectural challenge though — any middleware system that runs as a post-processing step will have this problem with streaming. The fix likely needs to happen at the LangGraph/middleware architecture level to support streaming-aware middleware.

**keenborder786:**
Unfortunately this will involve a major architectural change in AgentMiddleware (if we are to avoid the above hacky solution that I have proposed), so let's keep this issue open.
CC: @sydney-runkle

**jackirvine97:**
Echo everything said above here - the docs push streaming as a recommended, supported pattern. As such, it should be a safe assumption that all major agent features are compatible with it. Happy to help be part of solution here!

I think it would be prudent to add a warning box to the docs - users right now could easily be mistaken and be one step closer to shipping a DP bug (though ofc they should catch this in testing!)

**vincentayorinde:**
This issue is more serious than a normal streaming bug because it breaks the expected enforcement point for output guardrails. If unsafe content is visible before middleware executes, users can incorrectly assume they are protected while sensitive data has already leaked.

I noticed #35470 is now open to address this. I will review it locally against the original reproduction and look for any remaining exposure across sync/async streaming and different output-handling strategies.

From a security standpoint, the invariant should be: **if output middleware is configured as protective, no raw streamed content should bypass it.**

**Alexxigang:**
I reproduced this locally with a fake streaming model and `PIIMiddleware`, and I can confirm the issue: raw streamed tokens are exposed before `after_model` middleware blocks or redacts them.

I'm working on a fix that buffers model ouI reproduced this locally with a fake streaming model and `PIIMiddleware`, and I can confirm the issue: raw streamed tokens are exposed before `after_model` middleware blocks or redacts them.

I'm working on a fix that buffers model output whenever `after_model` middleware is present, so `stream_mode="messages"` only emits content after the middleware chain has finished. I also plan to add regression tests for block/redact and sync/async streaming paths.tput whenever `after_model` middleware is present, so `stream_mode="messages"` only emits content after the middleware chain has finished. I also plan to add regression tests for block/redact and sync/async streaming paths.
