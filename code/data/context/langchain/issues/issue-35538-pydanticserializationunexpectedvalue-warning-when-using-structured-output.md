# PydanticSerializationUnexpectedValue warning when using structured output

**Issue #35538** | State: closed | Created: 2026-03-03 | Updated: 2026-03-05
**Author:** johnayoub-wtw
**Labels:** bug, langchain, openai, external

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
from langchain_openai import ChatOpenAI
from pydantic.main import BaseModel

llm = ChatOpenAI(...) # not using responses API

class ModelOutput(BaseModel):
    output: str

output = llm.with_structured_output(ModelOutput).invoke("What is the capital of France?")
```

### Error Message and Stack Trace (if applicable)

```shell
PydanticSerializationUnexpectedValue(Expected `none` - serialized value may not be as expected [field_name='parsed', input_value=ModelOutput(output='The c...al of France is Paris.'), input_type=ModelOutput])
  return self.__pydantic_serializer__.to_python(
```

### Description

using structured output produces a serializer warning. This behavior seems to have been introduced with one the recent langchain releases.

### System Info

System Information
------------------
> OS:  Linux
> OS Version:  #1 SMP Tue Nov 5 00:21:55 UTC 2024
> Python Version:  3.14.3 (main, Feb  3 2026, 22:52:18) [Clang 21.1.4 ]

Package Information
-------------------
> langchain_core: 1.2.17
> langchain: 1.2.10
> langchain_community: 0.4.1
> langsmith: 0.7.10
> langchain_classic: 1.0.1
> langchain_openai: 1.1.10
> langchain_text_splitters: 1.1.1
> langgraph_sdk: 0.3.9

Optional packages not installed
-------------------------------
> deepagents
> deepagents-cli

Other Dependencies
------------------
> aiohttp: 3.13.3
> dataclasses-json: 0.6.7
> httpx: 0.28.1
> httpx-sse: 0.4.3
> jsonpatch: 1.33
> langgraph: 1.0.10
> numpy: 2.4.2
> openai: 2.24.0
> opentelemetry-api: 1.39.0
> opentelemetry-exporter-otlp-proto-http: 1.39.0
> opentelemetry-sdk: 1.39.0
> orjson: 3.11.7
> packaging: 26.0
> pydantic: 2.12.5
> pydantic-settings: 2.13.1
> pytest: 9.0.2
> pyyaml: 6.0.3
> PyYAML: 6.0.3
> requests: 2.32.5
> requests-toolbelt: 1.0.0
> rich: 14.3.3
> SQLAlchemy: 2.0.48
> sqlalchemy: 2.0.48
> tenacity: 9.1.4
> tiktoken: 0.12.0
> typing-extensions: 4.15.0
> uuid-utils: 0.14.1
> wrapt: 1.17.3
> xxhash: 3.6.0
> zstandard: 0.25.0
