# create_agent Does Not Handle invalid_tool_calls from JSON Parsing Errors (langchain alpha v1)

**Issue #33504** | State: open | Created: 2025-10-15 | Updated: 2026-03-12
**Author:** cladden
**Labels:** bug, langchain, external

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

Complete test script that reproduces the bug:

```python
"""
Minimal reproduction of LangChain bug: create_agent doesn't handle invalid_tool_calls

Run this script to see the bug in action.
"""

import asyncio
from langchain.agents import create_agent
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.tools import tool

@tool
def write_file(file_path: str, content: str) -> str:
    """Write content to a file."""
    return f"Wrote to {file_path}"

class MockChatModel(BaseChatModel):
    """Mock chat model that simulates invalid_tool_calls from JSON parsing errors."""

    @property
    def _llm_type(self) -> str:
        return "mock"

    def _generate(self, *args, **kwargs):
        raise NotImplementedError("Use ainvoke instead")

    def bind_tools(self, tools, **kwargs):
        """Return self to allow tool binding."""
        return self

    async def ainvoke(self, messages, config=None):
        """Return AIMessage with invalid_tool_calls on first call."""
        ai_message_count = sum(1 for m in messages if isinstance(m, AIMessage))

        if ai_message_count == 0:
            # First call: Simulate LLM generating malformed JSON
            return AIMessage(
                content="",
                tool_calls=[],  # Empty because JSON parsing failed
                invalid_tool_calls=[
                    {
                        "id": "call-123",
                        "name": "write_file",
                        "args": '{"file_path": "test.txt", "content": "Hello World"]',
                        "error": "Expecting ',' delimiter: line 1 column 50 (char 49)",
                    }
                ],
            )
        else:
            # Second call: If we get here, the agent continued
            return AIMessage(content="I see the error, let me fix it...")

async def main():
    model = MockChatModel()
    agent = create_agent(model=model, tools=[write_file])

    result = await agent.ainvoke(
        {"messages": [HumanMessage(content="Write 'Hello World' to test.txt")]}
    )

    # Count how many times the model was called
    ai_message_count = sum(1 for m in result["messages"] if isinstance(m, AIMessage))

    print(f"Model was called {ai_message_count} time(s)")
    print(f"Final message: {result['messages'][-1]}")

    if ai_message_count == 1:
        print("\n❌ BUG CONFIRMED: Agent exited after first call")
        print("   No ToolMessage created, LLM never saw the error")
    else:
        print("\n✅ Bug fixed: Agent continued after invalid_tool_calls")

if __name__ == "__main__":
    asyncio.run(main())
```

### Error Message and Stack Trace (if applicable)

**Expected Output**: Agent should continue after seeing the error
**Actual Output**:
```
Model was called 1 time(s)
Final message: content='' tool_calls=[] invalid_tool_calls=[...]

❌ BUG CONFIRMED: Agent exited after first call
   No ToolMessage created, LLM never saw the error
```

### Description

## Root Cause Analysis

### Issue 1: Routing Logic Ignores `invalid_tool_calls`

**File**: `langchain/agents/factory.py`, lines 1413-1414

```python
def model_to_tools(state: dict[str, Any]) -> str | list[Send] | None:
    last_ai_message, tool_messages = _fetch_last_ai_and_tool_messages(state["messages"])

    # if the model hasn't called any tools, exit the loop
    if len(last_ai_message.tool_calls) == 0:  #  tuple[list[ToolCall], ...]:
    latest_ai_message = next(m for m in reversed(messages) if isinstance(m, AIMessage))
    tool_calls = list(latest_ai_message.tool_calls)  #  str | list[Send] | None:
    last_ai_message, tool_messages = _fetch_last_ai_and_tool_messages(state["messages"])

    # if the model hasn't called any tools, exit the loop
    if len(last_ai_message.tool_calls) == 0:  #  tuple[list[ToolCall], ...]:
    latest_ai_message = next(m for m in reversed(messages) if isinstance(m, AIMessage))
    tool_calls = list(latest_ai_message.tool_calls)  #  CompiledStateGraph:
    """Creates an agent graph that calls tools in a loop.

    Args:
        handle_parsing_errors: If True, automatically convert invalid_tool_calls
            to ToolMessages so the LLM can see parsing errors and retry.
    """
```

### Option 2: Fix Routing Logic

Update `_make_model_to_tools_edge` to check for `invalid_tool_calls`:

```python
def model_to_tools(state: dict[str, Any]) -> str | list[Send] | None:
    last_ai_message, tool_messages = _fetch_last_ai_and_tool_messages(state["messages"])

    # Check for invalid tool calls before exiting
    if len(last_ai_message.tool_calls) == 0:
        # If there are invalid_tool_calls, convert them to ToolMessages
        if hasattr(last_ai_message, 'invalid_tool_calls') and last_ai_message.invalid_tool_calls:
            # Create ToolMessage for each invalid call
            error_messages = [
                ToolMessage(
                    content=f"Error: {inv['error']}",
                    tool_call_id=inv["id"],
                    status="error"
                )
                for inv in last_ai_message.invalid_tool_calls
            ]
            # Append error messages and continue loop
            state["messages"].extend(error_messages)
            return model_destination  # Continue, don't exit
        return end_destination
```

### Option 3: Handle in Middleware Layer

Provide built-in middleware that converts `invalid_tool_calls` automatically (this is what we currently do as a workaround).

## Current Workaround

We've implemented custom middleware to handle this:

```python
class ToolErrorHandlingMiddleware(AgentMiddleware):
    """Middleware that converts invalid_tool_calls to ToolMessages.

    This allows tools to raise ToolException for recoverable errors and
    handles JSON parsing errors from invalid_tool_calls that the LLM can see.
    """

    def after_model(self, state: AgentState[Any], runtime: Runtime[Any]) -> dict[str, Any] | None:
        """Convert invalid_tool_calls to ToolMessages so the LLM can see the error."""
        messages = state.get("messages", [])
        if not messages:
            return None

        last_message = messages[-1]
        if not isinstance(last_message, AIMessage):
            return None

        invalid_tool_calls = getattr(last_message, "invalid_tool_calls", None)
        if not invalid_tool_calls:
            return None

        # Convert each invalid tool call to a ToolMessage with error
        error_messages: list[ToolMessage] = []
        for invalid_call in invalid_tool_calls:
            tool_call_id = invalid_call.get("id", "")
            error_msg = invalid_call.get("error", "Unknown parsing error")

            # Create ToolMessage with the parsing error
            tool_message = ToolMessage(
                content=TOOL_CALL_ERROR_TEMPLATE.format(error=error_msg),
                tool_call_id=tool_call_id,
                status="error",
            )
            error_messages.append(tool_message)

        # Append error messages to state so LLM can see them
        if error_messages:
            return {"messages": error_messages}

        return None

    def wrap_tool_call(
        self,
        request: ToolCallRequest,
        handler: Callable[[ToolCallRequest], ToolMessage | Command[Any]],
    ) -> ToolMessage | Command[Any]:
        """Wrap tool call to catch ToolException and convert to ToolMessage."""
        try:
            return handler(request)
        except ToolException as e:
            return ToolMessage(
                content=TOOL_CALL_ERROR_TEMPLATE.format(error=repr(e)),
                tool_call_id=request.tool_call.get("id", ""),
                status="error",
            )

    async def awrap_tool_call(
        self,
        request: ToolCallRequest,
        handler: Callable[[ToolCallRequest], Awaitable[ToolMessage | Command[Any]]],
    ) -> ToolMessage | Command[Any]:
        """Async wrapper for tool call to catch ToolException and convert to ToolMessage."""
        try:
            return await handler(request)
        except ToolException as e:
            return ToolMessage(
                content=TOOL_CALL_ERROR_TEMPLATE.format(error=repr(e)),
                tool_call_id=request.tool_call.get("id", ""),
                status="error",
            )

# Usage
agent = create_agent(
    model=model,
    tools=tools,
    middleware=[ToolErrorHandlingMiddleware()],
)
```

### Limitations of Middleware Workaround

**Important**: Our middleware approach has limitations. While it successfully:
1. ✅ Converts `invalid_tool_calls` to `ToolMessage` objects
2. ✅ Appends error messages to the conversation state

The routing logic in `_make_model_to_tools_edge` still only checks `last_ai_message.tool_calls` and ignores the presence of error `ToolMessage` objects. This means:
- If the AIMessage has `tool_calls=[]` (parsing failed), routing goes to exit
- Even though ToolMessages with errors were added by middleware
- The agent may still stop depending on the routing conditions

A complete fix requires changes to both:
1. **Conversion**: `invalid_tool_calls` → `ToolMessage` (middleware can handle this)
2. **Routing**: Check for error ToolMessages, not just tool_calls (needs core fix)

### Questions:

Is this middleware approach the intended way to handle `invalid_tool_calls`, or should this be built into `create_agent` like it was in `AgentExecutor`?

If middleware is the intended approach:
1. Should there be a built-in middleware provided by LangChain for this common use case?
2. Should the routing logic be updated to account for error ToolMessages added by middleware?

## Additional Context

This issue is particularly problematic when LLMs generate:
- Source code with complex escape sequences
- Large JSON structures
- Content with nested quotes
- Multi-line strings with special formatting

In these cases, JSON parsing failures are relatively common, and having automatic retry capability is essential for production robustness.

### System Info

## Environment

- **langchain**: 1.0.0a14 ← **Bug is in this package**
- **langchain-core**: 1.0.0rc1
- **langchain-anthropic**: 1.0.0a4
- **langchain-openai**: 1.0.0a4
- **Python**: 3.12.11
- **OS**: macOS 24.6.0

## Affected Component

- **Package**: `langchain` (not `langchain-core`)
- **Module**: `langchain.agents`
- **File**: `langchain/agents/factory.py`
- **Function**: `create_agent()` and `_make_model_to_tools_edge()`

## Comments

**MannXo:**
I can work on this bug if no one minds?

**eyurtsev:**
Which model generated this result for you?

You can likely address this with an after model middleware for now

**cladden:**
This was gpt-oss-120b hosted on vllm. 

What would a work-around look like using after model middleware?

**eyurtsev:**
I'll need to reproduce to see where the error is raised. But you can use `model_wrap_call` or `tool_wrap_call` to try and fix the invalid json using an LLM. (which middleware to use depends on where/where the exception occurs)

**darklordzw:**
I'm having trouble working around this issue using the [Deep Agents](https://docs.langchain.com/oss/python/deepagents/overview) library. The LLM frequently has issues generating valid JSON for the "write_file" and "edit_file" tools, which results in those calls being added to the invalid_tool_calls array. Since the agents aren't handling invalid_tool_calls, processing the conversation stops with errors about missing ToolResult messages.

I've been able to add the ToolResult messages using an after model middleware that's similar to what @cladden posted, but it still stops processing and requires my users to prompt the LLM to continue.

@eyurtsev, you mention trying to fix the invalid JSON using an LLM in the middleware. Can you explain what that flow might look like? I've tried having the middleware jump to the model node, but possible I'm misunderstanding how that works.

UPDATE:
Turns out I had this working after all, I'd just gotten stuck in a loop because I neglected to clear invalid_tool_calls. Here's an example middleware that's working fine for me:
`
"""Middleware to patch invalid tool calls in the messages history."""

import json
from typing import Any
from langchain.agents.middleware import AgentMiddleware, AgentState, hook_config
from langchain_core.messages import RemoveMessage, ToolMessage
from langgraph.graph.message import REMOVE_ALL_MESSAGES
from langgraph.runtime import Runtime

class PatchInvalidToolCallsMiddleware(AgentMiddleware):
    """Middleware to patch dangling tool calls in the messages history."""

    @hook_config(can_jump_to=["model"])
    def after_agent(
        self, state: AgentState, runtime: Runtime[Any]
    ) -> dict[str, Any] | None:  # noqa: ARG002
        """After the agent runs, handle dangling tool calls from any AIMessage."""
        messages = state["messages"]
        if not messages or len(messages) == 0:
            return None

        patched_messages = []
        should_retry = False

        # Iterate over the messages and add any dangling tool calls
        for i, msg in enumerate(messages):
            patched_messages.append(msg)
            if msg.type == "ai" and msg.invalid_tool_calls:
                for tool_call in msg.invalid_tool_calls:
                    corresponding_tool_msg = next(
                        (
                            msg
                            for msg in messages[i:]
                            if msg.type == "tool"
                            and msg.tool_call_id == tool_call["id"]
                        ),
                        None,
                    )
                    if corresponding_tool_msg is None:
                        # We have an invalid tool call which needs a ToolMessage
                        tool_msg = (
                            f"Tool call {tool_call['name']} with id {tool_call['id']} was "
                            "invalid. Please try again with corrected parameters."
                        )
                        try:
                            args = json.loads(tool_call["args"])
                        except Exception as error:
                            tool_msg = (
                                f"Tool call {tool_call['name']} with id {tool_call['id']} failed "
                                f"because of invalid argument JSON: {error.msg}. Please try again and be sure to properly "
                                f"escape your arguments."
                            )
                        patched_messages.append(
                            ToolMessage(
                                content=tool_msg,
                                name=tool_call["name"],
                                tool_call_id=tool_call["id"],
                                status="error",
                            )
                        )
                    should_retry = True
                    msg.tool_calls.append(tool_call)
                msg.invalid_tool_calls = []

        if should_retry:
            return {
                "messages": [RemoveMessage(id=REMOVE_ALL_MESSAGES), *patched_messages],
                "jump_to": "model",
            }

        return {
            "messages": [RemoveMessage(id=REMOVE_ALL_MESSAGES), *patched_messages],
        }
`

**endlessc:**
> I'm having trouble working around this issue using the [Deep Agents](https://docs.langchain.com/oss/python/deepagents/overview) library. The LLM frequently has issues generating valid JSON for the "write_file" and "edit_file" tools, which results in those calls being added to the invalid_tool_calls array. Since the agents aren't handling invalid_tool_calls, processing the conversation stops with errors about missing ToolResult messages.
> 
> I've been able to add the ToolResult messages using an after model middleware that's similar to what [@cladden](https://github.com/cladden) posted, but it still stops processing and requires my users to prompt the LLM to continue.
> 
> [@eyurtsev](https://github.com/eyurtsev), you mention trying to fix the invalid JSON using an LLM in the middleware. Can you explain what that flow might look like? I've tried having the middleware jump to the model node, but possible I'm misunderstanding how that works.
> 
> UPDATE: Turns out I had this working after all, I'd just gotten stuck in a loop because I neglected to clear invalid_tool_calls. Here's an example middleware that's working fine for me: ` """Middleware to patch invalid tool calls in the messages history."""
> 
> import json from typing import Any from langchain.agents.middleware import AgentMiddleware, AgentState, hook_config from langchain_core.messages import RemoveMessage, ToolMessage from langgraph.graph.message import REMOVE_ALL_MESSAGES from langgraph.runtime import Runtime
> 
> class PatchInvalidToolCallsMiddleware(AgentMiddleware): """Middleware to patch dangling tool calls in the messages history."""
> 
> ```
> @hook_config(can_jump_to=["model"])
> def after_agent(
>     self, state: AgentState, runtime: Runtime[Any]
> ) -> dict[str, Any] | None:  # noqa: ARG002
>     """After the agent runs, handle dangling tool calls from any AIMessage."""
>     messages = state["messages"]
>     if not messages or len(messages) == 0:
>         return None
> 
>     patched_messages = []
>     should_retry = False
> 
>     # Iterate over the messages and add any dangling tool calls
>     for i, msg in enumerate(messages):
>         patched_messages.append(msg)
>         if msg.type == "ai" and msg.invalid_tool_calls:
>             for tool_call in msg.invalid_tool_calls:
>                 corresponding_tool_msg = next(
>                     (
>                         msg
>                         for msg in messages[i:]
>                         if msg.type == "tool"
>                         and msg.tool_call_id == tool_call["id"]
>                     ),
>                     None,
>                 )
>                 if corresponding_tool_msg is None:
>                     # We have an invalid tool call which needs a ToolMessage
>                     tool_msg = (
>                         f"Tool call {tool_call['name']} with id {tool_call['id']} was "
>                         "invalid. Please try again with corrected parameters."
>                     )
>                     try:
>                         args = json.loads(tool_call["args"])
>                     except Exception as error:
>                         tool_msg = (
>                             f"Tool call {tool_call['name']} with id {tool_call['id']} failed "
>                             f"because of invalid argument JSON: {error.msg}. Please try again and be sure to properly "
>                             f"escape your arguments."
>                         )
>                     patched_messages.append(
>                         ToolMessage(
>                             content=tool_msg,
>                             name=tool_call["name"],
>                             tool_call_id=tool_call["id"],
>                             status="error",
>                         )
>                     )
>                 should_retry = True
>                 msg.tool_calls.append(tool_call)
>             msg.invalid_tool_calls = []
> 
>     if should_retry:
>         return {
>             "messages": [RemoveMessage(id=REMOVE_ALL_MESSAGES), *patched_messages],
>             "jump_to": "model",
>         }
> 
>     return {
>         "messages": [RemoveMessage(id=REMOVE_ALL_MESSAGES), *patched_messages],
>     }
> ```
> 
> `

I have the same problem as well. Using your solution, I successfully resolved this issue. This solution can be used! Thank you very much.

**sailtonight:**
any update?

**sailtonight:**
invalid tool call should be handled by framework, not user.

**water-in-stone:**
Could we fix this issue with [json_repair](https://github.com/mangiucugna/json_repair) ? When parsing JSON fails, we could use `json_repair` to attempt parsing the JSON string again.  @cladden

**rayshen92:**
anyone fix this?
