# PIIMiddleware with custom detector raises KeyError: 'value' for hash and mask strategies

**Issue #35647** | State: closed | Created: 2026-03-08 | Updated: 2026-03-08
**Author:** Dalbirsm03
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
- [ ] langchain-openrouter
- [ ] langchain-perplexity
- [ ] langchain-qdrant
- [ ] langchain-xai
- [ ] Other / not sure / general

### Related Issues / PRs

_No response_

### Reproduction Steps / Example Code (Python)

```python
import re
from langchain.agents.middleware import PIIMiddleware
from langchain.agents import create_agent
from langchain.chat_models import init_chat_model
from langchain.messages import HumanMessage

model = init_chat_model(model="groq:qwen/qwen3-32b")

def detect_indian_phone(content: str) -> list[dict]:
    """Custom detector for Indian phone numbers"""
    matches = []
    pattern = r'\+91[\s.-]?[6-9]\d{9}'
    
    for match in re.finditer(pattern, content):
        matches.append({
            "text": match.group(0),
            "start": match.start(),
            "end": match.end(),
        })
    return matches

# Create agent with custom detector
agent = create_agent(
    model=model,
    middleware=[
        PIIMiddleware(
            pii_type="indian_phone",
            detector=detect_indian_phone,
            strategy="hash",  # Also fails with "mask"
            apply_to_input=True
        )
    ]
)

# This raises KeyError: 'value'
response = agent.invoke({
    "messages": [HumanMessage(content="Contact me at +91 9876543210")]
})
```

### Error Message and Stack Trace (if applicable)

```shell
## **Error Message and Stack Trace**

KeyError                                  Traceback (most recent call last)
Cell In[45], line 40
     28 agent = create_agent(
     29     model = model,
     30     middleware= [
   (...)
     37     ]
     38 )
---> 40 response = agent.invoke({
     41     "messages": [
     42         HumanMessage(content="Contact me at +91 9876543210")
     43     ]
     44 })
     45 print(response)

File c:\Users\Dalbir\Downloads\LangChain-Bootcamp\.venv\Lib\site-packages\langgraph\pregel\main.py:3071, in Pregel.invoke(self, input, config, context, stream_mode, print_mode, output_keys, interrupt_before, interrupt_after, durability, **kwargs)
   3068 chunks: list[dict[str, Any] | Any] = []
   3069 interrupts: list[Interrupt] = []
-> 3071 for chunk in self.stream(
   ...
    301     replacement = f""
    302     result = result[: match["start"]] + replacement + result[match["end"] :]

KeyError: 'value'
During task with name 'PIIMiddleware[indian_phone].before_model' and id 'a1a0b8f6-bbd5-1218-2eda-899805649ec4'
```

### Description

Problem:
PIIMiddleware fails with KeyError: 'value' when using a custom detector function with hash or mask strategies.
Expected Behavior:
According to the [PIIMiddleware documentation](https://python.langchain.com/docs/concepts/middleware/#pii-detection), custom detector functions should return a list of dictionaries with text, start, and end keys:
pythondef detector(content: str) -> list[dict[str, str | int]]:
    return [
        {"text": "matched_text", "start": 0, "end": 12},
    ]
This should work with all strategies: block, redact, hash, and mask.
Actual Behavior:

✅ Strategies redact and block work fine
❌ Strategies hash and mask raise KeyError: 'value'

What Works:
Using regex string directly instead of custom function:
pythonPIIMiddleware(
    pii_type="indian_phone",
    detector=r'\+91[\s.-]?[6-9]\d{9}',  # Works!
    strategy="hash",
    apply_to_input=True
)
Root Cause:
The error traceback shows the middleware code is trying to access match['value'] at line 301-302, but this key is not part of the documented return format and is not being provided by the custom detector.
Suggested Fix:
Either:

Update the middleware code to work with the documented format (text, start, end)
Update documentation to specify that value key is required

### System Info

System Information
------------------
> OS:  Windows
> OS Version:  10.0.26200
> Python Version:  3.12.0 (tags/v3.12.0:0fb18b0, Oct  2 2023, 13:03:39) [MSC v.1935 64 bit (AMD64)]

Package Information
-------------------
> langchain_core: 1.2.11
> langchain: 1.2.10
> langchain_community: 0.4.1
> langsmith: 0.7.1
> langchain_classic: 1.0.1
> langchain_google_genai: 4.2.0
> langchain_groq: 1.1.2
> langchain_openai: 1.1.9
> langchain_text_splitters: 1.1.0
> langgraph_sdk: 0.3.5

Optional packages not installed
-------------------------------
> langserve

Other Dependencies
------------------
> aiohttp: 3.13.3
> dataclasses-json: 0.6.7
> filetype: 1.2.0
> google-genai: 1.63.0
> groq: 0.37.1
> httpx: 0.28.1
> httpx-sse: 0.4.3
> jsonpatch: 1.33
> langgraph: 1.0.8
> numpy: 2.4.2
> openai: 2.20.0
> orjson: 3.11.7
> packaging: 26.0
> pydantic: 2.12.5
> pydantic-settings: 2.12.0
> pyyaml: 6.0.3
> PyYAML: 6.0.3
> requests: 2.32.5
> requests-toolbelt: 1.0.0
> sqlalchemy: 2.0.46
> SQLAlchemy: 2.0.46
> tenacity: 9.1.4
> tiktoken: 0.12.0
> typing-extensions: 4.15.0
> uuid-utils: 0.14.0
> xxhash: 3.6.0
> zstandard: 0.25.0

(LangChain-Bootcamp) C:\Users\Dalbir\Downloads\LangChain-Bootcamp>
