# Not using Tools in Langchain_Ollama causes: 'NoneType' object is not iterable

**Issue #28312** | State: closed | Created: 2024-11-23 | Updated: 2026-03-06
**Author:** bauerem
**Labels:** investigate

### Checked other resources

- [X] I added a very descriptive title to this issue.
- [X] I searched the LangChain documentation with the integrated search.
- [X] I used the GitHub search to find a similar question and didn't find it.
- [X] I am sure that this is a bug in LangChain rather than my code.
- [X] The bug is not resolved by updating to the latest stable version of LangChain (or the specific integration package).

### Example Code

from langchain_ollama import ChatOllama

llm = ChatOllama(
    model="llama3.1",
    temperature=0,
    disable_streaming=True
)

messages = [
    (
        "system",
        "You are a helpful assistant that translates English to French. Translate the user sentence.",
    ),
    ("human", "I love programming."),
]
ai_msg = llm.invoke(messages)
print(ai_msg)

### Error Message and Stack Trace (if applicable)

Traceback (most recent call last):
  File "/home/user1/Repo/ollama-cloud/use4.py", line 16, in 
    ai_msg = llm.invoke(messages)
  File "/home/user1/Repo/ollama-cloud/venv/lib/python3.10/site-packages/langchain_core/language_models/chat_models.py", line 286, in invoke
    self.generate_prompt(
  File "/home/user1/Repo/ollama-cloud/venv/lib/python3.10/site-packages/langchain_core/language_models/chat_models.py", line 786, in generate_prompt
    return self.generate(prompt_messages, stop=stop, callbacks=callbacks, **kwargs)
  File "/home/user1/Repo/ollama-cloud/venv/lib/python3.10/site-packages/langchain_core/language_models/chat_models.py", line 643, in generate
    raise e
  File "/home/user1/Repo/ollama-cloud/venv/lib/python3.10/site-packages/langchain_core/language_models/chat_models.py", line 633, in generate
    self._generate_with_cache(
  File "/home/user1/Repo/ollama-cloud/venv/lib/python3.10/site-packages/langchain_core/language_models/chat_models.py", line 851, in _generate_with_cache
    result = self._generate(
  File "/home/user1/Repo/ollama-cloud/venv/lib/python3.10/site-packages/langchain_ollama/chat_models.py", line 648, in _generate
    final_chunk = self._chat_stream_with_aggregation(
  File "/home/user1/Repo/ollama-cloud/venv/lib/python3.10/site-packages/langchain_ollama/chat_models.py", line 560, in _chat_stream_with_aggregation
    tool_calls=_get_tool_calls_from_response(stream_resp),
  File "/home/user1/Repo/ollama-cloud/venv/lib/python3.10/site-packages/langchain_ollama/chat_models.py", line 71, in _get_tool_calls_from_response
    for tc in response["message"]["tool_calls"]:
TypeError: 'NoneType' object is not iterable

### Description

Trying to simple get a chat response from ChatOllama.

### System Info

System Information
------------------
> OS:  Linux
> OS Version:  #49~22.04.1-Ubuntu SMP PREEMPT_DYNAMIC Wed Nov  6 17:42:15 UTC 2
> Python Version:  3.10.12 (main, Nov  6 2024, 20:22:13) [GCC 11.4.0]

Package Information
-------------------
> langchain_core: 0.3.20
> langchain: 0.3.7
> langchain_community: 0.3.7
> langsmith: 0.1.144
> langchain_ollama: 0.2.0
> langchain_text_splitters: 0.3.2

Optional packages not installed
-------------------------------
> langserve

Other Dependencies
------------------
> aiohttp: 3.11.7
> async-timeout: 4.0.3
> dataclasses-json: 0.6.7
> httpx: 0.27.2
> httpx-sse: 0.4.0
> jsonpatch: 1.33
> numpy: 1.26.4
> ollama: 0.4.0
> orjson: 3.10.11
> packaging: 24.2
> pydantic: 2.10.1
> pydantic-settings: 2.6.1
> PyYAML: 6.0.2
> requests: 2.32.3
> requests-toolbelt: 1.0.0
> SQLAlchemy: 2.0.35
> tenacity: 9.0.0
> typing-extensions: 4.12.2

## Comments

**Fernando7181:**
we had another issue that was similar to this one, maybe try `python
response["message"]["tool_calls"] is not None` and see if that works

**bauerem:**
Yes, that is how I would also fix the bug in the langchain implementation

**Fernando7181:**
> Yes, that is how I would also fix the bug in the langchain implementation

did it work?

**keenborder786:**
@bauerem please upgrade to latest version of `langchain-ollama`. It should fix the issue.

**espositodaniele:**
Same error here:

### Package Information

> ollama 0.4.1
> langchain 0.3.8
> langchain-community 0.3.8
> langchain-core 0.3.21
> langchain-ollama 0.2.0

### Code example

```
from langchain_ollama import ChatOllama

model = ChatOllama(model="llama3.2", temperature=0)
model.invoke("Chi è il presidente degli Stati Uniti?")

```

### Error

> TypeError                                 Traceback (most recent call last)
> Cell In[34], [line 4](vscode-notebook-cell:?execution_count=34&line=4)
>       [1](vscode-notebook-cell:?execution_count=34&line=1) from langchain_ollama import ChatOllama
>       [3](vscode-notebook-cell:?execution_count=34&line=3) model = ChatOllama(model="llama3.2", temperature=0)
> ----> [4](vscode-notebook-cell:?execution_count=34&line=4) model.invoke("Chi è il presidente degli Stati Uniti?")
> 
> File ~/aidev/pdf-rag/.venv/lib/python3.13/site-packages/langchain_core/language_models/chat_models.py:286, in BaseChatModel.invoke(self, input, config, stop, **kwargs)
>     [275](https://file+.vscode-resource.vscode-cdn.net/Users/danieleesposito/aidev/pdf-rag/~/aidev/pdf-rag/.venv/lib/python3.13/site-packages/langchain_core/language_models/chat_models.py:275) def invoke(
>     [276](https://file+.vscode-resource.vscode-cdn.net/Users/danieleesposito/aidev/pdf-rag/~/aidev/pdf-rag/.venv/lib/python3.13/site-packages/langchain_core/language_models/chat_models.py:276)     self,
>     [277](https://file+.vscode-resource.vscode-cdn.net/Users/danieleesposito/aidev/pdf-rag/~/aidev/pdf-rag/.venv/lib/python3.13/site-packages/langchain_core/language_models/chat_models.py:277)     input: LanguageModelInput,
>    (...)
>     [281](https://file+.vscode-resource.vscode-cdn.net/Users/danieleesposito/aidev/pdf-rag/~/aidev/pdf-rag/.venv/lib/python3.13/site-packages/langchain_core/language_models/chat_models.py:281)     **kwargs: Any,
>     [282](https://file+.vscode-resource.vscode-cdn.net/Users/danieleesposito/aidev/pdf-rag/~/aidev/pdf-rag/.venv/lib/python3.13/site-packages/langchain_core/language_models/chat_models.py:282) ) -> BaseMessage:
>     [283](https://file+.vscode-resource.vscode-cdn.net/Users/danieleesposito/aidev/pdf-rag/~/aidev/pdf-rag/.venv/lib/python3.13/site-packages/langchain_core/language_models/chat_models.py:283)     config = ensure_config(config)
>     [284](https://file+.vscode-resource.vscode-cdn.net/Users/danieleesposito/aidev/pdf-rag/~/aidev/pdf-rag/.venv/lib/python3.13/site-packages/langchain_core/language_models/chat_models.py:284)     return cast(
>     [285](https://file+.vscode-resource.vscode-cdn.net/Users/danieleesposito/aidev/pdf-rag/~/aidev/pdf-rag/.venv/lib/python3.13/site-packages/langchain_core/language_models/chat_models.py:285)         ChatGeneration,
> --> [286](https://file+.vscode-resource.vscode-cdn.net/Users/danieleesposito/aidev/pdf-rag/~/aidev/pdf-rag/.venv/lib/python3.13/site-packages/langchain_core/language_models/chat_models.py:286)         self.generate_prompt(
>     [287](https://file+.vscode-resource.vscode-cdn.net/Users/danieleesposito/aidev/pdf-rag/~/aidev/pdf-rag/.venv/lib/python3.13/site-packages/langchain_core/language_models/chat_models.py:287)             [self._convert_input(input)],
>     [288](https://file+.vscode-resource.vscode-cdn.net/Users/danieleesposito/aidev/pdf-rag/~/aidev/pdf-rag/.venv/lib/python3.13/site-packages/langchain_core/language_models/chat_models.py:288)             stop=stop,
>     [289](https://file+.vscode-resource.vscode-cdn.net/Users/danieleesposito/aidev/pdf-rag/~/aidev/pdf-rag/.venv/lib/python3.13/site-packages/langchain_core/language_models/chat_models.py:289)             callbacks=config.get("callbacks"),
>     [290](https://file+.vscode-resource.vscode-cdn.net/Users/danieleesposito/aidev/pdf-rag/~/aidev/pdf-rag/.venv/lib/python3.13/site-packages/langchain_core/language_models/chat_models.py:290)             tags=config.get("tags"),
>     [291](https://file+.vscode-resource.vscode-cdn.net/Users/danieleesposito/aidev/pdf-rag/~/aidev/pdf-rag/.venv/lib/python3.13/site-packages/langchain_core/language_models/chat_models.py:291)             metadata=config.get("metadata"),
>     [292](https://file+.vscode-resource.vscode-cdn.net/Users/danieleesposito/aidev/pdf-rag/~/aidev/pdf-rag/.venv/lib/python3.13/site-packages/langchain_core/language_models/chat_models.py:292)             run_name=config.get("run_name"),
>     [293](https://file+.vscode-resource.vscode-cdn.net/Users/danieleesposito/aidev/pdf-rag/~/aidev/pdf-rag/.venv/lib/python3.13/site-packages/langchain_core/language_models/chat_models.py:293)             run_id=config.pop("run_id", None),
> ...
>      [76](https://file+.vscode-resource.vscode-cdn.net/Users/danieleesposito/aidev/pdf-rag/~/aidev/pdf-rag/.venv/lib/python3.13/site-packages/langchain_ollama/chat_models.py:76)                 )
>      [77](https://file+.vscode-resource.vscode-cdn.net/Users/danieleesposito/aidev/pdf-rag/~/aidev/pdf-rag/.venv/lib/python3.13/site-packages/langchain_ollama/chat_models.py:77)             )
>      [78](https://file+.vscode-resource.vscode-cdn.net/Users/danieleesposito/aidev/pdf-rag/~/aidev/pdf-rag/.venv/lib/python3.13/site-packages/langchain_ollama/chat_models.py:78) return tool_calls
> 
> TypeError: 'NoneType' object is not iterable

**nourishnew:**
@keenborder786  Latest version doesn't seem to have the None check.

**keenborder786:**
@nourishnew yeap you are correct I have fixed it it in the PR. Hopefully in the next release it will be fixed.

**dosubot[bot]:**
Hi, @bauerem. I'm [Dosu](https://dosu.dev), and I'm helping the LangChain team manage their backlog. I'm marking this issue as stale.

**Issue Summary**
- You reported a bug in LangChain's ChatOllama model causing a 'NoneType' object is not iterable error.
- @Fernando7181 suggested a fix by checking if `response["message"]["tool_calls"]` is not None, which you agreed with.
- @keenborder786 mentioned a fix has been made in a pull request and will be included in the next release.

**Next Steps**
- Please confirm if this issue is still relevant with the latest version of LangChain. If so, feel free to comment to keep the discussion open.
- If there are no further updates, this issue will be automatically closed in 7 days.

Thank you for your understanding and contribution!
