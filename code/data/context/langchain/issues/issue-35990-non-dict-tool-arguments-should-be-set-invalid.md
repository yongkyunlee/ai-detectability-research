# Non-dict tool arguments should be set invalid

**Issue #35990** | State: open | Created: 2026-03-17 | Updated: 2026-03-18
**Author:** TideDra
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

_No response_

### Reproduction Steps / Example Code (Python)

```python
The `tool_call` field of AIMessage requires its arguments to be an dict:

class ToolCall(TypedDict):
    """Represents an AI's request to call a tool.

    Example:
        
        {"name": "foo", "args": {"a": 1}, "id": "123"}
        

        This represents a request to call the tool named `'foo'` with arguments
        `{"a": 1}` and an identifier of `'123'`.

    !!! note "Factory function"

        `tool_call` may also be used as a factory to create a `ToolCall`. Benefits
        include:

        * Required arguments strictly validated at creation time
    """

    name: str
    """The name of the tool to be called."""

    args: dict[str, Any]
    """The arguments to the tool call as a dictionary."""

    id: str | None
    """An identifier associated with the tool call.

    An identifier is needed to associate a tool call request with a tool
    call result in events when multiple concurrent tool calls are made.
    """

    type: NotRequired[Literal["tool_call"]]
    """Used for discrimination."""

While the conversion function only treats a tool call triggering JSONDecodeError as invalid tool call. Arguments deserialized as other types will trigger ValidationError of AIMessage:

def __construct_lc_result_from_response_api():
...
            try:
                args = json.loads(output.arguments, strict=False)
                if not isinstance(args, dict):
                    raise TypeError("Arguments must be a dictionary")
                error = None
            except (JSONDecodeError, TypeError) as e:
                args = output.arguments
                error = str(e)
            if error is None:
                tool_call = {
                    "type": "tool_call",
                    "name": output.name,
                    "args": args,
                    "id": output.call_id,
                }
                tool_calls.append(tool_call)
            else:
                tool_call = {
                    "type": "invalid_tool_call",
                    "name": output.name,
                    "args": args,
                    "id": output.call_id,
                    "error": error,
                }
                invalid_tool_calls.append(tool_call)
```

### Error Message and Stack Trace (if applicable)

```shell

```

### Description

tool arguments that can be deserialized via `json.loads` is not necessarily a dict. Other types will trigger ValidationError of AIMessage.

### System Info

System Information
------------------
> OS:  Linux
> OS Version:  #17~24.04.1-Ubuntu SMP Mon Dec  1 20:10:50 UTC 2025
> Python Version:  3.13.11 (main, Dec  9 2025, 19:04:10) [Clang 21.1.4 ]

Package Information
-------------------
> langchain_core: 1.2.8
> langchain: 1.2.8
> langsmith: 0.6.8
> langchain_openai: 1.1.7
> langgraph_sdk: 0.3.3

Optional packages not installed
-------------------------------
> langserve

Other Dependencies
------------------
> httpx: 0.28.1
> jsonpatch: 1.33
> langgraph: 1.0.7
> openai: 2.13.0
> orjson: 3.11.7
> packaging: 25.0
> pydantic: 2.12.5
> pytest: 9.0.2
> pyyaml: 6.0.3
> requests: 2.32.5
> requests-toolbelt: 1.0.0
> rich: 14.3.2
> tenacity: 9.1.2
> tiktoken: 0.12.0
> typing-extensions: 4.15.0
> uuid-utils: 0.14.0
> xxhash: 3.6.0
> zstandard: 0.25.0

## Comments

**gitbalaji:**
Hi, I'd like to work on this. Could a maintainer please assign it to me?

**TideDra:**
I have a PR fixing this #35991

**maxsnow651-dev:**
Assign me to this please

On Tue, Mar 17, 2026, 7:01 AM Geary.Z ***@***.***> wrote:

> *TideDra* left a comment (langchain-ai/langchain#35990)
> 
>
> I have a PR fixing this #35991
> 
>
> —
> Reply to this email directly, view it on GitHub
> ,
> or unsubscribe
> 
> .
> You are receiving this because you are subscribed to this thread.Message
> ID: ***@***.***>
>

**gitbalaji:**
Hi, I've opened PR #36052 with a fix for this issue. The fix adds a non-dict check after `json.loads()` so that valid JSON arrays, strings, numbers, booleans, and null are all routed to `invalid_tool_calls` instead of causing a `ValidationError`. Tests for all 5 non-dict cases are included and passing.

Could a maintainer please assign this issue to me so the PR can be reviewed? Happy to make any adjustments!

**maxsnow651-dev:**
Following up in case this is relevant

On Wed, Mar 18, 2026, 1:52 AM Balaji Seshadri ***@***.***>
wrote:

> *gitbalaji* left a comment (langchain-ai/langchain#35990)
> 
>
> Hi, I've opened PR #36052
>  with a fix for
> this issue. The fix adds a non-dict check after json.loads() so that
> valid JSON arrays, strings, numbers, booleans, and null are all routed to
> invalid_tool_calls instead of causing a ValidationError. Tests for all 5
> non-dict cases are included and passing.
>
> Could a maintainer please assign this issue to me so the PR can be
> reviewed? Happy to make any adjustments!
>
> —
> Reply to this email directly, view it on GitHub
> ,
> or unsubscribe
> 
> .
> You are receiving this because you commented.Message ID:
> ***@***.***>
>

**ccurme:**
Do you have a reproducible example / can you clarify the issue? Are you saying we should add runtime checks to assert `args` is a dict? Curious if a specific model is violating this.

**TideDra:**
> Do you have a reproducible example / can you clarify the issue? Are you saying we should add runtime checks to assert `args` is a dict? Curious if a specific model is violating this.

Weak models that have strong hallucinations deployed by local inference engine, may output invalid tool calls that can be parsed and deserialized. e.g. `{"name":"search","arguments":"hello"}`, where (1) the tool tags are valid (2) can be deserialized as dict (3) both the `name`and `arguments` fields exists, so it will be extracted as a valid tool call by the parser. The inference engines, openai client, and langchain parser all do not check the type of arguments. But AIMessage requires the arguments of its tool call be a dict. So this case will trigger pydantic vallidation error when converting it to AIMessage, because "hello" is a string. So we need to check the type of arguments in langchain parser, and put such tool calls into the invalid_tool_calls.
