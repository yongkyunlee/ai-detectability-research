# `AnthropicPromptCachingMiddleware` breaks model fallback with `cache_control` param

**Issue #33709** | State: open | Created: 2025-10-29 | Updated: 2026-03-10
**Author:** bart0401
**Labels:** bug, anthropic, external

### Checked other resources

- [x] This is a bug, not a usage question.
- [x] I added a clear and descriptive title that summarizes this issue.
- [x] I used the GitHub search to find a similar question and didn't find it.
- [x] I am sure that this is a bug in LangChain rather than my code.
- [x] The bug is not resolved by updating to the latest stable version of LangChain (or the specific integration package).
- [x] This is not related to the langchain-community package.
- [x] I read what a minimal reproducible example is (https://stackoverflow.com/help/minimal-reproducible-example).
- [x] I posted a self-contained, minimal, reproducible example. A maintainer can copy it and run it AS IS.

### Example Code

```python
from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI
from langchain_anthropic.middleware.prompt_caching import AnthropicPromptCachingMiddleware
from langchain.agents.middleware import ModelFallbackMiddleware
from langchain.agents import create_agent

# Setup: Main model (Anthropic) with fallback to OpenAI
main_model = ChatAnthropic(
    model="claude-sonnet-4-latest",
    anthropic_api_key="YOUR_ANTHROPIC_KEY"
)

fallback_model = ChatOpenAI(
    model="gpt-4o-mini",
    openai_api_key="YOUR_OPENAI_KEY"
)

# Create middleware list
middleware = [
    AnthropicPromptCachingMiddleware(
        ttl="5m",
        unsupported_model_behavior="ignore"  # ← This doesn't prevent the bug
    ),
    ModelFallbackMiddleware(
        fallback_models=[fallback_model]
    )
]

# Create agent with middleware
agent = create_agent(
    model=main_model,
    system_prompt="You are a helpful assistant.",
    tools=[],
    middleware=middleware
)

# Trigger the bug:
# 1. Force Anthropic API to fail (e.g., network issue, rate limit)
# 2. ModelFallbackMiddleware kicks in → switches to OpenAI
# 3. OpenAI receives messages with cache_control parameter
# 4. Error: "AsyncCompletions.create() got an unexpected keyword argument 'cache_control'"

# Reproduce by invoking when Anthropic API is unstable
result = agent.invoke({"messages": [{"role": "user", "content": "Hello"}]})
```

### Error Message and Stack Trace (if applicable)

```
2025-10-29 09:07:14 [INFO] Chat model invocation: ChatAnthropic
2025-10-29 09:07:20 [ERROR] LLM error: peer closed connection without sending complete message body (incomplete chunked read)

# Fallback triggered
2025-10-29 09:07:20 [INFO] Fallback activated: ChatAnthropic -> ChatOpenAI
2025-10-29 09:07:20 [INFO] Chat model invocation: ChatOpenAI

# Fallback fails with cache_control error
2025-10-29 09:07:20 [ERROR] LLM error: AsyncCompletions.create() got an unexpected keyword argument 'cache_control'

Traceback (most recent call last):
  File "langchain/agents/react/graph.py", line 284, in invoke
    result = await fallback_model.ainvoke(messages, config)
  File "langchain_openai/chat_models/base.py", line 412, in ainvoke
    response = await self.async_client.chat.completions.create(**params)
TypeError: AsyncCompletions.create() got an unexpected keyword argument 'cache_control'
```

### Description

### Problem

When using `AnthropicPromptCachingMiddleware` together with `ModelFallbackMiddleware`, the middleware adds Anthropic-specific `cache_control` parameters to messages. If the Anthropic model fails and triggers a fallback to a non-Anthropic provider (e.g., OpenAI, Google), the fallback model receives messages with the `cache_control` parameter, causing a `TypeError`.

This completely breaks the fallback mechanism, forcing production systems to choose between prompt caching optimization (AnthropicPromptCachingMiddleware) or reliability (ModelFallbackMiddleware), but not both.

### Expected Behavior

1. Anthropic model fails with "peer closed connection"
2. ModelFallbackMiddleware activates and switches to OpenAI
3. AnthropicPromptCachingMiddleware should not apply `cache_control` to non-Anthropic models
4. OpenAI model succeeds and returns normal response

Note: The `unsupported_model_behavior="ignore"` parameter does not prevent this issue.

### Actual Behavior

1. Anthropic model fails with "peer closed connection"
2. AnthropicPromptCachingMiddleware.before_model() adds `cache_control` to messages
3. ModelFallbackMiddleware activates and switches to OpenAI
4. The same message objects (with `cache_control` still present) are reused
5. OpenAI model fails with TypeError: unexpected keyword argument 'cache_control'
6. Both models fail, resulting in complete service failure

### Root Cause

The AnthropicPromptCachingMiddleware modifies messages before the model invocation, but the `unsupported_model_behavior` parameter only controls whether to warn/raise/ignore when applied to non-Anthropic models. It does not remove `cache_control` parameters from messages.

When ModelFallbackMiddleware switches to a fallback model:
- The middleware pipeline does not re-run
- Messages already contain `cache_control` parameters
- Non-Anthropic providers reject these parameters

### Why unsupported_model_behavior="ignore" Does Not Help

```python
AnthropicPromptCachingMiddleware(
    ttl="5m",
    unsupported_model_behavior="ignore"  # Only affects warnings, not cleanup
)
```

This parameter:
- Prevents warnings/errors when middleware runs on non-Anthropic models
- Does not remove `cache_control` from messages after fallback
- Does not re-run middleware after fallback switches models

### Execution Flow

```
Step 1: AnthropicPromptCachingMiddleware.before_model()
  - Adds cache_control to messages (Anthropic-specific)
  - Modified messages: [{"role": "user", "content": "...", "cache_control": {"type": "ephemeral"}}]

Step 2: ChatAnthropic.invoke(messages)
  - Fails: "peer closed connection" (network/API issue)

Step 3: ModelFallbackMiddleware activates
  - Switches to ChatOpenAI
  - Reuses the SAME message objects (with cache_control still present)

Step 4: ChatOpenAI.invoke(messages)
  - Receives messages with cache_control parameter
  - TypeError: AsyncCompletions.create() got an unexpected keyword argument 'cache_control'
```

### System Info

```
System Information
------------------
OS: Linux
Python Version: 3.12.8

Package Information
-------------------
langchain-core: 1.0.1
langchain: 1.0.2
langchain-anthropic: 1.0.0
langchain-openai: 1.0.1
langgraph: 1.0.1
langgraph-checkpoint-postgres: 3.0.0
deepagents: 0.1.4
langmem: 0.0.28
```

Full package list from `python -m langchain_core.sys_info`:

```
langchain                      1.0.2
langchain-anthropic            1.0.0
langchain-aws                  1.0.0
langchain-community            1.0.0a1
langchain-core                 1.0.1
langchain-google-genai         3.0.0
langchain-google-vertexai      3.0.1
langchain-huggingface          1.0.0
langchain-openai               1.0.1
langgraph                      1.0.1
langgraph-checkpoint           3.0.0
langgraph-checkpoint-postgres  3.0.0
```

## Comments

**josiahcoad:**
I'm getting this too! (using deep agents which I think auto-injects this middleware?)

**dylan-clark-sh:**
This will be a problem for me in the near future once I fail over between OpenAI and Anthropic models.

**sydney-runkle:**
It's possible we'd want to clear the model settings to account for this, but that would be breaking. We could also add more hooks and solely clear the `cache_control` param.

**ccurme:**
Maybe a brittle solution but as a workaround you can swap the order of the middlewares:
```python
middleware = [
    ModelFallbackMiddleware(
        main_model, fallback_model
    ),
    AnthropicPromptCachingMiddleware(
        ttl="5m",
        unsupported_model_behavior="ignore"  # ← This doesn't prevent the bug
    ),
]
```
I can reproduce the issue and resolve it this way (this will ensure that the model is identified before the prompt-caching middleware, which checks for Anthropic models in the request).

**joy7758:**
Thanks for the clear repro. I'm exploring budget-aware middleware patterns around `create_agent`, and this lifecycle issue matters for routing and fallback control too.

If middleware-mutated messages are reused across fallback model calls without re-running the middleware pipeline, provider-specific state can leak into the next model attempt.

From an integration-side perspective, re-running middleware on fallback seems safer than treating the first middleware pass as globally reusable.

If helpful, I can sanity-check that against thin budget-gate middleware examples.
