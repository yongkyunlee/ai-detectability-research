# `No data received from Ollama stream.` exception

**Issue #34918** | State: open | Created: 2026-01-29 | Updated: 2026-03-05
**Author:** khteh
**Labels:** bug, core, langchain, ollama, external

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
- [x] langchain-ollama
- [ ] langchain-perplexity
- [ ] langchain-prompty
- [ ] langchain-qdrant
- [ ] langchain-xai
- [ ] Other / not sure / general

### Related Issues / PRs

_No response_

### Reproduction Steps / Example Code (Python)

```python
async for stream_mode, data in self._agent.astream(
    {"messages": [{"role": "user", "content": message}]},
    stream_mode = modes, # Use this to stream all values in the state after each step.
    config = config, # This is needed by Checkpointer
    subgraphs = subgraphs
):
    logging.debug(f"stream_mode: {stream_mode}")
    if stream_mode == "values":
        messages.append(data["messages"][-1])
        data["messages"][-1].pretty_print()
```

### Error Message and Stack Trace (if applicable)

```shell
Traceback (most recent call last):
  File "/usr/src/Python/rag-agent/src/rag_agent/RAGAgent.py", line 249, in ChatAgent
    async for stream_mode, data in self._agent.astream( # The output of each step in the graph. The output shape depends on the stream_mode.
    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    ......
                    await output_queue.put(update) # Queue the state object. Not the message: update["messages"][-1]
                    ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/src/Python/rag-agent/.venv/lib/python3.13/site-packages/langgraph/pregel/main.py", line 2974, in astream
    async for _ in runner.atick(
    ......
            yield o
  File "/usr/src/Python/rag-agent/.venv/lib/python3.13/site-packages/langgraph/pregel/_runner.py", line 304, in atick
    await arun_with_retry(
    ......
    )
  File "/usr/src/Python/rag-agent/.venv/lib/python3.13/site-packages/langgraph/pregel/_retry.py", line 138, in arun_with_retry
    return await task.proc.ainvoke(task.input, config)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/src/Python/rag-agent/.venv/lib/python3.13/site-packages/langgraph/_internal/_runnable.py", line 705, in ainvoke
    input = await asyncio.create_task(
            ^^^^^^^^^^^^^^^^^^^^^^^^^^
        step.ainvoke(input, config, **kwargs), context=context
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    )
    ^
  File "/usr/src/Python/rag-agent/.venv/lib/python3.13/site-packages/langgraph/_internal/_runnable.py", line 473, in ainvoke
    ret = await self.afunc(*args, **kwargs)
          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/src/Python/rag-agent/.venv/lib/python3.13/site-packages/langchain/agents/factory.py", line 1224, in amodel_node
    response = await awrap_model_call_handler(request, _execute_model_async)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/src/Python/rag-agent/.venv/lib/python3.13/site-packages/langchain/agents/factory.py", line 303, in final_normalized
    final_result = await result(request, handler)
                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/src/Python/rag-agent/.venv/lib/python3.13/site-packages/langchain/agents/factory.py", line 287, in composed
    outer_result = await outer(request, inner_handler)
                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/src/Python/rag-agent/.venv/lib/python3.13/site-packages/langchain/agents/middleware/todo.py", line 248, in awrap_model_call
    return await handler(request.override(system_message=new_system_message))
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/src/Python/rag-agent/.venv/lib/python3.13/site-packages/langchain/agents/factory.py", line 283, in inner_handler
    inner_result = await inner(req, handler)
                   ^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/src/Python/rag-agent/.venv/lib/python3.13/site-packages/langchain/agents/factory.py", line 287, in composed
    outer_result = await outer(request, inner_handler)
                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/src/Python/rag-agent/.venv/lib/python3.13/site-packages/deepagents/middleware/filesystem.py", line 1029, in awrap_model_call
    return await handler(request)
           ^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/src/Python/rag-agent/.venv/lib/python3.13/site-packages/langchain/agents/factory.py", line 283, in inner_handler
    inner_result = await inner(req, handler)
                   ^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/src/Python/rag-agent/.venv/lib/python3.13/site-packages/langchain/agents/factory.py", line 287, in composed
    outer_result = await outer(request, inner_handler)
                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/src/Python/rag-agent/.venv/lib/python3.13/site-packages/deepagents/middleware/subagents.py", line 557, in awrap_model_call
    return await handler(request.override(system_message=new_system_message))
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/src/Python/rag-agent/.venv/lib/python3.13/site-packages/langchain/agents/factory.py", line 283, in inner_handler
    inner_result = await inner(req, handler)
                   ^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/src/Python/rag-agent/.venv/lib/python3.13/site-packages/langchain_anthropic/middleware/prompt_caching.py", line 140, in awrap_model_call
    return await handler(request)
           ^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/src/Python/rag-agent/.venv/lib/python3.13/site-packages/langchain/agents/factory.py", line 1192, in _execute_model_async
    output = await model_.ainvoke(messages)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/usr/src/Python/rag-agent/.venv/lib/python3.13/site-packages/langchain_core/runnables/base.py", line 5570, in ainvoke
    return await self.bound.ainvoke(
           ^^^^^^^^^^^^^^^^^^^^^^^^^
    ......
    )
    ^
  File "/usr/src/Python/rag-agent/.venv/lib/python3.13/site-packages/langchain_core/language_models/chat_models.py", line 425, in ainvoke
    llm_result = await self.agenerate_prompt(
                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    ......
    )
    ^
  File "/usr/src/Python/rag-agent/.venv/lib/python3.13/site-packages/langchain_core/language_models/chat_models.py", line 1132, in agenerate_prompt
    return await self.agenerate(
           ^^^^^^^^^^^^^^^^^^^^^
        prompt_messages, stop=stop, callbacks=callbacks, **kwargs
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    )
    ^
  File "/usr/src/Python/rag-agent/.venv/lib/python3.13/site-packages/langchain_core/language_models/chat_models.py", line 1090, in agenerate
    raise exceptions[0]
  File "/usr/src/Python/rag-agent/.venv/lib/python3.13/site-packages/langchain_core/language_models/chat_models.py", line 1359, in _agenerate_with_cache
    result = await self._agenerate(
             ^^^^^^^^^^^^^^^^^^^^^^
        messages, stop=stop, run_manager=run_manager, **kwargs
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    )
    ^
  File "/usr/src/Python/rag-agent/.venv/lib/python3.13/site-packages/langchain_ollama/chat_models.py", line 1208, in _agenerate
    final_chunk = await self._achat_stream_with_aggregation(
                  ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
        messages, stop, run_manager, verbose=self.verbose, **kwargs
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    )
    ^
  File "/usr/src/Python/rag-agent/.venv/lib/python3.13/site-packages/langchain_ollama/chat_models.py", line 1004, in _achat_stream_with_aggregation
    raise ValueError(msg)
ValueError: No data received from Ollama stream.
During task with name 'model' and id '0087e180-6d26-4f5b-b507-8784d005cd77'
```

### Description

deepagent RAG using ollama with gpt-oss LLM model sometimes hit this kind of error.

### System Info

```
System Information
------------------
> OS:  Linux
> OS Version:  #8-Ubuntu SMP PREEMPT_DYNAMIC Fri Nov 14 21:44:46 UTC 2025
> Python Version:  3.13.7 (main, Jan  8 2026, 12:15:45) [GCC 15.2.0]

Package Information
-------------------
> langchain_core: 1.2.7
> langchain: 1.2.7
> langchain_community: 0.4.1
> langsmith: 0.6.5
> langchain_anthropic: 1.3.1
> langchain_classic: 1.0.1
> langchain_google_genai: 4.2.0
> langchain_neo4j: 0.8.0
> langchain_ollama: 1.0.1
> langchain_postgres: 0.0.16
> langchain_text_splitters: 1.1.0
> langgraph_api: 0.7.9
> langgraph_cli: 0.4.12
> langgraph_runtime_inmem: 0.23.1
> langgraph_sdk: 0.3.3

Optional packages not installed
-------------------------------
> langserve

Other Dependencies
------------------
> aiohttp: 3.13.3
> anthropic: 0.76.0
> asyncpg: 0.31.0
> blockbuster: 1.5.26
> click: 8.3.1
> cloudpickle: 3.1.2
> cryptography: 46.0.3
> dataclasses-json: 0.6.7
> filetype: 1.2.0
> google-genai: 1.60.0
> grpcio: 1.76.0
> grpcio-health-checking: 1.76.0
> grpcio-tools: 1.75.1
> httpx: 0.28.1
> httpx-sse: 0.4.3
> jsonpatch: 1.33
> jsonschema-rs: 0.29.1
> langgraph: 1.0.7
> langgraph-checkpoint: 4.0.0
> neo4j: 6.1.0
> neo4j-graphrag: 1.12.0
> numpy: 2.4.1
> ollama: 0.6.1
> opentelemetry-api: 1.39.1
> opentelemetry-exporter-otlp-proto-http: 1.39.1
> opentelemetry-sdk: 1.39.1
> orjson: 3.11.5
> packaging: 25.0
> pgvector: 0.3.6
> protobuf: 6.33.4
> psycopg: 3.3.2
> psycopg-pool: 3.3.0
> pydantic: 2.12.5
> pydantic-settings: 2.12.0
> pyjwt: 2.10.1
> pytest: 9.0.2
> python-dotenv: 1.2.1
> pyyaml: 6.0.3
> PyYAML: 6.0.3
> requests: 2.32.5
> requests-toolbelt: 1.0.0
> sqlalchemy: 2.0.46
> SQLAlchemy: 2.0.46
> sse-starlette: 2.1.3
> starlette: 0.50.0
> structlog: 25.5.0
> tenacity: 9.1.2
> truststore: 0.10.4
> typing-extensions: 4.15.0
> uuid-utils: 0.14.0
> uvicorn: 0.40.0
> watchfiles: 1.1.1
> zstandard: 0.25.0
```

## Comments

**nikhildoifode:**
+1

**Austinae:**
+1

**baptmerciv:**
+1
