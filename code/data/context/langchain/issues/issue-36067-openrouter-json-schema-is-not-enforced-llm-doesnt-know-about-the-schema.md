# openrouter json_schema is not enforced, llm doesn't know about the schema

**Issue #36067** | State: open | Created: 2026-03-18 | Updated: 2026-03-18
**Author:** Nazareka
**Labels:** bug, external, openrouter

### Checked other resources

- [x] This is a bug, not a usage question.
- [x] I added a clear and descriptive title that summarizes this issue.
- [x] I used the GitHub search to find a similar question and didn't find it.
- [x] I am sure that this is a bug in LangChain rather than my code.
- [x] The bug is not resolved by updating to the latest stable version of LangChain (or the specific integration package).
- [x] This is not related to the langchain-community package.
- [x] I posted a self-contained, minimal, reproducible example. A maintainer can copy it and run it AS IS.

### Package (Required)

- [ ] langchain
- [ ] langchain-openai
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
- [x] langchain-openrouter
- [ ] langchain-perplexity
- [ ] langchain-qdrant
- [ ] langchain-xai
- [ ] Other / not sure / general

### Related Issues / PRs

_No response_

### Reproduction Steps / Example Code (Python)

```python
import os
from langchain_openrouter import ChatOpenRouter
from pydantic import BaseModel, ConfigDict, Field

os.environ["OPENROUTER_API_KEY"] = "x"

schema = {
    "title": "ProductInfo",
    "description": "Structured product data extracted from user text",
    "type": "object",
    "properties": {
        "name": {
            "type": "string",
            "description": "Product name"
        },
        "price_pln": {
            "type": "number",
            "description": "Price in PLN"
        },
        "color": {
            "type": "string",
            "description": "Product color"
        },
        "volume_ml": {
            "type": "integer",
            "description": "Volume in milliliters"
        },
        "dishwasher_safe": {
            "type": "boolean",
            "description": "Whether the product is dishwasher safe"
        }
    },
    "required": ["name", "price_pln"],
    "additionalProperties": False
}
# same with pydantic model - langchain_core.exceptions.OutputParserException: Failed to parse ProductInfo from completion {"product_name": "Red ceramic mug", "capacity_ml": 350, "dishwasher_safe": true, "price": 24.99, "currency": "PLN"}.

class ProductInfo(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str = Field(description="Product name")
    price_pln: float = Field(description="Price in PLN")
    color: str | None = Field(default=None, description="Product color")
    volume_ml: int | None = Field(default=None, description="Volume in milliliters")
    dishwasher_safe: bool | None = Field(
        default=None,
        description="Whether the product is dishwasher safe",
    )

llm = ChatOpenRouter(
    model="openrouter/hunter-alpha",
    temperature=0,
    max_retries=2,
)

structured_llm = llm.with_structured_output(
    schema,
    method="json_schema",
    strict=True,
)

result = structured_llm.invoke(
    "Extract product data from: Red ceramic mug, 350 ml, dishwasher-safe, price 24.99 PLN."
)

print(result)
# {'product_name': 'Red ceramic mug', 'capacity': '350 ml', 'features': ['dishwasher-safe'], 'price': {'amount': 24.99, 'currency': 'PLN'}}
```

### Error Message and Stack Trace (if applicable)

```shell

```

### Description

The schema is not enforced, and it seems like LLM doesn't know about it

### System Info

System Information
------------------
> OS:  Darwin
> OS Version:  Darwin Kernel Version 24.5.0: Tue Apr 22 19:54:43 PDT 2025; root:xnu-11417.121.6~2/RELEASE_ARM64_T8132
> Python Version:  3.14.2 (main, Jan 14 2026, 23:37:46) [Clang 21.1.4 ]

Package Information
-------------------
> langchain_core: 1.2.17
> langchain_community: 0.4.1
> langsmith: 0.7.12
> langchain_classic: 1.0.2
> langchain_openai: 1.1.10
> langchain_openrouter: 0.1.0
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
> numpy: 2.4.3
> openai: 2.25.0
> openrouter: 0.7.11
> orjson: 3.11.7
> packaging: 26.0
> pydantic: 2.12.5
> pydantic-settings: 2.13.1
> pytest: 9.0.2
> PyYAML: 6.0.3
> pyyaml: 6.0.3
> requests: 2.32.5
> requests-toolbelt: 1.0.0
> sqlalchemy: 2.0.48
> SQLAlchemy: 2.0.48
> tenacity: 9.1.4
> tiktoken: 0.12.0
> typing-extensions: 4.15.0
> uuid-utils: 0.14.1
> websockets: 16.0
> xxhash: 3.6.0
> zstandard: 0.25.0

## Comments

**maxsnow651-dev:**
Any updates on this bug

On Wed, Mar 18, 2026, 9:54 AM Nazareka ***@***.***> wrote:

> *Nazareka* created an issue (langchain-ai/langchain#36067)
> 
> Checked other resources
>
>    - This is a bug, not a usage question.
>    - I added a clear and descriptive title that summarizes this issue.
>    - I used the GitHub search to find a similar question and didn't find
>    it.
>    - I am sure that this is a bug in LangChain rather than my code.
>    - The bug is not resolved by updating to the latest stable version of
>    LangChain (or the specific integration package).
>    - This is not related to the langchain-community package.
>    - I posted a self-contained, minimal, reproducible example. A
>    maintainer can copy it and run it AS IS.
>
> Package (Required)
>
>    - langchain
>    - langchain-openai
>    - langchain-anthropic
>    - langchain-classic
>    - langchain-core
>    - langchain-model-profiles
>    - langchain-tests
>    - langchain-text-splitters
>    - langchain-chroma
>    - langchain-deepseek
>    - langchain-exa
>    - langchain-fireworks
>    - langchain-groq
>    - langchain-huggingface
>    - langchain-mistralai
>    - langchain-nomic
>    - langchain-ollama
>    - langchain-openrouter
>    - langchain-perplexity
>    - langchain-qdrant
>    - langchain-xai
>    - Other / not sure / general
>
> Related Issues / PRs
>
> *No response*
> Reproduction Steps / Example Code (Python)
>
> import os
> from langchain_openrouter import ChatOpenRouter
> from pydantic import BaseModel, ConfigDict, Field
>
> os.environ["OPENROUTER_API_KEY"] = "x"
>
> schema = {
>     "title": "ProductInfo",
>     "description": "Structured product data extracted from user text",
>     "type": "object",
>     "properties": {
>         "name": {
>             "type": "string",
>             "description": "Product name"
>         },
>         "price_pln": {
>             "type": "number",
>             "description": "Price in PLN"
>         },
>         "color": {
>             "type": "string",
>             "description": "Product color"
>         },
>         "volume_ml": {
>             "type": "integer",
>             "description": "Volume in milliliters"
>         },
>         "dishwasher_safe": {
>             "type": "boolean",
>             "description": "Whether the product is dishwasher safe"
>         }
>     },
>     "required": ["name", "price_pln"],
>     "additionalProperties": False
> }
> # same with pydantic model - langchain_core.exceptions.OutputParserException: Failed to parse ProductInfo from completion {"product_name": "Red ceramic mug", "capacity_ml": 350, "dishwasher_safe": true, "price": 24.99, "currency": "PLN"}.
>
> class ProductInfo(BaseModel):
>     model_config = ConfigDict(extra="forbid")
>
>     name: str = Field(description="Product name")
>     price_pln: float = Field(description="Price in PLN")
>     color: str | None = Field(default=None, description="Product color")
>     volume_ml: int | None = Field(default=None, description="Volume in milliliters")
>     dishwasher_safe: bool | None = Field(
>         default=None,
>         description="Whether the product is dishwasher safe",
>     )
>
> llm = ChatOpenRouter(
>     model="openrouter/hunter-alpha",
>     temperature=0,
>     max_retries=2,
> )
>
> structured_llm = llm.with_structured_output(
>     schema,
>     method="json_schema",
>     strict=True,
> )
>
> result = structured_llm.invoke(
>     "Extract product data from: Red ceramic mug, 350 ml, dishwasher-safe, price 24.99 PLN."
> )
>
> print(result)
> # {'product_name': 'Red ceramic mug', 'capacity': '350 ml', 'features': ['dishwasher-safe'], 'price': {'amount': 24.99, 'currency': 'PLN'}}
>
> Error Message and Stack Trace (if applicable)
>
>  Description
>
> The schema is not enforced, and it seems like LLM doesn't know about it
> System Info System Information
>
> OS: Darwin
> OS Version: Darwin Kernel Version 24.5.0: Tue Apr 22 19:54:43 PDT 2025;
> root:xnu-11417.121.6~2/RELEASE_ARM64_T8132
> Python Version: 3.14.2 (main, Jan 14 2026, 23:37:46) [Clang 21.1.4 ]
>
> Package Information
>
> langchain_core: 1.2.17
> langchain_community: 0.4.1
> langsmith: 0.7.12
> langchain_classic: 1.0.2
> langchain_openai: 1.1.10
> langchain_openrouter: 0.1.0
> langchain_text_splitters: 1.1.1
> langgraph_sdk: 0.3.9
>
> Optional packages not installed
>
> deepagents
> deepagents-cli
>
> Other Dependencies
>
> aiohttp: 3.13.3
> dataclasses-json: 0.6.7
> httpx: 0.28.1
> httpx-sse: 0.4.3
> jsonpatch: 1.33
> numpy: 2.4.3
> openai: 2.25.0
> openrouter: 0.7.11
> orjson: 3.11.7
> packaging: 26.0
> pydantic: 2.12.5
> pydantic-settings: 2.13.1
> pytest: 9.0.2
> PyYAML: 6.0.3
> pyyaml: 6.0.3
> requests: 2.32.5
> requests-toolbelt: 1.0.0
> sqlalchemy: 2.0.48
> SQLAlchemy: 2.0.48
> tenacity: 9.1.4
> tiktoken: 0.12.0
> typing-extensions: 4.15.0
> uuid-utils: 0.14.1
> websockets: 16.0
> xxhash: 3.6.0
> zstandard: 0.25.0
>
> —
> Reply to this email directly, view it on GitHub
> , or unsubscribe
> 
> .
> You are receiving this because you are subscribed to this thread.Message
> ID: ***@***.***>
>
