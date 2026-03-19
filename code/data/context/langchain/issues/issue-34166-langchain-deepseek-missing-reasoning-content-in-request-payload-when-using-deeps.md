# [langchain-deepseek] Missing `reasoning_content` in request payload when using deepseek-reasoner with tool calling

**Issue #34166** | State: open | Created: 2025-12-02 | Updated: 2026-03-07
**Author:** yefengzi7
**Labels:** bug, deepseek, external

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
- [ ] langchain-cli
- [ ] langchain-model-profiles
- [ ] langchain-tests
- [ ] langchain-text-splitters
- [ ] langchain-chroma
- [x] langchain-deepseek
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
### Checked other resources

- [x] I added a very descriptive title to this issue.
- [x] I searched the LangChain documentation with the integrated search.
- [x] I used the GitHub search to find a similar question and didn't find it.
- [x] I am sure that this is a bug in LangChain rather than my code.
- [x] The bug is not resolved by updating to the latest stable version of LangChain (or the specific integration package).

### Example Code

from langchain_deepseek import ChatDeepSeek
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from langchain_core.tools import tool

@tool
def calculator(a: float, b: float) -> float:
    """Add two numbers."""
    return a + b

llm = ChatDeepSeek(model="deepseek-reasoner")
llm_with_tools = llm.bind_tools([calculator])

# First call - works fine
messages = [HumanMessage(content="What is 1 + 2?")]
response = llm_with_tools.invoke(messages)
# response.additional_kwargs contains 'reasoning_content'

# Simulate tool execution
messages.append(response)
messages.append(ToolMessage(content="3", tool_call_id=response.tool_calls[0]["id"]))

# Second call - fails with 400 error
response2 = llm_with_tools.invoke(messages)  # ERROR!
```

### Error Message and Stack Trace (if applicable)

```shell
Error code: 400 - {'error': {'message': 'Missing `reasoning_content` field in the assistant message at message index 1. For more information, please refer to https://api-docs.deepseek.com/guides/thinking_with_tools', 'type': 'invalid_request_error', 'param': None, 'code': 'invalid_request_error'}}
```

### Description

### Checked other resources

- [x] I added a very descriptive title to this issue.
- [x] I searched the LangChain documentation with the integrated search.
- [x] I used the GitHub search to find a similar question and didn't find it.
- [x] I am sure that this is a bug in LangChain rather than my code.
- [x] The bug is not resolved by updating to the latest stable version of LangChain (or the specific integration package).

### Example Code

```python
from langchain_deepseek import ChatDeepSeek
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from langchain_core.tools import tool

@tool
def calculator(a: float, b: float) -> float:
    """Add two numbers."""
    return a + b

llm = ChatDeepSeek(model="deepseek-reasoner")
llm_with_tools = llm.bind_tools([calculator])

# First call - works fine
messages = [HumanMessage(content="What is 1 + 2?")]
response = llm_with_tools.invoke(messages)
# response.additional_kwargs contains 'reasoning_content'

# Simulate tool execution
messages.append(response)
messages.append(ToolMessage(content="3", tool_call_id=response.tool_calls[0]["id"]))

# Second call - fails with 400 error
response2 = llm_with_tools.invoke(messages)  # ERROR!

### System Info

System Information
OS: Windows
OS Version: 10.0.22631
Python Version: 3.12.12

Package Information
langchain_core: 1.1.0
langchain: 1.1.0
langchain_deepseek: 1.0.1
langchain_openai: 1.1.0
langgraph: 1.0.3
openai: 2.8.1

## Comments

**iantinney:**
I'll take a look into this, shouldn't be too hard to fix. Would appreciate if someone assigns it, thanks

**Jiweipy:**
# Bug Fix Proposal: ChatDeepSeek Class Missing `reasoning_content` Field for Reasoning Models

## Issue Description
When using DeepSeek reasoning models (e.g., `deepseek-reasoner`) with tool calling functionality, the ChatDeepSeek class throws a 400 error:

```json
BadRequestError: Error code: 400 - {'error': {'message': 'Missing `reasoning_content` field in the assistant message at message index 2', 'type': 'invalid_request_error', 'param': None, 'code': 'invalid_request_error'}}
```

## Root Cause
The DeepSeek reasoning model API requires assistant messages to include a reasoning_content field, even if it's empty. The current ChatDeepSeek._get_request_payload() method does not properly handle this `requirement.

## Reproduction Steps

- Create a ChatDeepSeek instance with the deepseek-reasoner model

- Use tool calling functionality

- After the model generates a response containing tool calls, continue the conversation

- The second assistant message lacks the reasoning_content field, causing the API to return a 400 error

## Solution

Modify the ChatDeepSeek._get_request_payload() method to ensure all assistant messages include the reasoning_content field.

## Specific Changes

file_path_class: `site-packages/langchain_deepseek/chat_models.py`  => `class ChatDeepSeek(BaseChatOpenAI)`

```python
def _get_request_payload(
    self,
    input_: LanguageModelInput,
    *,
    stop: list[str] | None = None,
    **kwargs: Any,
) -> dict:
    payload = super()._get_request_payload(input_, stop=stop, **kwargs)
    
    # Ensure assistant messages include reasoning_content field
    for i, message in enumerate(payload["messages"]):
        if message["role"] == "assistant":
            # DeepSeek API expects assistant content to be a string, not a list
            if isinstance(message["content"], list):
                text_parts = [
                    block.get("text", "")
                    for block in message["content"]
                    if isinstance(block, dict) and block.get("type") == "text"
                ]
                message["content"] = "".join(text_parts) if text_parts else ""
            
            # Ensure each assistant message includes reasoning_content field
            # Get reasoning content from additional_kwargs, or set to empty string if not present
            if "reasoning_content" not in message:
                # Try to get reasoning content from original message
                if isinstance(input_, list) and i < len(input_):
                    original_msg = input_[i]
                    if hasattr(original_msg, 'additional_kwargs'):
                        reasoning = original_msg.additional_kwargs.get("reasoning_content", "")
                        message["reasoning_content"] = reasoning
                    else:
                        message["reasoning_content"] = ""
                else:
                    message["reasoning_content"] = ""
        
        # Handle tool messages
        elif message["role"] == "tool" and isinstance(message["content"], list):
            message["content"] = json.dumps(message["content"])
    
    return payload
```

**giulio-leone:**
I've submitted a fix in #35620.

**Root cause**: `_create_chat_result()` correctly stores `reasoning_content` in `AIMessage.additional_kwargs`, but `_get_request_payload()` doesn't re-inject it into the API payload for subsequent turns. The parent `BaseChatOpenAI._convert_message_to_dict()` doesn't know about this DeepSeek-specific field, so it gets silently dropped.

**Fix**: In `_get_request_payload()`, resolve the original input messages and extract `reasoning_content` from `additional_kwargs` for each assistant message. Defaults to empty string when absent (matching the API requirement).

All 27 unit tests pass, including 2 new tests for this specific scenario.
