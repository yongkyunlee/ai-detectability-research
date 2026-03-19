# Args with default_factory in a tool's args_schema should not be required

**Issue #35547** | State: closed | Created: 2026-03-04 | Updated: 2026-03-08
**Author:** liaowang11
**Labels:** core, langchain, feature request, external

### Checked other resources

- [x] This is a feature request, not a bug report or usage question.
- [x] I added a clear and descriptive title that summarizes the feature request.
- [x] I used the GitHub search to find a similar feature request and didn't find it.
- [x] I checked the LangChain documentation and API reference to see if this feature already exists.
- [x] This is not related to the langchain-community package.

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

### Feature Description

When a tool is defined to have a Pydantic-based args_schema with default_factory, the tool schema generated should not put that arg are "required"

### Use Case

As in https://github.com/langchain-ai/langchain/issues/34384, langchain currently will populate args with `default` and `default_factory`. But the tool schema generated still put theses fields in "required", forcing the LLM to generate these fields. 

Here is an example snippet:
```python
import json

from langchain_core.tools import tool
from langchain_core.utils.function_calling import convert_to_openai_tool
from pydantic import BaseModel, Field

class Args(BaseModel):
    """Hello"""
    names: list[str] = Field(default_factory=list, description="Some names")

@tool(args_schema=Args)
def some_func(name: list[str] = None):
    pass

print(json.dumps(convert_to_openai_tool(some_func), indent=2))

```

Outputs(note `names` in `required`):
```json
{
  "type": "function",
  "function": {
    "name": "some_func",
    "description": "Hello",
    "parameters": {
      "properties": {
        "names": {
          "description": "Some names",
          "items": {
            "type": "string"
          },
          "type": "array"
        }
      },
      "required": [
        "names"
      ],
      "type": "object"
    }
  }
}
```

### Proposed Solution

Langchain dynamically create a new model when generating tool schema in `tool_call_schema`, currently it only copies `field.default` not `field.default_factory` thus making the generated schema incorrect.
https://github.com/langchain-ai/langchain/blob/e50625e7c3cac04be68ae095bee030e0c321ef34/libs/core/langchain_core/utils/pydantic.py#L245

### Alternatives Considered

Using `Field(default=[])` works, but it maybe a little misleading.

### Additional Context

_No response_
