# core: documentation of `@tool` decorator lists an incorrect requirement

**Issue #31405** | State: closed | Created: 2025-05-29 | Updated: 2026-03-03
**Author:** krassowski
**Labels:** investigate, core, external

### Checked other resources

- [x] I added a very descriptive title to this issue.
- [x] I used the GitHub search to find a similar question and didn't find it.
- [x] I am sure that this is a bug in LangChain rather than my code.
- [x] The bug is not resolved by updating to the latest stable version of LangChain (or the specific integration package).
- [x] I posted a self-contained, minimal, reproducible example. A maintainer can copy it and run it AS IS.

### Example Code

N/A

### Error Message and Stack Trace (if applicable)

_No response_

### Description

The documentation of `@tool` lists two requirements:

> **Requires:**
> - Function must be of type (str) -> str
> - Function must have a docstring

However the same documentation shows examples which contradict the first requirement.

This example on 
https://api.python.langchain.com/en/latest/tools/langchain_core.tools.tool.html accepts more than one argument and accepts non-string argument:

```python
@tool(parse_docstring=True)
def foo(bar: str, baz: int) -> str:
    """The foo.

    Args:
        bar: The bar.
        baz: The baz.
    """
    return bar
```

This example on https://python.langchain.com/v0.2/docs/how_to/custom_tools/#tool-decorator returns an `int`:

```Python
@tool
def multiply(a: int, b: int) -> int:
    """Multiply two numbers."""
    return a * b
```

I am noting this incorrect documentation because I was trying to specify the return type, but I see this is basically ignored, and unless it is mentioned in the docstring the LLM will not be able to choose the tool giving it the output type it desires. Separately, of the documentation issue, would a suggestion to extract the output type and include it in the generated description be accepted?

### System Info

N/A

## Comments

**keenborder786:**
Specifying return_type is not supported in OpenAI Tool Call Format. And if you think about it, LLM does not that need that information for tool execution.

**krassowski:**
> And if you think about it, LLM does not that need that information for tool execution.

It does in https://github.com/langchain-ai/langgraph-codeact. It also does if user requests something where the tool to call can be discriminated based on the return type:

```python
@tool
def take_from_top_shelf() -> Tea:
    ...

@tool
def take_from_bottom_shelf() -> Coffee:
    ...
```

> Hi LLM, get me some tea please!

**RichardKlem:**
I strongly agree with @krassowski. Another benefit of parsing the `Returns` section is that the agent(LLM) can better understand the content and work with it further correctly.

**JulianoLagana:**
To add to the discussion, up until today I relied on LangChain to stringify the output from my `@tool`-decorated functions for me. 

But now I noticed that LangChain does that in [`BaseTool.run`](https://github.com/langchain-ai/langchain/blob/bc91a4811c454511af50a2fbd95f48f024b5738a/libs/core/langchain_core/tools/base.py#L889), when calling `_format_output`, which will **fail to stringify** a `[]` output from the tool (because the `all` in `_is_message_content_type` evaluates to True for an empty list).

In my case, my tool was returning a list of documents, which were being correctly stringified automatically by LangChain. Until it returned an empty list (failed to find any relevant documents). This was not stringified, and LangChain created a ToolMessage with `content` set to `[]` (not a string).

This might be a bug, or maybe it was indeed intended for `@tool` to only decorate `str -> str` functions.

**shivangraikar:**
I can submit a docs-only PR clarifying the actual requirements shown in the examples.

**JulianoLagana:**
@shivangraikar, now that the docs don't restrict the use of `@tool` to `str`->`str` only anymore, maybe the behavior I mentioned above should be addressed as a bug?
