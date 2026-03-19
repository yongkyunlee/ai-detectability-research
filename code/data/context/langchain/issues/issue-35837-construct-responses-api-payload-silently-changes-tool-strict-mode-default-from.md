# _construct_responses_api_payload silently changes tool strict mode default from false to true

**Issue #35837** | State: open | Created: 2026-03-13 | Updated: 2026-03-16
**Author:** onmete
**Labels:** bug, openai, external

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

#25111 , #27423

### Reproduction Steps / Example Code (Python)

```python
from langchain_core.tools import StructuredTool
from langchain_openai import ChatOpenAI

async def my_tool(kind: str, field_selector: str = "") -> str:
    return f"{kind} {field_selector}"

tool = StructuredTool(
    name="resources_list",
    description="List Kubernetes resources",
    func=lambda **kw: "",
    coroutine=my_tool,
    args_schema={
        "type": "object",
        "properties": {
            "kind": {"type": "string", "description": "Resource kind"},
            "fieldSelector": {
                "type": "string",
                "description": "Field selector filter",
                "pattern": r"^[.\-A-Za-z0-9]+=.+$",
            },
        },
        "required": ["kind"],
    },
)

# Works correctly — Chat Completions API, strict defaults to false
llm = ChatOpenAI(model="gpt-4o")
llm_with_tools = llm.bind_tools([tool])
# Model treats schema as best-effort, generates sensible fieldSelector values

# Broken — adding reasoning triggers Responses API, strict silently becomes true
llm = ChatOpenAI(model="gpt-5", reasoning_effort="high")
llm_with_tools = llm.bind_tools([tool])
# Model now misinterprets the "pattern" regex as a literal value,
# e.g. sends fieldSelector="^[.\-A-Za-z0-9]+=.+$" instead of "status.phase=Running"

# Workaround — explicitly set strict=False
llm_with_tools = llm.bind_tools([tool], strict=False)
# Restores non-strict behavior, model generates correct arguments again
```

### Error Message and Stack Trace (if applicable)

```shell
No Python exception — the API accepts the schema. The model generates tool calls with incorrect arguments (regex patterns used as literal values), which then fail server-side. Example observed error from a downstream MCP tool:

Tool 'resources_list' execution failed after 1 attempt(s):
failed to list resources: unable to parse requirement: :
Invalid value: "/": prefix part must be non-empty; name part must be non-empty
```

### Description

When `langchain-openai` transparently switches from the Chat Completions API to the Responses API (triggered by the presence of `reasoning` parameters), the effective `strict` default for function tools changes silently.

In the Chat Completions API, omitting `strict` from a tool definition means non-strict (best-effort) tool calling. In the Responses API, omitting `strict` means `strict: true` (per OpenAI's docs: "strict: boolean — Whether to enforce strict parameter validation. Default true.").

`_construct_responses_api_payload` converts tools via:
```python
new_tools.append({"type": "function", **tool["function"]})
```
This preserves the absence of `strict`, but the semantics flip. Users who call `bind_tools(tools)` without explicit `strict` get non-strict behavior on Chat Completions but strict behavior on Responses API — without any warning or opt-in.

With `strict: true`, tools enter structured-outputs mode which only supports a subset of JSON Schema. Tool schemas containing unsupported keywords (e.g. `pattern`) cause the model to misinterpret regex constraints as literal argument values, producing broken tool calls. Schemas that don't set `additionalProperties: false` or don't mark all fields as required also violate strict mode requirements.

Suggested fix: In `_construct_responses_api_payload`, when a Chat Completions tool doesn't have strict set, explicitly set `"strict": False` in the Responses API tool to preserve the same semantics:
```python
func = tool["function"]
if "strict" not in func:
    func = {**func, "strict": False}
new_tools.append({"type": "function", **func})
```

### System Info

langchain-openai: 1.1.9
langchain-core: 1.2.18
openai: 1.109.1
Python: 3.12.3
OS: Linux (x86_64)

## Comments

**jackjin1997:**
Hi, I've submitted a fix for this issue in PR #35839. Could a maintainer please assign me to this issue so the PR can be reopened? Thanks\!

**ccurme:**
I suspect this problem is misdiagnosed. `llm_with_tools.kwargs` will show you the raw tool schema that is sent to OpenAI. I get:
```
{'tools': [{'type': 'function',
   'function': {'name': 'resources_list',
    'description': 'List Kubernetes resources',
    'parameters': {'type': 'object',
     'properties': {'kind': {'type': 'string', 'description': 'Resource kind'},
      'fieldSelector': {'type': 'string',
       'description': 'Field selector filter',
       'pattern': '^[.\\-A-Za-z0-9]+=.+$'}},
     'required': ['kind']}}}]}
```
for the Responses payload (no `strict`)

For specifying regex constraints on tool args, you might be interested in OpenAI's custom tools feature: https://docs.langchain.com/oss/python/integrations/chat/openai#context-free-grammars

**jackjin1997:**
Good point about the payload not including an explicit `strict` field — I dug into this a bit more and I think the issue is actually about the **API-level default difference** between the two endpoints:

- Chat Completions API defaults `strict` to `false` when omitted
- Responses API defaults `strict` to `true` when omitted ([OpenAI migration guide](https://platform.openai.com/docs/guides/migrate-to-responses), [related issue](https://github.com/vercel/ai/issues/11869))

So LangChain correctly omits `strict` from the payload, but because the two APIs interpret that omission differently, users get a silent behavior change when switching from Chat Completions to Responses API (e.g. by adding `reasoning_effort`).

The fix would be to explicitly pass `strict: false` in `_construct_responses_api_payload` when `strict` isn't set by the user, to preserve backward-compatible behavior. Happy to update my PR if that makes sense.

**passionworkeer:**
Hi! I'd like to work on this issue. Could you please assign it to me?
