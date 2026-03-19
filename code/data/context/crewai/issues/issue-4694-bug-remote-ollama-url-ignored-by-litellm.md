# [BUG] Remote Ollama url ignored by litellm

**Issue #4694** | State: open | Created: 2026-03-04 | Updated: 2026-03-04
**Author:** Killian-fal
**Labels:** bug

### Description

When using CrewAI with a remote Ollama server (not localhost) and a Task with output_pydantic, two failures occur:

1. The api_base/base_url is not forward to LiteLLM. Even though the LLM object is configured with a remote URL. (I analyse and found that InternalInstructor calls litellm.completion without those parameters, causing LiteLLM to fall back to http://localhost:11434)

2. LLM.supports_function_calling() always returns False for remote Ollama, because LiteLLM internally calls http://localhost:11434/api/show (ignoring api_base) to check model capabilities. This forces CrewAI to use the ReAct text-based loop instead of native function calling, even for models that fully support it.

### Steps to Reproduce

```python
from crewai import LLM, Agent, Task, Crew
from pydantic import BaseModel

class MyOutput(BaseModel):
    result: str

llm = LLM(
    model="ollama_chat/mistral-small3.2:24b",
    base_url="https://my-remote-ollama.example.com",
    api_base="https://my-remote-ollama.example.com",
)

agent = Agent(role="Assistant", goal="Answer", backstory="...", llm=llm)
task = Task(description="Say hello", expected_output="A greeting", agent=agent, output_pydantic=MyOutput)
crew = Crew(agents=[agent], tasks=[task])
crew.kickoff() # same with async
```

### Expected behavior

1. Bug 1 (api_base):
Use a remote Ollama server via base_url/api_base
Run the crew -> observe that InternalInstructor hits localhost:11434 instead of the remote URL

2. Bug 2 (supports_function_calling):
Use a remote Ollama server via base_url/api_base
Run the crew -> check llm.supports_function_calling() -> returns False even for models like mistral-small3.2 that natively support function calling

### Screenshots/Code snippets

X

### Operating System

Ubuntu 20.04

### Python Version

3.11

### crewAI Version

1.10.0

### crewAI Tools Version

1.10.0

### Virtual Environment

Venv

### Evidence

```

      litellm.APIConnectionError: Ollama_chatException - {"error":"model 'mistral-small3.2:24b' not found"}
   Traceback (most recent call last):
    File "/home/kfalguiere/Workspace/Beyond/afe/interfaceafe_final/.venv/lib/python3.11/site-packages/litellm/llms/custom_httpx/llm_http_handler.py", line 174, in _make_common_sync_call
      response = sync_httpx_client.post(
                 ^^^^^^^^^^^^^^^^^^^^^^^
    File "/home/kfalguiere/Workspace/Beyond/afe/interfaceafe_final/.venv/lib/python3.11/site-packages/litellm/llms/custom_httpx/http_handler.py", line 780, in post
      raise e
    File "/home/kfalguiere/Workspace/Beyond/afe/interfaceafe_final/.venv/lib/python3.11/site-packages/litellm/llms/custom_httpx/http_handler.py", line 762, in post
      response.raise_for_status()
    File "/home/kfalguiere/Workspace/Beyond/afe/interfaceafe_final/.venv/lib/python3.11/site-packages/httpx/_models.py", line 829, in raise_for_status
      raise HTTPStatusError(message, request=request, response=self)
  httpx.HTTPStatusError: Client error '404 Not Found' for url 'http://localhost:11434/api/chat'
  For more information check: https://developer.mozilla.org/en-US/docs/Web/HTTP/Status/404
```

### Possible Solution

To fix in my project I did that : 

1. Bug 1 - in internal_instructor.py
```python
def _get_llm_extra_kwargs(self) -> dict[str, Any]:
    if self.llm is None:
        return {}
    extra: dict[str, Any] = {}
    for attr in ("api_base", "base_url"): # add other maybe ?
        value = getattr(self.llm, attr, None)
        if value is not None:
            extra[attr] = value
    return extra

def to_pydantic(self) -> T:
    # ...
    return self._client.chat.completions.create(
        model=model_name, response_model=self.model, messages=messages,
        **self._get_llm_extra_kwargs(),  # FIX HERE
    )
 ```

3. Bug 2
I found nothing sorry, I juste override the function in my code 

```python
llm.supports_function_calling = lambda: True
```

### Additional context

X
