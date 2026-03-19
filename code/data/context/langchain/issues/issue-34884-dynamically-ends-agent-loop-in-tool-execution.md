# Dynamically ends Agent loop in Tool execution

**Issue #34884** | State: open | Created: 2026-01-26 | Updated: 2026-03-08
**Author:** jectpro7
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
- [ ] langchain-perplexity
- [ ] langchain-prompty
- [ ] langchain-qdrant
- [ ] langchain-xai
- [ ] Other / not sure / general

### Feature Description

Now tool support `return_direct` feature, tool will end the loop when setting it to `true`. Or a structure response tool can end loop.

But sometime we don't know it should end or not before execution. This feature is for allowing the tool to decide whether the agent loop should stop after the tool execution.

### Use Case

Some message need to be returned directly

### Proposed Solution

```
@tool
def verify_value(value):
    if verify(value):
        return Command(update={"jump_to": "end"}) # supports jump_to in tool
    return "verify failed ..."
```

### Alternatives Considered

_No response_

### Additional Context

_No response_

## Comments

**jectpro7:**
Hi @ccurme @mdrxy, I have created a PR to address the issue, would be glad to see if you have any comments.

**bmdhodl:**
I needed the same thing — a way for tools to signal "I'm done, stop the agent loop."

The pattern I use is a LoopGuard that sits outside the agent loop and watches for completion conditions. For LangChain specifically, there's a callback handler that wires this in automatically:

```python
from agentguard import LoopGuard, BudgetGuard
from agentguard.integrations.langchain import AgentGuardCallbackHandler

handler = AgentGuardCallbackHandler(
    loop_guard=LoopGuard(max_repeats=3),
    budget_guard=BudgetGuard(max_tokens=50000),
)

# The handler auto-traces all chain/tool/LLM calls
# and raises LoopDetected if a tool is called 3x with the same args
llm = ChatOpenAI(callbacks=[handler])
```

For the "tool decides the task is complete" use case, you can raise a custom exception from your tool and catch it at the agent level — the handler will log it as a clean exit rather than an error.

`pip install agentguard47[langchain]`

Repo: https://github.com/bmdhodl/agent47

Not a native LangChain solution, but might be useful until there's built-in support. Happy to discuss the approach.

**jectpro7:**
Looks great, the BudgetGuard is also very important for production agent, I have seen similar approach in "_Budget-Aware Tool-Use Enables Effective Agent Scaling_" from deepmind team. Is this based on Langchain Agent middleware?

**Aye10032:**
Similarly, I tried using
```python
return Command(goto='__end__')
```
but it still cannot directly end the loop. Look forward to related functionality.
