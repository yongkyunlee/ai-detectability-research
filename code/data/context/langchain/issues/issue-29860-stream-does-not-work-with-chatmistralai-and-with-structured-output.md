# Stream does not work with `ChatMistralAI` and `with_structured_output`

**Issue #29860** | State: open | Created: 2025-02-18 | Updated: 2026-03-13
**Author:** brochier
**Labels:** bug, investigate, integration, mistralai, external

### Checked other resources

- [x] I added a very descriptive title to this issue.
- [x] I searched the LangChain documentation with the integrated search.
- [x] I used the GitHub search to find a similar question and didn't find it.
- [x] I am sure that this is a bug in LangChain rather than my code.
- [x] The bug is not resolved by updating to the latest stable version of LangChain (or the specific integration package).

### Example Code

```python
import os
import getpass
from langchain_mistralai.chat_models import ChatMistralAI

if "MISTRAL_API_KEY" not in os.environ:
    os.environ["MISTRAL_API_KEY"] = getpass.getpass("Enter your Mistral API key: ")

model = ChatMistralAI(
    temperature=0, max_retries=2, model="mistral-small-latest", streaming=True
)

output_schema = {
    "title": "biggest_cities",
    "description": "",
    "type": "object",
    "properties": {
        "cities": {"type": "array", "items": {"type": "string"}, "description": ""}
    },
    "required": ["cities"],
}

model_with_structure = model.with_structured_output(
    output_schema, method="function_calling"
)

for chunk in model_with_structure.stream("What are the 10 biggest cities in France?"):
    print(chunk)

```

### Error Message and Stack Trace (if applicable)

_No response_

### Description

When using `ChatMistralAI` model with the `with_structured_output` method, with `function_calling`mode, the `stream`method does not stream anymore (the entire response is received at once). Any idea why this happens ? Is it MistralAI that does not stream the answer in this case ? 

### System Info

System Information
------------------
> OS:  Darwin
> OS Version:  Darwin Kernel Version 24.2.0: Fri Dec  6 18:51:28 PST 2024; root:xnu-11215.61.5~2/RELEASE_ARM64_T8112
> Python Version:  3.11.6 (main, Apr  8 2024, 17:17:59) [Clang 15.0.0 (clang-1500.3.9.4)]

Package Information
-------------------
> langchain_core: 0.3.35
> langchain: 0.3.19
> langsmith: 0.2.11
> langchain_google_genai: 2.0.9
> langchain_mistralai: 0.2.4
> langchain_ollama: 0.2.2
> langchain_openai: 0.3.0
> langchain_text_splitters: 0.3.6

Optional packages not installed
-------------------------------
> langserve

Other Dependencies
------------------
> aiohttp=3.8.3: Installed. No version info available.
> async-timeout=4.0.0;: Installed. No version info available.
> filetype: 1.2.0
> google-generativeai: 0.8.4
> httpx: 0.27.2
> httpx-sse: 0.4.0
> jsonpatch=1.33: Installed. No version info available.
> langchain-anthropic;: Installed. No version info available.
> langchain-aws;: Installed. No version info available.
> langchain-cohere;: Installed. No version info available.
> langchain-community;: Installed. No version info available.
> langchain-core=0.3.34: Installed. No version info available.
> langchain-core=0.3.35: Installed. No version info available.
> langchain-deepseek;: Installed. No version info available.
> langchain-fireworks;: Installed. No version info available.
> langchain-google-genai;: Installed. No version info available.
> langchain-google-vertexai;: Installed. No version info available.
> langchain-groq;: Installed. No version info available.
> langchain-huggingface;: Installed. No version info available.
> langchain-mistralai;: Installed. No version info available.
> langchain-ollama;: Installed. No version info available.
> langchain-openai;: Installed. No version info available.
> langchain-text-splitters=0.3.6: Installed. No version info available.
> langchain-together;: Installed. No version info available.
> langchain-xai;: Installed. No version info available.
> langsmith-pyo3: Installed. No version info available.
> langsmith=0.1.125: Installed. No version info available.
> langsmith=0.1.17: Installed. No version info available.
> numpy=1.26.4;: Installed. No version info available.
> numpy=1.26.2;: Installed. No version info available.
> ollama: 0.4.6
> openai: 1.59.7
> orjson: 3.10.14
> packaging=23.2: Installed. No version info available.
> pydantic: 2.10.5
> pydantic=2.5.2;: Installed. No version info available.
> pydantic=2.7.4: Installed. No version info available.
> pydantic=2.7.4;: Installed. No version info available.
> PyYAML>=5.3: Installed. No version info available.
> requests: 2.32.3
> requests-toolbelt: 1.0.0
> requests=2: Installed. No version info available.
> SQLAlchemy=1.4: Installed. No version info available.
> tenacity!=8.4.0,=8.1.0: Installed. No version info available.
> tenacity!=8.4.0,=8.1.0: Installed. No version info available.
> tiktoken: 0.8.0
> tokenizers: 0.21.0
> typing-extensions>=4.7: Installed. No version info available.
> zstandard: Installed. No version info available.

## Comments

**brochier:**
If anyone could propose a quick fix to maintain the custom JSON mode while maintaining the stream response it would be amazing ! I tried to deep dive into the code but I can't understand where exactly the json parser is defined when using the `with_structured_output` method and thus I can't verify if the `partial=True` is passed.

**andrasfe:**
I don't know if there is more to it, but adding the underscore to "biggest cities" fixed it for me.

The error is coming from the output_schema definition, specifically with the title "biggest cities". According to the error message, function names must only contain alphanumeric characters, underscores, and dashes (no spaces).
Here's how to fix it:

`// ... existing code ...

output_schema = {
    "title": "biggest_cities",  # Changed from "biggest cities" to "biggest_cities"
    "description": "",
    "type": "object",
    "properties": {
        "cities": {"type": "array", "items": {"type": "string"}, "description": ""}
    },
    "required": ["cities"],
}

// ... existing code ...`

**brochier:**
I did a mistake when copy pasting the code (I updated my post). It should indeed be `"title": "biggest_cities"`. 
In this case, it does not produce any error. It is just not streaming, that's the bug I want to point.

**keenborder786:**
Following is the payload being passed to Mistral Endpoint `https://api.mistral.ai/v1/chat/completions`:

```
{'messages': [{'role': 'user', 'content': 'What are the 10 biggest cities in France?'}], 'model': 'mistral-small-latest', 'temperature': 0.0, 'top_p': 1, 'tools': [{'type': 'function', 'function': {'name': 'biggest_cities', 'description': '', 'parameters': {'type': 'object', 'properties': {'cities': {'type': 'array', 'items': {'type': 'string'}, 'description': ''}}, 'required': ['cities']}}}], 'tool_choice': 'any', 'stream': True}
```

I tested the Mistral API and directly and the tool calling streaming is not yet supported in MistralAI therefore it is yielding the output as a single result.

**brochier:**
Using the API directly actually works as expected. So the bug is in langchain. 

```bash
curl --location "https://api.mistral.ai/v1/chat/completions" \
     --header 'Content-Type: application/json' \
     --header 'Accept: application/json' \
     --header "Authorization: Bearer $MISTRAL_API_KEY" \
     --data '{
    "model": "ministral-8b-latest",
    "stream": true,
    "messages": [
     {
        "role": "system",
        "content": "Extract the books information."
      },
     {
        "role": "user",
        "content": "I recently read To Kill a Mockingbird by Harper Lee."
      }
    ],
    "response_format": {
      "type": "json_schema",
      "json_schema": {
        "schema": {
          "properties": {
            "name": {
              "title": "Name",
              "type": "string"
            },
            "authors": {
              "items": {
                "type": "string"
              },
              "title": "Authors",
              "type": "array"
            }
          },
          "required": ["name", "authors"],
          "title": "Book",
          "type": "object",
          "additionalProperties": false
        },
        "name": "book",
        "strict": true
      }
    },
    "max_tokens": 256,
    "temperature": 0
  }'
```

**brochier:**
Here is a substitue I currently use to get streaming working while enforcing structured output. 

```python
from typing import Optional
import requests
import json
from langchain_core.utils.json import parse_partial_json
import time

DATA_BLOCK = "data: "

class MistralAPIClient:
    def __init__(self, api_key, model):
        self.api_key = api_key
        self.model = model
        self.url = "https://api.mistral.ai/v1/chat/completions"
        self.headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Bearer {self.api_key}"
        }

    def call(self, prompt, json_schema=None, stream=False):
        data = {
            "model": "mistral-small-latest",
            "stream": stream,
            "temperature": 0,
            "messages": [
             {
                "role": "system",
                "content": prompt
              }
            ]
          }

        if json_schema:
            data["response_format"] = json_schema

        with requests.post(self.url, headers=self.headers, data=json.dumps(data), stream=stream) as response:
            if not stream:
                message = response.json()["choices"][0]["message"]["content"]
                if json_schema:
                    yield json.loads(message)
                else:
                    yield message
            else:
                message = ""
                response.raise_for_status()
                for chunk in response.iter_lines(chunk_size=None):
                    if chunk:
                        chunk = chunk.decode("utf-8")

                        if chunk.startswith(DATA_BLOCK):
                            chunk = chunk[len(DATA_BLOCK):]
                            if chunk.startswith("{"):
                                chunk = json.loads(chunk)
                                message += chunk["choices"][0]["delta"]["content"]

                                if json_schema:
                                    if len(message.strip()) == 0:
                                        yield {}
                                    else:
                                        yield parse_partial_json(message)
                                else:
                                    yield chunk["choices"][0]["delta"]["content"]
```

**aheschl1:**
Hello, I am getting a similar issue with Ollama and tool calling:

```
self.model = ChatOllama(
    model=model_name,
    num_ctx=context,
    temperature=temperature,
    base_url=endpoint,
    extract_reasoning=False
).bind_tools(tools=[tool[0] for tool in tools])
```
and 
```
message = None
async for chunk in self.model.astream(state.messages):
    print(chunk.content, end="", flush=True)
    if not message:
        message = chunk
    else:
        message += chunk
  ```
leads to the entire message printing at once.

**dosubot[bot]:**
Hi, @brochier. I'm [Dosu](https://dosu.dev), and I'm helping the LangChain team manage their backlog. I'm marking this issue as stale.

**Issue Summary:**
- The `ChatMistralAI` model's `stream` method does not function correctly with `with_structured_output` and `function_calling` mode.
- The entire response is received at once, contrary to expected streaming behavior.
- @keenborder786 mentioned the Mistral API's lack of support for tool calling streaming, but you confirmed direct API usage works, suggesting a LangChain bug.
- You provided a workaround using a custom API client for streaming with structured output.
- A similar issue was reported by @aheschl1 with the Ollama model.

**Next Steps:**
- Please confirm if this issue is still relevant with the latest version of LangChain. If it is, feel free to comment to keep the discussion open.
- If there is no further activity, this issue will be automatically closed in 7 days.

Thank you for your understanding and contribution!

**keenborder786:**
> Here is a substitue I currently use to get streaming working while enforcing structured output.
> 
> from typing import Optional
> import requests
> import json
> from langchain_core.utils.json import parse_partial_json
> import time
> 
> 
> DATA_BLOCK = "data: "
> 
> class MistralAPIClient:
>     def __init__(self, api_key, model):
>         self.api_key = api_key
>         self.model = model
>         self.url = "https://api.mistral.ai/v1/chat/completions"
>         self.headers = {
>             "Content-Type": "application/json",
>             "Accept": "application/json",
>             "Authorization": f"Bearer {self.api_key}"
>         }
> 
>     def call(self, prompt, json_schema=None, stream=False):
>         data = {
>             "model": "mistral-small-latest",
>             "stream": stream,
>             "temperature": 0,
>             "messages": [
>              {
>                 "role": "system",
>                 "content": prompt
>               }
>             ]
>           }
> 
>         if json_schema:
>             data["response_format"] = json_schema
> 
>         with requests.post(self.url, headers=self.headers, data=json.dumps(data), stream=stream) as response:
>             if not stream:
>                 message = response.json()["choices"][0]["message"]["content"]
>                 if json_schema:
>                     yield json.loads(message)
>                 else:
>                     yield message
>             else:
>                 message = ""
>                 response.raise_for_status()
>                 for chunk in response.iter_lines(chunk_size=None):
>                     if chunk:
>                         chunk = chunk.decode("utf-8")
> 
>                         if chunk.startswith(DATA_BLOCK):
>                             chunk = chunk[len(DATA_BLOCK):]
>                             if chunk.startswith("{"):
>                                 chunk = json.loads(chunk)
>                                 message += chunk["choices"][0]["delta"]["content"]
> 
>                                 if json_schema:
>                                     if len(message.strip()) == 0:
>                                         yield {}
>                                     else:
>                                         yield parse_partial_json(message)
>                                 else:
>                                     yield chunk["choices"][0]["delta"]["content"]

@brochier In your original issue, you mentioned `function_calling` but here you are giving a reference to `json_schema`.

For `json_schema` streaming already works in Langchain:

```python

from langchain_mistralai import ChatMistralAI

model = ChatMistralAI(model="mistral-small-latest")
output_schema = {
    "title": "biggest_cities",
    "description": "",
    "type": "object",
    "properties": {
        "cities": {"type": "array", "items": {"type": "string"}, "description": ""}
    },
    "required": ["cities"],
}

model_with_structure = model.with_structured_output(
    output_schema, method="json_schema"
)

for chunk in model_with_structure.stream("What are the 10 biggest cities in France?"):
    print(chunk)
```

Mistral's API spec makes it structurally impossible to stream tool call arguments incrementally — every ToolCall in a streaming delta must include the full name and full arguments. This is why the function_calling method can never stream token-by-token on Mistral. The json_schema method (which outputs regular text content, not tool calls) is the correct approach for incremental streaming on Mistral. Reference I used --> docs.mistral.ai/openapi.yaml (See DeltaMessage)

**shivamtiwari3:**
Hi, I've implemented a fix for this issue in PR #35848. The fix adds a warning when streaming is used with `function_calling` method in `with_structured_output`, since Mistral's function calling mode doesn't support true streaming.

Could a maintainer please assign me to this issue? Once assigned, the PR will be automatically reopened per the repo's contribution policy.

Thank you!
