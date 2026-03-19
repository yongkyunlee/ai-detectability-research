# Error in create_agent() when enable "messages" streaming mode: 'Error:  is not a valid tool'

**Issue #34654** | State: open | Created: 2026-01-08 | Updated: 2026-03-09
**Author:** Smpests
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
- [ ] langchain-cli
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

### Example Code (Python)

```python
from langgraph.config import get_stream_writer
from langchain_openai import ChatOpenAI
from langchain.agents import create_agent
from langchain.messages import AIMessageChunk, AIMessage, AnyMessage, ToolMessage

from agent.config import settings

def get_weather(city: str) -> str:
    """Get weather for a given city."""

    return f"It's always sunny in {city}!"

llm = ChatOpenAI(
    base_url=settings.llm.base_url,
    api_key=settings.llm.api_key.get_secret_value(),
    model="gpt-4o",
)

agent = create_agent(
    model=llm,
    tools=[get_weather],
)

def _render_message_chunk(token: AIMessageChunk) -> None:
    if token.text:
        print(token.text, end="|")
    if token.tool_call_chunks:
        print(token.tool_call_chunks)

def _render_completed_message(message: AnyMessage) -> None:
    if isinstance(message, AIMessage) and message.tool_calls:
        print(f"Tool calls: {message.tool_calls}")
    if isinstance(message, ToolMessage):
        print(f"Tool response: {message.content_blocks}")

input_message = {"role": "user", "content": "What is the weather in Boston?"}
for stream_mode, data in agent.stream(
        {"messages": [input_message]},
        stream_mode=["messages", "updates", "custom"],
):
    if stream_mode == "messages":
        token, metadata = data
        if isinstance(token, AIMessageChunk):
            _render_message_chunk(token)
    if stream_mode == "updates":
        for source, update in data.items():
            if source in ("model", "tools"):
                _render_completed_message(update["messages"][-1])
    if stream_mode == "custom":
        # access completed message in stream
        print(f"Tool calls: {data.tool_calls}")
```

### Error Message and Stack Trace (if applicable)

```shell
!!!!!!!!!!!!!!!!!!! Interrupted: 1 error during collection !!!!!!!!!!!!!!!!!!!!
============================== 1 error in 8.98s ===============================
[{'name': 'get_weather', 'args': '', 'id': 'call_bc4a6fa73fe443b88c566a45', 'index': None, 'type': 'tool_call_chunk'}]
[{'name': '', 'args': '', 'id': 'call_bc4a6fa73fe443b88c566a45', 'index': None, 'type': 'tool_call_chunk'}]
[{'name': '', 'args': '{"city": "Boston', 'id': '', 'index': None, 'type': 'tool_call_chunk'}]
[{'name': '', 'args': '"', 'id': '', 'index': None, 'type': 'tool_call_chunk'}]
[{'name': None, 'args': '}', 'id': '', 'index': None, 'type': 'tool_call_chunk'}]
Tool calls: [{'name': 'get_weather', 'args': {}, 'id': 'call_bc4a6fa73fe443b88c566a45', 'type': 'tool_call'}, {'name': '', 'args': {}, 'id': 'call_bc4a6fa73fe443b88c566a45', 'type': 'tool_call'}, {'name': '', 'args': {'city': 'Boston'}, 'id': '', 'type': 'tool_call'}]
Tool response: [{'type': 'text', 'text': 'Error:  is not a valid tool, try one of [get_weather].'}]
Tool response: [{'type': 'text', 'text': "Error invoking tool 'get_weather' with kwargs {} with error:\n city: Field required\n Please fix the error and try again."}]
Tool response: [{'type': 'text', 'text': 'Error:  is not a valid tool, try one of [get_weather].'}]

tests/test_agent.py:None (tests/test_agent.py)
test_agent.py:42: in 
    for stream_mode, data in agent.stream(
..\.venv\Lib\site-packages\langgraph\pregel\main.py:2643: in stream
    for _ in runner.tick(
..\.venv\Lib\site-packages\langgraph\pregel\_runner.py:258: in tick
    _panic_or_proceed(
..\.venv\Lib\site-packages\langgraph\pregel\_runner.py:520: in _panic_or_proceed
    raise exc
..\.venv\Lib\site-packages\langgraph\pregel\_executor.py:80: in done
    task.result()
..\..\..\..\AppData\Roaming\uv\python\cpython-3.12.11-windows-x86_64-none\Lib\concurrent\futures\_base.py:449: in result
    return self.__get_result()
           ^^^^^^^^^^^^^^^^^^^
..\..\..\..\AppData\Roaming\uv\python\cpython-3.12.11-windows-x86_64-none\Lib\concurrent\futures\_base.py:401: in __get_result
    raise self._exception
..\..\..\..\AppData\Roaming\uv\python\cpython-3.12.11-windows-x86_64-none\Lib\concurrent\futures\thread.py:59: in run
    result = self.fn(*self.args, **self.kwargs)
             ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
..\.venv\Lib\site-packages\langgraph\pregel\_retry.py:42: in run_with_retry
    return task.proc.invoke(task.input, config)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
..\.venv\Lib\site-packages\langgraph\_internal\_runnable.py:656: in invoke
    input = context.run(step.invoke, input, config, **kwargs)
            ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
..\.venv\Lib\site-packages\langgraph\_internal\_runnable.py:400: in invoke
    ret = self.func(*args, **kwargs)
          ^^^^^^^^^^^^^^^^^^^^^^^^^^
..\.venv\Lib\site-packages\langchain\agents\factory.py:1130: in model_node
    response = _execute_model_sync(request)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^
..\.venv\Lib\site-packages\langchain\agents\factory.py:1101: in _execute_model_sync
    output = model_.invoke(messages)
             ^^^^^^^^^^^^^^^^^^^^^^^
..\.venv\Lib\site-packages\langchain_core\runnables\base.py:5557: in invoke
    return self.bound.invoke(
..\.venv\Lib\site-packages\langchain_core\language_models\chat_models.py:398: in invoke
    self.generate_prompt(
..\.venv\Lib\site-packages\langchain_core\language_models\chat_models.py:1117: in generate_prompt
    return self.generate(prompt_messages, stop=stop, callbacks=callbacks, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
..\.venv\Lib\site-packages\langchain_core\language_models\chat_models.py:927: in generate
    self._generate_with_cache(
..\.venv\Lib\site-packages\langchain_core\language_models\chat_models.py:1178: in _generate_with_cache
    for chunk in self._stream(messages, stop=stop, **kwargs):
                 ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
..\.venv\Lib\site-packages\langchain_openai\chat_models\base.py:1294: in _stream
    response = self.client.create(**payload)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
..\.venv\Lib\site-packages\openai\_utils\_utils.py:286: in wrapper
    return func(*args, **kwargs)
           ^^^^^^^^^^^^^^^^^^^^^
..\.venv\Lib\site-packages\openai\resources\chat\completions\completions.py:1192: in create
    return self._post(
..\.venv\Lib\site-packages\openai\_base_client.py:1259: in post
    return cast(ResponseT, self.request(cast_to, opts, stream=stream, stream_cls=stream_cls))
                           ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
..\.venv\Lib\site-packages\openai\_base_client.py:1047: in request
    raise self._make_status_error_from_response(err.response) from None
E   openai.UnprocessableEntityError: Error code: 422 - {'detail': [{'type': 'string_type', 'loc': ['body', 'messages', 1, 'tool_calls', 4, 'function', 'name'], 'msg': 'Input should be a valid string', 'input': None, 'url': 'https://errors.pydantic.dev/2.4/v/string_type'}]}
E   During task with name 'model' and id 'c972124e-efca-88a3-503b-e511a486fe97'

Process finished with exit code 2
```

### Description

I'm trying the example streaming code from [langchain offical docs](https://docs.langchain.com/oss/python/langchain/streaming)
We expected the same result with the example but  got an error. Please check the error messages.
We found that an error occurs when "stream_mode" is enabled with "messages". From the logs, it seems that the program is unable to generate the correct parameters when calling the tool.

Any suggestions, Thanks.

### System Info

sys_info.print_sys_info()
System Information
------------------
> OS:  Windows
> OS Version:  10.0.22631
> Python Version:  3.12.11 (main, Jul 23 2025, 00:32:20) [MSC v.1944 64 bit (AMD64)]
Package Information
-------------------
> langchain_core: 1.2.5
> langchain: 1.2.2
> langchain_community: 0.4.1
> langsmith: 0.4.58
> langchain_classic: 1.0.0
> langchain_mcp_adapters: 0.2.1
> langchain_openai: 1.1.6
> langchain_text_splitters: 1.0.0
> langgraph_sdk: 0.3.1
Optional packages not installed
-------------------------------
> langserve
Other Dependencies
------------------
> aiohttp: 3.13.2
> dataclasses-json: 0.6.7
> httpx: 0.28.1
> httpx-sse: 0.4.3
> jsonpatch: 1.33
> langgraph: 1.0.5
> mcp: 1.24.0
> numpy: 2.3.5
> openai: 2.9.0
> orjson: 3.11.5
> packaging: 25.0
> pydantic: 2.12.5
> pydantic-settings: 2.12.0
> pytest: 9.0.2
> PyYAML: 6.0.3
> pyyaml: 6.0.3
> requests: 2.32.5
> requests-toolbelt: 1.0.0
> SQLAlchemy: 2.0.45
> sqlalchemy: 2.0.45
> tenacity: 9.1.2
> tiktoken: 0.12.0
> typing-extensions: 4.15.0
> uuid-utils: 0.12.0
> zstandard: 0.25.0

## Comments

**aankur-kumar777:**
I can confirm this is reproducible on latest versions and appears to be a LangChain streaming bug, not user code.

When using agent.stream() with stream_mode=["messages", "updates"], the messages stream emits malformed tool_call_chunks:
- > empty or None tool names
- > arguments split across chunks

These malformed chunks are later re-assembled into invalid tool_calls, which causes the OpenAI API to reject the request with:
- >  422 UnprocessableEntityError:
- > Input should be a valid string at tool_calls[].function.name

**Expected behavior**
The tool call (name + args) should only be considered valid once fully assembled, or only surfaced via the updates / values stream (as shown in the docs).

**Workaround**
Avoid reading tool calls from the messages stream. Instead:
- > use stream_mode="updates" or
- > stream_mode="values" and read state["messages"][-1].tool_calls
This aligns with the streaming examples in the LangChain docs.

**Likely root cause**
Partial tool_call_chunks from the token stream are being promoted into final tool_calls without validation or merging, resulting in empty function.name values.

Happy to help with a fix or test if needed.

**SeasonPilot:**
Thank you for the detailed reproduction steps and stack trace. It appears that this error is not caused by `create_agent()` itself "selecting the wrong tool", but rather by an issue with merging streaming chunks when using `stream_mode="messages"` alongside tool calling. This results in invalid tool calls appearing in the next round of requests.

From the exception, the backend (OpenAI or an OpenAI-compatible service) returned a 422 error while validating the request body: `tool_calls[*].function.name` received a `None` value (it must be a string). This typically occurs during streaming: tool calls are returned as multiple incremental chunks,
where the `name` field in subsequent chunks is allowed to be `None`. The system relies on the `index` field to merge these chunks back into a single valid tool call. If the `index` field is missing or its type does not match expectations (a common issue is OpenAI-compatible backends returning the `index` as the string "0", or intermittently omitting the field entirely),
the merging process fails. LangChain then retains these fragments as multiple (invalid) tool calls, and when serializing and sending them in the next round, the `name=None` value is included—triggering the 422 error you observed.

Could you please help confirm/supplement the following two pieces of information to identify whether LangChain needs a compatibility fallback, or if the backend streaming format is incompatible:

1. Does your `base_url` point to the official OpenAI service or an OpenAI-compatible service? (You may redact the domain name)
2. When the error occurs, print the value of `AIMessageChunk.tool_call_chunks` (especially the value and type of `index`), for example:

```python
from langchain.messages import AIMessageChunk

for stream_mode, data in agent.stream({"messages":[input_message]}, stream_mode=["messages"]):
    if stream_mode == "messages":
        token, meta = data
        if isinstance(token, AIMessageChunk) and token.tool_call_chunks:
            for tc in token.tool_call_chunks:
                print(tc, type(tc.get("index")))
```

Temporary workaround solutions:

- First, use `stream_mode="updates"` (this bypasses token-level streaming and usually avoids triggering the issue); or
- Disable streaming for the model: `ChatOpenAI(..., streaming=False)` / `disable_streaming="tool_calling"` (prevents streaming from being used in tool-calling scenarios).

If you confirm that the `index` is indeed returned as a string (e.g., "0"), we can implement a compatibility fix in the streaming delta parsing logic of `langchain-openai` (normalizing parseable numeric strings to integers, and preventing invalid tool calls with `name=None` from being sent back to the API), thus avoiding this 422 error.

**686f6c61:**
Hi @Smpests, @aankur-kumar777, and @SeasonPilot,

Thank you for reporting this issue and the helpful discussion. We encountered the same problem in our own streaming implementation, which motivated us to investigate and develop a solution. Your clear reproduction example made it much easier to track down and fix the root cause.

I've investigated the problem and found the root cause: the `merge_lists()` function in `langchain_core/utils/_merge.py` wasn't handling `tool_call_chunks` correctly when the `index` field was `None`. This caused chunks not to merge and created multiple partial tool calls with empty names, resulting in the 422 errors you reported.

## Solution implemented

I've created PR #34671 with a fix that modifies the merging logic to handle these cases:

1. **Chunks with same id**: If a chunk has `index=None` but keeps the same non-empty `id`, it merges with the corresponding chunk
2. **Sequential chunks without id**: For chunks that lose their `id` (like subsequent argument chunks), they merge sequentially with the last `tool_call_chunk` in the list
3. **Preserves existing behavior**: Chunks with valid `index` continue working as before

The logic only merges chunks that are clearly fragments (empty name), to avoid mixing different tool calls.

## Tests

I've added comprehensive tests covering:
- The exact scenario you reported
- Multiple simultaneous tool calls with different ids
- Interleaved chunks between different tool calls
- Sequential merging when id is lost

All existing tests pass without regression (1573 tests).

## Verification

I reproduced the issue with the example code you provided and confirmed the solution resolves it completely. Chunks now merge correctly into a single valid tool call with complete name and arguments.

Additionally verified compatibility with:
- OpenAI streaming pattern (index=None with empty name/id in continuations)
- Anthropic streaming pattern (valid index with name=None, id=None in continuations)

The PR is ready for review. If you need any adjustments or have questions, I'm happy to make them.

Thanks again for the detailed report and to the LangChain team for maintaining this project!

**Smpests:**
> Thank you for the detailed reproduction steps and stack trace. It appears that this error is not caused by `create_agent()` itself "selecting the wrong tool", but rather by an issue with merging streaming chunks when using `stream_mode="messages"` alongside tool calling. This results in invalid tool calls appearing in the next round of requests.
> 
> From the exception, the backend (OpenAI or an OpenAI-compatible service) returned a 422 error while validating the request body: `tool_calls[*].function.name` received a `None` value (it must be a string). This typically occurs during streaming: tool calls are returned as multiple incremental chunks, where the `name` field in subsequent chunks is allowed to be `None`. The system relies on the `index` field to merge these chunks back into a single valid tool call. If the `index` field is missing or its type does not match expectations (a common issue is OpenAI-compatible backends returning the `index` as the string "0", or intermittently omitting the field entirely), the merging process fails. LangChain then retains these fragments as multiple (invalid) tool calls, and when serializing and sending them in the next round, the `name=None` value is included—triggering the 422 error you observed.
> 
> Could you please help confirm/supplement the following two pieces of information to identify whether LangChain needs a compatibility fallback, or if the backend streaming format is incompatible:
> 
> 1. Does your `base_url` point to the official OpenAI service or an OpenAI-compatible service? (You may redact the domain name)
> 2. When the error occurs, print the value of `AIMessageChunk.tool_call_chunks` (especially the value and type of `index`), for example:
> 
> from langchain.messages import AIMessageChunk
> 
> for stream_mode, data in agent.stream({"messages":[input_message]}, stream_mode=["messages"]):
>     if stream_mode == "messages":
>         token, meta = data
>         if isinstance(token, AIMessageChunk) and token.tool_call_chunks:
>             for tc in token.tool_call_chunks:
>                 print(tc, type(tc.get("index")))
> Temporary workaround solutions:
> 
> * First, use `stream_mode="updates"` (this bypasses token-level streaming and usually avoids triggering the issue); or
> * Disable streaming for the model: `ChatOpenAI(..., streaming=False)` / `disable_streaming="tool_calling"` (prevents streaming from being used in tool-calling scenarios).
> 
> If you confirm that the `index` is indeed returned as a string (e.g., "0"), we can implement a compatibility fix in the streaming delta parsing logic of `langchain-openai` (normalizing parseable numeric strings to integers, and preventing invalid tool calls with `name=None` from being sent back to the API), thus avoiding this 422 error.

Thanks for your solutions, and for your information:
1. Our `base_url` point to a self-hosted OpenAI-compatible service.
2. The data type of `index` is `NoneType`.

**Smpests:**
Thank you all! Based on your suggestions, we finally found the cause.
In our self-hosted OpenAI-Compatible service, our tool calling response does not include the `index` property.

**686f6c61:**
Thanks for the feedback @Smpests! This confirms the fix in PR #34671 addresses your use case with self-hosted OpenAI-compatible services.

**repeating:**
hey, i'd like to take this on — the previous PR was abandoned so i'll open a fresh one with a fix for the index=None merging in merge_lists
