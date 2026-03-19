# Tool calls sometimes fail due to missing positional argument

**Issue #34029** | State: open | Created: 2025-11-19 | Updated: 2026-03-05
**Author:** giltirn
**Labels:** documentation, bug, langchain, openai, external

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
- [x] langchain-openai
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
from langchain_openai import ChatOpenAI
from langchain.agents import create_agent
from langchain.tools import tool, ToolRuntime
from langchain.agents.middleware import wrap_tool_call, AgentState

llm = ChatOpenAI(
    model="Qwen3-8B-GGUF",
    openai_api_key="sk-local",  # Or a placeholder if required by the local server                                                                                                                                                                                   
    openai_api_base="http://localhost:8002/v1"
)

@tool
def addConfig(config: str, runtime: ToolRuntime):
    """                                                                                                                                                                                                                                                              
    Add a configuration file name to the list of configurations                                                                                                                                                                                                      
    Args:                                                                                                                                                                                                                                                            
       config: The file name, formatted as a path (relative or absolute)                                                                                                                                                                                             
    """
    print("(Dummy) Appending configuration ",config)

@wrap_tool_call
def printToolCalls(request, handler):
    print(request)
    return handler(request)

agent = create_agent(
    model=llm,
    tools=[addConfig],
    system_prompt="You are a helpful assistant.",
    middleware = [printToolCalls]
)

response = agent.invoke(
    {"messages": [{"role": "user", "content": "Add the configuration config.0"}]}
)
```

### Error Message and Stack Trace (if applicable)

```shell
Traceback (most recent call last):
  File "/home/ckelly/test/langchain/qcd_workflow/config_state/weird_err_reproducer/repro.py", line 36, in 
    response = agent.invoke(
        {"messages": [{"role": "user", "content": "Add the configuration config.0"}]}
    )
  File "/home/ckelly/miniconda3/envs/ai-py313/lib/python3.13/site-packages/langgraph/pregel/main.py", line 3050, in invoke
    for chunk in self.stream(
                 ~~~~~~~~~~~^
        input,
        ^^^^^^
    ......
        **kwargs,
        ^^^^^^^^^
    ):
    ^
  File "/home/ckelly/miniconda3/envs/ai-py313/lib/python3.13/site-packages/langgraph/pregel/main.py", line 2633, in stream
    for _ in runner.tick(
             ~~~~~~~~~~~^
        [t for t in loop.tasks.values() if not t.writes],
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    ......
        schedule_task=loop.accept_push,
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    ):
    ^
  File "/home/ckelly/miniconda3/envs/ai-py313/lib/python3.13/site-packages/langgraph/pregel/_runner.py", line 167, in tick
    run_with_retry(
    ~~~~~~~~~~~~~~^
        t,
        ^^
    ......
        },
        ^^
    )
    ^
  File "/home/ckelly/miniconda3/envs/ai-py313/lib/python3.13/site-packages/langgraph/pregel/_retry.py", line 42, in run_with_retry
    return task.proc.invoke(task.input, config)
           ~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^
  File "/home/ckelly/miniconda3/envs/ai-py313/lib/python3.13/site-packages/langgraph/_internal/_runnable.py", line 656, in invoke
    input = context.run(step.invoke, input, config, **kwargs)
  File "/home/ckelly/miniconda3/envs/ai-py313/lib/python3.13/site-packages/langgraph/_internal/_runnable.py", line 400, in invoke
    ret = self.func(*args, **kwargs)
  File "/home/ckelly/miniconda3/envs/ai-py313/lib/python3.13/site-packages/langgraph/prebuilt/tool_node.py", line 727, in _func
    outputs = list(
        executor.map(self._run_one, tool_calls, input_types, tool_runtimes)
    )
  File "/home/ckelly/miniconda3/envs/ai-py313/lib/python3.13/concurrent/futures/_base.py", line 619, in result_iterator
    yield _result_or_cancel(fs.pop())
          ~~~~~~~~~~~~~~~~~^^^^^^^^^^
  File "/home/ckelly/miniconda3/envs/ai-py313/lib/python3.13/concurrent/futures/_base.py", line 317, in _result_or_cancel
    return fut.result(timeout)
           ~~~~~~~~~~^^^^^^^^^
  File "/home/ckelly/miniconda3/envs/ai-py313/lib/python3.13/concurrent/futures/_base.py", line 456, in result
    return self.__get_result()
           ~~~~~~~~~~~~~~~~~^^
  File "/home/ckelly/miniconda3/envs/ai-py313/lib/python3.13/concurrent/futures/_base.py", line 401, in __get_result
    raise self._exception
  File "/home/ckelly/miniconda3/envs/ai-py313/lib/python3.13/concurrent/futures/thread.py", line 59, in run
    result = self.fn(*self.args, **self.kwargs)
  File "/home/ckelly/miniconda3/envs/ai-py313/lib/python3.13/site-packages/langchain_core/runnables/config.py", line 546, in _wrapped_fn
    return contexts.pop().run(fn, *args)
           ~~~~~~~~~~~~~~~~~~^^^^^^^^^^^
  File "/home/ckelly/miniconda3/envs/ai-py313/lib/python3.13/site-packages/langgraph/prebuilt/tool_node.py", line 957, in _run_one
    content = _handle_tool_error(e, flag=self._handle_tool_errors)
  File "/home/ckelly/miniconda3/envs/ai-py313/lib/python3.13/site-packages/langgraph/prebuilt/tool_node.py", line 404, in _handle_tool_error
    content = flag(e)  # type: ignore [assignment, call-arg]
  File "/home/ckelly/miniconda3/envs/ai-py313/lib/python3.13/site-packages/langgraph/prebuilt/tool_node.py", line 361, in _default_handle_tool_errors
    raise e
  File "/home/ckelly/miniconda3/envs/ai-py313/lib/python3.13/site-packages/langgraph/prebuilt/tool_node.py", line 951, in _run_one
    return self._wrap_tool_call(tool_request, execute)
           ~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/ckelly/miniconda3/envs/ai-py313/lib/python3.13/site-packages/langchain/agents/middleware/types.py", line 1604, in wrapped
    return func(request, handler)
  File "/home/ckelly/test/langchain/qcd_workflow/config_state/weird_err_reproducer/repro.py", line 27, in printToolCalls
    return handler(request)
  File "/home/ckelly/miniconda3/envs/ai-py313/lib/python3.13/site-packages/langgraph/prebuilt/tool_node.py", line 947, in execute
    return self._execute_tool_sync(req, input_type, config)
           ~~~~~~~~~~~~~~~~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^^^^
  File "/home/ckelly/miniconda3/envs/ai-py313/lib/python3.13/site-packages/langgraph/prebuilt/tool_node.py", line 891, in _execute_tool_sync
    content = _handle_tool_error(e, flag=self._handle_tool_errors)
  File "/home/ckelly/miniconda3/envs/ai-py313/lib/python3.13/site-packages/langgraph/prebuilt/tool_node.py", line 404, in _handle_tool_error
    content = flag(e)  # type: ignore [assignment, call-arg]
  File "/home/ckelly/miniconda3/envs/ai-py313/lib/python3.13/site-packages/langgraph/prebuilt/tool_node.py", line 361, in _default_handle_tool_errors
    raise e
  File "/home/ckelly/miniconda3/envs/ai-py313/lib/python3.13/site-packages/langgraph/prebuilt/tool_node.py", line 844, in _execute_tool_sync
    response = tool.invoke(call_args, config)
  File "/home/ckelly/miniconda3/envs/ai-py313/lib/python3.13/site-packages/langchain_core/tools/base.py", line 605, in invoke
    return self.run(tool_input, **kwargs)
           ~~~~~~~~^^^^^^^^^^^^^^^^^^^^^^
  File "/home/ckelly/miniconda3/envs/ai-py313/lib/python3.13/site-packages/langchain_core/tools/base.py", line 932, in run
    raise error_to_raise
  File "/home/ckelly/miniconda3/envs/ai-py313/lib/python3.13/site-packages/langchain_core/tools/base.py", line 898, in run
    response = context.run(self._run, *tool_args, **tool_kwargs)
  File "/home/ckelly/miniconda3/envs/ai-py313/lib/python3.13/site-packages/langchain_core/tools/structured.py", line 93, in _run
    return self.func(*args, **kwargs)
           ~~~~~~~~~^^^^^^^^^^^^^^^^^
TypeError: addConfig() missing 1 required positional argument: 'config'
During task with name 'tools' and id '947599f3-98b7-5563-3987-38d0d47f7223'
```

### Description

I am trying to use LangChain agents to assist in putting together a job plan / configuration for an HPC application. The simple tool call above consistently fails due to its positional argument being missing. By wrapping the tool call I confirm that the argument (config.0) is actually being passed to the tool correctly so the issue is happening at a lower level within the tool execution chain:

```
ToolCallRequest(tool_call={'name': 'addConfig', 'args': {'config': 'config.0'}, 'id': 'WnemfvoElnQZJnjhgfT7wlBvzWm1jNXt', 'type': 'tool_call'}, tool=StructuredTool(name='addConfig', description='Add a configuration file name to the list of configurations\nArgs:\n   config: The file name, formatted as a path (relative or absolute)', args_schema=, func=), state=...
```
**The issue appears to go away if the argument is renamed**. For example, with

```@tool
def addConfig(configf: str, runtime: ToolRuntime):
    """                                                                                                                                                                                                                                                              
    Add a configuration file name to the list of configurations                                                                                                                                                                                                      
    Args:                                                                                                                                                                                                                                                            
       configf: The file name, formatted as a path (relative or absolute)                                                                                                                                                                                             
    """
    print("(Dummy) Appending configuration ",configf)
```

the tool is executed correctly:

```
ToolCallRequest(tool_call={'name': 'addConfig', 'args': {'configf': 'config.0'}, 'id': 'L3kzDmy7D8bN0NtYdjTEcOXOlqqe4NQQ', 'type': 'tool_call'}, ...
...
...
(Dummy) Appending configuration  config.0
```
This suggests some sort of keyword / name collision somewhere within the bowels of the software.

### System Info

System Information
------------------
> OS:  Linux
> OS Version:  #15~22.04.1-Ubuntu SMP PREEMPT_DYNAMIC Fri Jan 12 18:54:30 UTC 2
> Python Version:  3.13.9 | packaged by Anaconda, Inc. | (main, Oct 21 2025, 19:16:10) [GCC 11.2.0]

Package Information
-------------------
> langchain_core: 1.0.6
> langchain: 1.0.8
> langchain_community: 0.4.1
> langsmith: 0.4.43
> langchain_classic: 1.0.0
> langchain_openai: 1.0.3
> langchain_text_splitters: 1.0.0
> langgraph_sdk: 0.2.9

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
> langgraph: 1.0.3
> numpy: 2.3.5
> openai: 2.8.1
> orjson: 3.11.4
> packaging: 25.0
> pydantic: 2.12.4
> pydantic-settings: 2.12.0
> pyyaml: 6.0.3
> PyYAML: 6.0.3
> requests: 2.32.5
> requests-toolbelt: 1.0.0
> sqlalchemy: 2.0.44
> SQLAlchemy: 2.0.44
> tenacity: 9.1.2
> tiktoken: 0.12.0
> typing-extensions: 4.15.0
> zstandard: 0.25.0

## Comments

**dumko2001:**
This is a known naming collision. The config argument name is reserved in LangChain's Runnable protocol to pass the RunnableConfig object (containing callbacks, tags, etc.) to the tool. When your function defines an argument named config, it shadows this internal parameter, causing the framework to inject the configuration object instead of the expected user input. Renaming the argument to something else (e.g., configuration or file_path) is the correct and necessary solution.

**giltirn:**
OK, I'm glad that it is known about. Is this documented anywhere? I did not come across it, and given that "config" is not an uncommon variable name (especially in my field), I would have thought this information would have more prominence. Might I suggest you go even further and either rename this internal variable to something less likely to have a collision (e.g. _langchain_internal_config) or perhaps just throw an error?

**dumko2001:**
@giltirn I decided to go ahead with your suggestion to strictly validate this in the code.

I've opened PR #34112 which adds a "fail fast" check. If config is used as an argument name, it will now raise a clear ValueError immediately at definition time (explaining the name collision) rather than crashing silently at runtime.

**JiwaniZakir:**
Picked this up -- working on a fix now. I'll include a test to prevent regression.

**JiwaniZakir:**
Picked this up -- working on a fix now. I'll include a test to prevent regression.

**JiwaniZakir:**
PR is up: https://github.com/langchain-ai/langchain/pull/35579
