# RunnableWithFallbacks.invoke() drops parent_run_id for child callback events (regression from #25550)

**Issue #36072** | State: open | Created: 2026-03-18 | Updated: 2026-03-18
**Author:** AnkushMalaker
**Labels:** bug, core, external

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
- [ ] langchain-openrouter
- [ ] langchain-perplexity
- [ ] langchain-qdrant
- [ ] langchain-xai
- [ ] Other / not sure / general

### Related Issues / PRs

#25337 — Original bug report (callbacks not firing in fallbacks), closed by #25550                                               
#25550 — PR that introduced this regression (passed config instead of child_config)                                              

### Reproduction Steps / Example Code (Python)

```python
from langchain_openai import ChatOpenAI                                                                                            
from langchain_core.callbacks.base import BaseCallbackHandler 
from langchain_core.messages import HumanMessage                                                                                   
                                                                                
                                                                                                                                    
class Tracker(BaseCallbackHandler):                                                                                                
    def __init__(self):
        self.events = []

    def on_chain_start(self, serialized, inputs, *, run_id, parent_run_id=None, **kwargs):
        self.events.append(("chain_start", run_id, parent_run_id))

    def on_chat_model_start(self, serialized, messages, *, run_id, parent_run_id=None, **kwargs):
        self.events.append(("chat_model_start", run_id, parent_run_id))

    def on_llm_error(self, error, *, run_id, parent_run_id=None, **kwargs):
        self.events.append(("llm_error", run_id, parent_run_id))

tracker = Tracker()
llm = ChatOpenAI(model="gpt-4o-mini", api_key="sk-bad").with_fallbacks(
    [ChatOpenAI(model="gpt-4o-mini", api_key="sk-bad-2")]
)

try:
    llm.invoke([HumanMessage(content="hi")], config={"callbacks": [tracker]})
except Exception:
    pass

chain_run_id = tracker.events[0][1]  # run_id from chain_start
for event_name, run_id, parent_run_id in tracker.events:
    if event_name in ("chat_model_start", "llm_error"):
        assert parent_run_id == chain_run_id, (
            f"{event_name}: expected parent_run_id={chain_run_id}, got {parent_run_id}"
        )
```

### Error Message and Stack Trace (if applicable)

```shell

```

### Description

RunnableWithFallbacks.invoke() passes config instead of child_config to child runnables (line 196 of
fallbacks.py). This causes child callback events (on_chat_model_start, on_llm_error, on_llm_end) to
receive parent_run_id=None instead of the fallback chain's run_id.

This breaks any tracing/observability tool that relies on parent_run_id to build span trees — child LLM
spans become orphans invisible to the trace.

Regression introduced by #25550. Fix is one line — change config to child_config:
```
                child_config = patch_config(config, callbacks=run_manager.get_child())
                with set_config_context(child_config) as context:
                    output = context.run(
                        runnable.invoke,
                        input,
-                        config,
+                        child_config,
                        **kwargs,
                    )
```
Same issue likely applies to ainvoke, batch, and abatch.

### System Info

>>> from langchain_core import sys_info
>>> sys_info.print_sys_info()

System Information
------------------
> OS:  Darwin
> OS Version:  Darwin Kernel Version 25.3.0: Wed Jan 28 20:56:35 PST 2026; root:xnu-12377.91.3~2/RELEASE_ARM64_T6030
> Python Version:  3.12.8 (main, Dec  6 2024, 19:42:06) [Clang 18.1.8 ]

Package Information
-------------------
> langchain_core: 1.2.19
> langchain: 1.2.10
> langsmith: 0.7.9
> langchain_google_vertexai: 3.2.2
> langchain_openai: 1.1.10
> langchain_tests: 1.1.5
> langgraph_sdk: 0.3.9

Optional packages not installed
-------------------------------
> deepagents
> deepagents-cli

Other Dependencies
------------------
> bottleneck: 1.6.0
> google-cloud-aiplatform: 1.139.0
> google-cloud-storage: 3.9.0
> google-cloud-vectorsearch: 0.5.0
> httpx: 0.28.1
> httpx-sse: 0.4.3
> jsonpatch: 1.33
> langgraph: 1.0.10
> numexpr: 2.14.1
> numpy: 2.4.2
> openai: 2.29.0
> openai-agents: 0.12.4
> opentelemetry-api: 1.39.1
> opentelemetry-exporter-otlp-proto-http: 1.39.1
> opentelemetry-sdk: 1.39.1
> orjson: 3.11.7
> packaging: 26.0
> pyarrow: 22.0.0
> pydantic: 2.12.5
> pytest: 9.0.2
> pytest-asyncio: 1.3.0
> pytest-benchmark: 5.2.3
> pytest-codspeed: 4.3.0
> pytest-recording: 0.13.4
> pytest-socket: 0.7.0
> pyyaml: 6.0.3
> requests: 2.32.5
> requests-toolbelt: 1.0.0
> rich: 14.3.3
> syrupy: 5.1.0
> tenacity: 9.1.4
> tiktoken: 0.12.0
> typing-extensions: 4.15.0
> uuid-utils: 0.14.1
> validators: 0.35.0
> vcrpy: 8.1.1
> websockets: 16.0
> wrapt: 1.17.3
> xxhash: 3.6.0
> zstandard: 0.25.0

## Comments

**LRRuan:**
Hi! I opened a fix for this issue here: https://github.com/langchain-ai/langchain/pull/36079

The PR was auto-closed because I am not assigned to the issue yet. Could a maintainer please assign me to #36072 so I can reopen the PR? Thanks!

**fairchildadrian9-create:**
This works for me now after the fix

On Wed, Mar 18, 2026, 7:41 AM LRRuan ***@***.***> wrote:

> *LRRuan* left a comment (langchain-ai/langchain#36072)
> 
>
> Hi! I opened a fix for this issue here: #36079
> 
>
> The PR was auto-closed because I am not assigned to the issue yet. Could a
> maintainer please assign me to #36072
>  so I can reopen
> the PR? Thanks!
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
