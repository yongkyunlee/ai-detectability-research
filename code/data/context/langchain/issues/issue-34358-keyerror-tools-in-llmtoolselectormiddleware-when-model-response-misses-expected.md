# 🐛 KeyError: 'tools' in LLMToolSelectorMiddleware when model response misses expected key

**Issue #34358** | State: open | Created: 2025-12-15 | Updated: 2026-03-18
**Author:** zhuweid
**Labels:** bug, core, langchain, openai, external

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
- [x] langchain-core
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
from langchain.agents import create_agent
from langchain.agents.middleware import LLMToolSelectorMiddleware
from langchain.tools import tool

@tool
def tool1(query: str) -> str:
    """Tool 1 description"""
    return "result1"

@tool
def tool2(query: str) -> str:
    """Tool 2 description"""
    return "result2"

@tool
def tool3(query: str) -> str:
    """Tool 3 description"""
    return "result3"

# Create middleware with max_tools limit
middleware = LLMToolSelectorMiddleware(max_tools=2)

# Create agent with middleware
agent = create_agent(
    model="openai: gpt-4o",
    tools=[tool1, tool2, tool3],
    middleware=[middleware],
)

# This intermittently fails with KeyError: 'tools'
response = await agent.ainvoke({"messages": [{"role": "user", "content":  "Help me with something"}]})
```

### Error Message and Stack Trace (if applicable)

```shell
File "C:\app\.venv\Lib\site-packages\langchain_core\runnables\base.py", line 1168, in astream
    yield await self.ainvoke(input, config, **kwargs)
          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\app\. venv\Lib\site-packages\langgraph\_internal\_runnable.py", line 473, in ainvoke
    ret = await self.afunc(*args, **kwargs)
          ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\app\.venv\Lib\site-packages\langchain\agents\factory.py", line 1189, in amodel_node
    response = await awrap_model_call_handler(request, _execute_model_async)
               ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\app\. venv\Lib\site-packages\langchain\agents\factory.py", line 277, in final_normalized
    final_result = await result(request, handler)
                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\app\. venv\Lib\site-packages\langchain\agents\factory.py", line 261, in composed
    outer_result = await outer(request, inner_handler)
                   ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
  File "C:\app\.venv\Lib\site-packages\langchain\agents\middleware\tool_selection.py", line 317, in awrap_model_call
    modified_request = self._process_selection_response(
        response, selection_request.available_tools, selection_request.valid_tool_names, request
    )
  File "C:\RAFM.Actuator\.venv\Lib\site-packages\langchain\agents\middleware\tool_selection.py", line 229, in _process_selection_response
    for tool_name in response["tools"]: 
                     ~~~~~~~~^^^^^^^^^
KeyError: 'tools'
```

### Description

* I'm using the LLMToolSelectorMiddleware to select relevant tools before the main model call in a LangChain agent. 
* I expect the agent to robustly handle tool selection, even if the LLM returns a malformed or incomplete response.
* Instead, the middleware occasionally raises a `KeyError: 'tools'` when the response from the LLM is missing the `"tools"` key. This happens intermittently and seems to be related to the LLM not strictly following the structured output schema, especially for complex or edge-case user prompts. The error interrupts all downstream processing and requires patching the middleware for resilience.

**Steps to reproduce:**
1. Set up a LangChain agent with the LLMToolSelectorMiddleware and at least 2+ tools.
2. Invoke the agent several times with different prompts. Some runs will intermittently fail with the KeyError if the LLM response structure is malformed. 

### System Info

python -m langchain_core.sys_info

OS:  Windows
Python version: 3.11+
LangChain: 1.1.3
langchain-core: (2024 or compatible)
langgraph: latest (as of Dec 2024)

## Comments

**suryaashish-tyke:**
Facing the same issue

**ccurme:**
I think what we want to do here is re-try the structured model invocation, then raise. If we fall back to all available tools (for example), performance may just silently degrade when something else is consistently wrong. If the issue is intermittent, a retry is probably a good bet.

**gitbalaji:**
Hi, I have an open PR (#35490) that fixes this issue. Could you please assign this to me? Happy to address any review feedback.
