# Make ToolCallLimitMiddleware proactive via before_model hook

**Issue #35766** | State: open | Created: 2026-03-11 | Updated: 2026-03-15
**Author:** 29swastik
**Labels:** langchain, feature request, external

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

### Feature Description

The `ToolCallLimitMiddleware` is currently reactive, which means the limit logic is invoked after the limit is reached which has few downsides:
1. This might make LLM to utilize tools less effectively since it is not aware of tool limit from the beginning. When the limit is reached we panick the LLM by sending tool call limit reached message all of a sudden which it was not aware of
2. The reactive way of detecting tool call limit leads to additional tool call which doesn't get used.

### Use Case

LLM can plan ahead if it is aware of the concept of tool call limit and MAYBE converge better. Compare it with how a human would act in real life, in a game if we are aware of no of retries/no of tries left we do plan accordingly right? 

### Proposed Solution

This can be implemted by using `@before_model` hook where an additional message is passed which informs LLM how many tool calls left.

```py
[
HumanMessage(content='Get all current affairs across the globe'),
HumanMessage(content=f'You are left with {tool_calls_left}' tool calls, plan accordingly), # inserted before model call
AIMessage(content=...)
ToolMessage(content=...)
HumanMessage(content=f'You are left with {tool_calls_left}' tool calls, plan accordingly), # inserted before next model call
AIMessage(content=...)
...
]
```

If this appraoch makes sense I'll be happy to raise the PR!

### Alternatives Considered
The proposed solution requires no additional configuration through constructor parameters and the remaining tool call left message is sent after each iteration., we can make few enhancements to the proposed solution:

1. Introduce new attributes to `ToolCallLimitMiddleware` class with which developers can configure the behaviour of tool call remaining message sent to LLM (as suggested in one of the comments below)

```py
class ToolCallLimitMiddleware(BaseCallbackHandler):
    def __init__(
        self,
        max_tool_calls: int = 50,
        proactive: bool = True,  # New flag
        warning_threshold: int = 5  # Warn when N calls left
    ):
        self.max_tool_calls = max_tool_calls
        self.proactive = proactive
        self.warning_threshold = warning_threshold
```

2. The tool call remaining message is sent using `HumanMessage` if this is not the right message type we can consider `ToolMessage`

## Comments

**laniakea001:**
This is a thoughtful proposal! The proactive approach makes sense — informing the LLM about tool call limits upfront can lead to more intentional tool usage rather than reactive panic when limits are hit.

Here are a few considerations for the implementation:

### Architecture Suggestion

The  hook approach is solid. You could extend the existing  with a new config flag:

### Implementation Strategy

1. **Track remaining calls**: Maintain a counter accessible via 
2. **Inject contextual message**: Use  to insert a  with remaining count
3. **Graceful degradation**: If , fall back to current reactive behavior

### Potential Enhancements

- **Adaptive warnings**: Instead of every turn, warn when 
- **Tool-family specific limits**: Different limits per tool category
- **Token budget integration**: Combine with total token limits for better planning

### Existing Patterns to Follow

Check  for how tool execution is tracked, and  for the callback pattern.

Happy to review the PR when you're ready! 🎯

**laniakea001:**
This is a thoughtful proposal! The proactive approach makes sense — informing the LLM about tool call limits upfront can lead to more intentional tool usage rather than reactive panic when limits are hit.

Here are a few considerations for the implementation:

### Architecture Suggestion

The `@before_model` hook approach is solid. You could extend the existing `ToolCallLimitMiddleware` with a new config flag:

```python
from langchain_core.callbacks import BaseCallbackHandler
from langchain_core.messages import HumanMessage
from typing import Optional

class ToolCallLimitMiddleware(BaseCallbackHandler):
    def __init__(
        self,
        max_tool_calls: int = 50,
        proactive: bool = True,  # New flag
        warning_threshold: int = 5  # Warn when N calls left
    ):
        self.max_tool_calls = max_tool_calls
        self.proactive = proactive
        self.warning_threshold = warning_threshold
```

### Implementation Strategy

1. **Track remaining calls**: Maintain a counter accessible via `agent_config`
2. **Inject contextual message**: Use `@before_model` hook to insert a `HumanMessage` with remaining count
3. **Graceful degradation**: If `proactive=False`, fall back to current reactive behavior

### Potential Enhancements

- **Adaptive warnings**: Instead of every turn, warn when `remaining <= warning_threshold`
- **Tool-family specific limits**: Different limits per tool category
- **Token budget integration**: Combine with total token limits for better planning

### Existing Patterns to Follow

Check `langgraph.prebuilt.tool_node` for how tool execution is tracked, and `langchain.agents.agent` for the callback pattern.

Happy to review the PR when you are ready! 🎯

**pawel-twardziak:**
I like this feature @29swastik  :) I proposed a PR (it got closed, fair), but if I got assigned to this issue, I could continue on it :)

**29swastik:**
> I like this feature [Swastik (@29swastik)](https://github.com/29swastik) :) I proposed a PR (it got closed, fair), but if I got assigned to this issue, I could continue on it :)

I think it gets closed if it is not assigned by maintainer (as per docs). 
>The pull request must link to an issue or discussion where a solution has been approved by a maintainer.

I was hoping to submit PR, nvm :)

**pawel-twardziak:**
> I think it gets closed if it is not assigned by maintainer (as per docs).

yes, I know why :)

> I was hoping to submit PR, nvm :)

Feel free to clone & modify my PR! Or raise something completely different by your idea :) I'm even encouraging you to do it :)
I'll rasie an equivalent PR in the JS repo then.

**29swastik:**
>I'm even encouraging you to do it :)

Thanks for the encouragement! 🙂

I'll take a look at your PR and see if I can build on top of it

Also, just to confirm, should we first align on the approach and finalize it so that the Python and JS implementations stay in sync?

**pawel-twardziak:**
Yes, we should :) Let's see where this thread goes and what the maintainers say. 
I'll follow it and give my input - my first input (it's already a part of my PR):

- two additional options to the existing middleware: `proactive=True` and `warning_builder=`,
- by default `proactiove` is disabled - for backward compatibility

**29swastik:**
>Yes, we should :) 

@pawel-twardziak I opened a new PR with 2 minor enhancements listed below:

1. Added initial context message which informs LLM about `thread_limit`, `run_limit` & `warning_threshold` which gets injected at the beginning of each run (i.e when the `tool_count` is zero). The idea is, giving LLM this context helps it in chosing the right starting point whereas the subsequent warning messages helps LLM in chosing right next step

2. `warning_threshold` can now accepts `int | list[int]`.
 - `int`: Warn when `remaining <= threshold` (continuous)
     -  e.g: warning_threshold=5 → warns at 5, 4, 3, 2, 1, 0
 - `list[int]`: Warn only when remaining exactly matches a value in the list (discrete)
     - e.g: warning_threshold=[5, 3, 1] → warns only at 5, 3, 1
