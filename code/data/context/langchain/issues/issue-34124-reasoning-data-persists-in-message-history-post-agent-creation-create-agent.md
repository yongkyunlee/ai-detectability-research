# Reasoning data persists in message history post-agent creation (create_agent)

**Issue #34124** | State: open | Created: 2025-11-27 | Updated: 2026-03-18
**Author:** ai-blockchain-dev
**Labels:** bug, investigate, langchain, openai, external

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
- [ ] langchain-cli
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

### Example Code (Python)

```python
init_chat_model(
    openai_api_key=Config.MODEL_API_KEY,           # API Key for model auth
    model=Config.MODEL_NAME or "doubao-seed-1-6-251015",  # Preferred model or fallback
    model_provider="openai",                       # Provider name
    base_url=Config.MODEL_API_BASE_URL,            # Custom endpoint
    temperature=0,                                 # Deterministic behavior
    extra_body={"thinking": {"type": "enabled"}},  # Enable reasoning mode
    stream_usage=True,                             # Stream tokens live
    use_responses_api=True,                        # Use responses endpoint
)
```

### Error Message and Stack Trace (if applicable)

```shell
❗ ERROR — Agent Invocation Failed

File "Cell In[9]", line 25
  ├─ weather_agent = create_agent(
  │     model=llm,
  │     tools=[get_weather],
  │     system_prompt="You are a helpful assistant",
  │ )
  │
  └─ result = weather_agent.invoke(
        input={"messages": [HumanMessage(content="What's the weather like in San Francisco?")]}
     )

Traceback (most recent call last):
  File ".../langgraph/pregel/main.py", line 3094, in Pregel.invoke
    for chunk in self.stream(input, config, ...):
      ⋮
  File ".../langgraph/pregel/main.py", line 1049
    break

AssertionError: could not resolve response (should never happen)
```

### Description

When invoking an agent generated using create_agent, execution fails.
Expected outcome: The agent should correctly handle input messages and filter out reasoning fields prior to LLM API calls.

### System Info

OS: Windows 10.0.26200

Python: 3.13.1 (64-bit, MSC v.1942, built Jan 14 2025)

## Comments

**matiasdev30:**
When use_responses_api=True and reasoning is enabled, reasoning blocks persist in message history between tool calls. The API expects these blocks to be formatted correctly in subsequent requests. LangChain fails to filter them properly, causing a BadRequestError (HTTP 400), which LangGraph surfaces as AssertionError: could not resolve response.

Fix: Add output_version="responses/v1" to your model initialization:

```
init_chat_model(
    # ... existing params ...
    output_version="responses/v1"  # Add this
)
```

If that doesn't work, also add:
`use_previous_response_id=True`

Alternative: Disable reasoning if not needed:
`extra_body={"thinking": {"type": "disabled"}}`

**thromel:**
## Investigation Summary

After thorough investigation of this issue, I've determined that **this is expected behavior** rather than a bug, though it highlights a need for better documentation around the Responses API configuration.

### Understanding the Issue

When using `create_agent` with `use_responses_api=True` and reasoning enabled, reasoning blocks from the model's response are included in subsequent API requests. This causes errors in two scenarios:

1. **Non-OpenAI endpoints** (like Doubao in this case) that don't fully implement OpenAI's Responses API spec
2. **Missing configuration** that leads to format mismatches

### Why This Behavior is Correct for OpenAI

According to [OpenAI's documentation on handling function calls with reasoning models](https://cookbook.openai.com/examples/reasoning_function_calls):

> *"It is essential that we preserve any reasoning and function call responses in our conversation history. This is how the model keeps track of what chain-of-thought steps it has run through. The API will error if these are not included."*

And from the [Responses API reasoning items guide](https://cookbook.openai.com/examples/responses_api/reasoning_items):

> *"If a turn includes a function call (which may require an extra round trip outside the API), you do need to include the reasoning items—either via `previous_response_id` or by explicitly adding the reasoning item to `input`."*

So LangChain is correctly including reasoning items as required by OpenAI's API.

### The Real Issue

The problem occurs because:

1. **For non-OpenAI endpoints**: These APIs may not support reasoning blocks in input at all, making the Responses API incompatible
2. **Missing `output_version` configuration**: Without explicit `output_version="responses/v1"`, format inconsistencies can occur

### Solution

The workaround mentioned by @matiasdev30 is correct:

```python
init_chat_model(
    model="your-model",
    model_provider="openai",
    base_url="your-endpoint",
    use_responses_api=True,
    output_version="responses/v1",  # Ensures consistent format
    use_previous_response_id=True,   # Server maintains reasoning state
    # ... other params
)
```

**Why this works:**

| Parameter | Effect |
|-----------|--------|
| `output_version="responses/v1"` | Ensures AIMessage content uses the correct v1 format for the Responses API |
| `use_previous_response_id=True` | Instead of sending reasoning blocks back, uses the response ID to let the server maintain reasoning state. This avoids sending reasoning blocks in input entirely. |

### For Non-OpenAI Endpoints

If your endpoint doesn't support `previous_response_id`:

1. **Disable reasoning mode**: `extra_body={"thinking": {"type": "disabled"}}`
2. **Use Chat Completions API instead**: Don't set `use_responses_api=True`

### Recommendation

I suggest closing this issue as "works as designed" since:

1. The current behavior follows OpenAI's specification
2. Working solutions exist via proper configuration
3. Non-OpenAI endpoints may have varying levels of Responses API support

However, it would be valuable to **improve documentation** around:
- Required configuration when using reasoning with `create_agent`
- Compatibility considerations for non-OpenAI endpoints
- The relationship between `output_version`, `use_previous_response_id`, and reasoning

---

**Sources:**
- [OpenAI Cookbook: Handling Function Calls with Reasoning Models](https://cookbook.openai.com/examples/reasoning_function_calls)
- [OpenAI Cookbook: Better performance from reasoning models using the Responses API](https://cookbook.openai.com/examples/responses_api/reasoning_items)
- [OpenAI Blog: Why we built the Responses API](https://developers.openai.com/blog/responses-api/)

**AhmedEmam7:**
When something like this happens, how do you usually debug it?

Is it easy to trace where the state went wrong, or does it take a lot of trial and error?

**maxsnow651-dev:**
Maybe we can improve error handling here

On Wed, Mar 18, 2026, 4:35 AM AhmedEmam7 ***@***.***> wrote:

> *AhmedEmam7* left a comment (langchain-ai/langchain#34124)
> 
>
> When something like this happens, how do you usually debug it?
>
> Is it easy to trace where the state went wrong, or does it take a lot of
> trial and error?
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
