#  max_tokens param in ChatOpenAI() can't be processed

**Issue #29060** | State: closed | Created: 2025-01-07 | Updated: 2026-03-06
**Author:** newispk
**Labels:** bug, investigate, external

### Checked other resources

- [X] I added a very descriptive title to this issue.
- [X] I searched the LangChain documentation with the integrated search.
- [X] I used the GitHub search to find a similar question and didn't find it.
- [X] I am sure that this is a bug in LangChain rather than my code.
- [X] The bug is not resolved by updating to the latest stable version of LangChain (or the specific integration package).

### Example Code

```python
from langchain_community.chat_models import ChatOpenAI
# from langchain_openai.chat_models import ChatOpenAI
qwen_local_llm = ChatOpenAI(model=QWEN_API_LOCAL_MODEL_NAME,
                            openai_api_key=OPENAI_API_KEY,
                            openai_api_base=OPENAI_API_BASE,
                            max_tokens=4096,
                            temperature=0.01,request_timeout=600)
prompt_context_str = """你是一个提取算法专家，仅从文本中提取相关信息。......."""
full_response = ""
for chunk in qwen_local_llm.stream(prompt_context_str):
    full_response += chunk.content
print(full_response)  ```

### Error Message and Stack Trace (if applicable)

When the returned result exceeds 1,024 tokens, it will be truncated.

### Description

The max_tokens parameter of the ChatOpenAI object introduced in the way of from langchain_openai.chat_models import ChatOpenAI doesn't take effect. While the max_tokens function of the ChatOpenAI object introduced in the way of from langchain_community.chat_models import ChatOpenAI works normally. The default value of max_tokens for the former is 1024.

### System Info

System Information
------------------
> OS:  Darwin
> OS Version:  Darwin Kernel Version 24.2.0: Fri Dec  6 18:40:14 PST 2024; root:xnu-11215.61.5~2/RELEASE_ARM64_T8103
> Python Version:  3.9.21 | packaged by conda-forge | (main, Dec  5 2024, 13:47:18) 
[Clang 18.1.8 ]

Package Information
-------------------
> langchain_core: 0.3.29
> langchain: 0.3.14
> langchain_community: 0.3.14
> langsmith: 0.2.10
> langchain_chroma: 0.1.4
> langchain_ollama: 0.2.2
> langchain_openai: 0.2.14
> langchain_text_splitters: 0.3.4

Optional packages not installed
-------------------------------
> langserve

## Comments

**ccurme:**
OpenAI has [deprecated](https://platform.openai.com/docs/api-reference/chat/create#chat-create-max_tokens) the `max_tokens` parameter in favor of `max_completion_tokens`. The API you are interacting with via the OpenAI SDK has not kept up with OpenAI's changes.

Can you try using `BaseChatOpenAI` instead? This supports `max_tokens`:
```python
from langchain_openai.chat_models.base import BaseChatOpenAI

llm = BaseChatOpenAI(model="gpt-4o-mini")
llm.invoke("hi, how are you?", max_tokens=3)
```

**newispk:**
> OpenAI has [deprecated](https://platform.openai.com/docs/api-reference/chat/create#chat-create-max_tokens) the `max_tokens` parameter in favor of `max_completion_tokens`. The API you are interacting with via the OpenAI SDK has not kept up with OpenAI's changes.
> 
> Can you try using `BaseChatOpenAI` instead? This supports `max_tokens`:
> 
> ```python
> from langchain_openai.chat_models.base import BaseChatOpenAI
> 
> llm = BaseChatOpenAI(model="gpt-4o-mini")
> llm.invoke("hi, how are you?", max_tokens=3)
> ```

Thanks it worked for me!
