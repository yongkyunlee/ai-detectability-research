# `trim_messages` and `ChatAnthropic` token counter with tools

**Issue #29637** | State: open | Created: 2025-02-06 | Updated: 2026-03-15
**Author:** ccurme
**Labels:** bug, investigate, integration, anthropic, internal

### Privileged issue

- [x] I am a LangChain maintainer, or was asked directly by a LangChain maintainer to create an issue here.

### Issue Content

`ChatAnthropic.get_num_tokens_from_messages` uses Anthropic's [token counting API](https://docs.anthropic.com/en/api/messages-count-tokens) and will error for invalid message sequences. These constraints are not respected inside `trim_messages`. See below for examples.

```python
from functools import partial

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langchain_core.messages.utils import trim_messages
from langchain_core.tools import tool

@tool
def get_weather(location: str):
    """Get the weather."""
    pass

tools = [get_weather]

llm = ChatAnthropic(model="claude-3-5-sonnet-latest").bind_tools(tools)

messages = [
    HumanMessage("hi"),
    AIMessage("hello"),
    HumanMessage("what's the weather in florida?"),
    AIMessage(
        [
            {"type": "text", "text": "let's check the weahter in florida"},
            {
                "type": "tool_use",
                "id": "abc123",
                "name": "get_weather",
                "input": {"location": "florida"},
            },
        ],
        tool_calls=[
            {
                "name": "get_weather",
                "args": {"location": "florida"},
                "id": "abc123",
                "type": "tool_call",
            },
        ],
    ),
    ToolMessage(
        "It's sunny.",
        name="get_weather",
        tool_call_id="abc123",
    ),
]
```

## Example 1
```python
trim_messages(
    messages,
    max_tokens=200,
    token_counter=llm,
)
```
Breaks when we attempt to count tokens in a reversed list of messages: https://github.com/langchain-ai/langchain/blob/db8201d4dafb533133cc51c87c7ef011e546e03f/libs/core/langchain_core/messages/utils.py#L1309-L1312
> BadRequestError: Error code: 400 - {'type': 'error', 'error': {'type': 'invalid_request_error', 'message': 'messages.0: `tool_result` block(s) provided when previous message does not contain any `tool_use` blocks'}}

## Example 2
```python
trim_messages(
    messages,
    max_tokens=200,
    token_counter=llm,
    strategy="first",
)
```
Breaks because `ChatAnthropic.get_num_tokens_from_messages` expects tools to be passed in as a kwarg:
https://github.com/langchain-ai/langchain/blob/db8201d4dafb533133cc51c87c7ef011e546e03f/libs/partners/anthropic/langchain_anthropic/chat_models.py#L1160-L1162
> BadRequestError: Error code: 400 - {'type': 'error', 'error': {'type': 'invalid_request_error', 'message': 'Requests which include `tool_use` or `tool_result` blocks must define tools.'}}

## Example 3
```python
trim_messages(
    messages,
    max_tokens=200,
    token_counter=partial(llm.get_num_tokens_from_messages, tools=tools),
    strategy="first",
)
```
Breaks because an invalid history is sent to the token counting API:
> BadRequestError: Error code: 400 - {'type': 'error', 'error': {'type': 'invalid_request_error', 'message': 'messages.3: Messages containing `tool_use` blocks must be followed by a user message with `tool_result` blocks'}}

## Comments

**jmbledsoe:**
It turns out that to resolve Example 2, Anthropic doesn't care if all the tools referenced in the messages are included, just that _at least one_ tool is included.

I originally encountered this issue (thanks @ccurme for writing it up so well 🏆) and I'm currently working around it by passing the following as the `token_counter` parameter to `trim_messages`:
```
def count_tokens(messages: list[BaseMessage]) -> int:
    # Create an Anthropic LLM (configure however your application normally does so)
    llm = ChatAnthropic(model="claude-3-5-sonnet-latest")

    # Reverse messages when counting tokens to work around the issue in Example 1
    messages = list(reversed(messages))

    # Include a dummy tool so that Anthropic doesn't complain about missing tools to work around the issue in Example 2
    tools = [StructuredTool.from_function(name='dummy', func=lambda: None)]

    # Use `get_num_tokens_from_messages` from the LLM to count tokens, which is what LangChain does natively
    try:
        # Use `get_num_tokens_from_messages` from the LLM to count tokens, which is what LangChain does natively
        return llm.get_num_tokens_from_messages(messages=messages, tools=tools)
    except anthropic.BadRequestError as bre:
        # If the reason for the error is mismatched tool messages, just return a large number to force trimming to work around the issue in Example 3
        error = '`tool_result` block(s) provided when previous message does not contain any `tool_use` blocks'
        try:
            if error in cast(dict, bre.body)['error']['message']:
                return sys.maxsize
        except (KeyError, TypeError):
            pass  # If the error doesn't have the format we expect, just raise it

        raise  # If the error isn't the one we're expecting, raise it
```

🤔 this code doesn't work around Example 3 yet, but when I encounter that I'll post an update.

**avshalom-dayan-glossai:**
this is what I'm using, not sure I fully understand the implications on the trim strategy though (because of the reversing).

```
from collections.abc import Callable

from langchain_core.messages.base import BaseMessage
from langchain_core.tools import BaseTool
from langchain_anthropic.chat_models import convert_to_anthropic_tool, _format_messages
from anthropic import Anthropic

def get_anthropic_token_counter(tools: list[BaseTool], model: str) -> Callable[[list[BaseMessage]], int]:
    """
    Create a token counter function for an Anthropic model with tools.

    Args:
        tools: A list of tools to be used by the model.
        model: The name of the model to use.

    Returns:
        A function that counts the number of tokens in a list of messages.
    """
    formatted_tools = [convert_to_anthropic_tool(tool) for tool in tools]
    client = Anthropic()

    def anthropic_token_counter(messages: list[BaseMessage]) -> int:
        """
        Count the number of tokens in a list of messages.

        The function first attempts to count tokens using the original message order.
        If a specific error regarding `tool_result` blocks occurs, it retries using
        the reversed order (except the system message).

        Args:
            messages: A list of messages (first message should be a system message).

        Returns:
            The total number of input tokens.

        Raises:
            ValueError: If token counting fails.
        """
        def count_tokens(msgs: list[BaseMessage]) -> int:
            system_message, formatted_messages = _format_messages(msgs)
            response = client.messages.count_tokens(
                model=model,
                system=system_message,
                tools=formatted_tools,
                messages=formatted_messages,
            )
            return response.input_tokens

        try:
            return count_tokens(messages)
        except Exception as error:
            error_message = str(error)
            specific_error = (
                "`tool_result` block(s) provided when previous message does not contain any `tool_use` blocks"
            )
            if specific_error in error_message:
                reversed_messages = [messages[0]] + messages[1:][::-1]
                try:
                    return count_tokens(reversed_messages)
                except Exception as reversed_error:
                    raise ValueError(
                        f"Failed to count tokens with reversed messages: {reversed_error}"
                    )
            else:
                raise ValueError(f"Failed to count tokens: {error}")

    return anthropic_token_counter

if __name__ == '__main__':
    # example use
    from langchain_core.messages import SystemMessage, AIMessage, HumanMessage, ToolMessage
    from langchain.tools import StructuredTool
    from pydantic.v1 import BaseModel, Field

    # init_anthropic_key()

    class DummyToolInput(BaseModel):
        dummy_input: str = Field(..., description="Dummy input")

    def dummy(dummy_input: str) -> str:
        """
        Dummy function for testing.
        """
        return "I am fine."

    tools = [StructuredTool.from_function(dummy, name="dummy_tool", args_schema=DummyToolInput)]
    counter_func = get_anthropic_token_counter(tools, "claude-3-5-sonnet-20241022")

    messages = [
        SystemMessage(content="some dummy content"),
        ToolMessage(content='dummy input', name='dummy_tool', id='a4ce8831-0996-4ba6-b806-abddf94946e3',
                    tool_call_id='toolu_01PGy9VSNTgDni135BPGUBBh'),
        AIMessage(
            content=[
                {'citations': None, 'text': 'lets do some dummy dummy.', 'type': 'text'},
                {'id': 'toolu_01PGy9VSNTgDni135BPGUBBh', 'input': {'dummy_input': 'dummy input'}, 'name': 'dummy_tool',
                 'type': 'tool_use'}
            ],
        ),
        HumanMessage(content='do some dummy dummy.', id='abf85260-e5b0-4659-a734-5555ef8bd31b'),
    ]

    token_count_orig_messages = counter_func(messages)
    token_count_rev_messages = counter_func([messages[0]] + messages[1:][::-1])
    assert token_count_orig_messages == token_count_rev_messages and token_count_orig_messages > 0
    print(f"Token count: {token_count_orig_messages}")

```

usage in `trim_messages`: 

```
messages: list[BaseMessage] = ...
tools: list[BaseTool] = ...
model = "claude-3-5-sonnet-20241022"
trimmed_messages = trim_messages(
                messages=messages,
                token_counter=get_anthropic_token_counter(tools, model),
                max_tokens=100_000,
)
```

**jmbledsoe:**
Our local workaround is still necessary on LangChain `0.3.25`, so the issue still seems relevant.

**wudstrand:**
@ccurme do you know the status of this bug? I am primarily running into issues with the example 3 situation. I have tried specifying the `end_on=("human", "tool")` parameter, but I havent had any success. This is causing issues with the summarization node in langmem as well.

**ccurme:**
Hi @wudstrand, as a workaround, I'm wondering if you are able to use the count_tokens_approximately(https://python.langchain.com/api_reference/core/messages/langchain_core.messages.utils.count_tokens_approximately.html) as the token counter? It should be default in langmem.

**wudstrand:**
@ccurme this will still be a problem is a select number of cases where the trim messages function removes a tool call response from the chat window which is not an accepted input to gemini and anthropic. This is an issue since I cannot control the end_on parameter in langmem.

**ccurme:**
Hi @wudstrand,

Are you using `count_tokens_approximately` (which I believe is the default in langmem) or ChatAnthropic as the token counter? If `count_tokens_approximately`, would you mind providing an example to help me reproduce the issue? Here is my attempt using the [settings used in langmem](https://github.com/langchain-ai/langmem/blob/41a6c3b39c94e47ebe8c20be6d4898a193c73e42/src/langmem/short_term/summarization.py#L236-L244). Output sequences appear to be valid here.
```python
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_core.messages.utils import count_tokens_approximately, trim_messages

messages = [
    SystemMessage("system"),
    HumanMessage("human_1"),
    AIMessage(
        "ai_1",
        tool_calls=[
            {
                "type": "tool_call",
                "name": "foo",
                "args": {},
                "id": "abc123",
            }
        ]
    ),
    ToolMessage("tool_1", tool_call_id="abc123"),
    AIMessage("ai_2"),
    HumanMessage("human_2"),
    AIMessage(
        "ai_3",
        tool_calls=[
            {
                "type": "tool_call",
                "name": "foo",
                "args": {},
                "id": "abc234",
            }
        ]
    ),
    ToolMessage("tool_2", tool_call_id="abc234"),
    AIMessage("ai_3"),
    HumanMessage("human_3"),
]
```
```python
trim_messages(
    messages,
    max_tokens=48,
    token_counter=count_tokens_approximately,
    start_on="human",
    strategy="last",
    allow_partial=True,
)

# [HumanMessage(content='human_3')]
```
```python
trim_messages(
    messages,
    max_tokens=49,
    token_counter=count_tokens_approximately,
    start_on="human",
    strategy="last",
    allow_partial=True,
)

# [HumanMessage(content='human_2'),
#  AIMessage(content='ai_3', tool_calls=[{'name': 'foo', 'args': {}, 'id': 'abc234', 'type': 'tool_call'}]),
#  ToolMessage(content='tool_2', tool_call_id='abc234'),
#  AIMessage(content='ai_4'),
#  HumanMessage(content='human_3')]
```

**jmbledsoe:**
> Are you using `count_tokens_approximately` (which I believe is the default in langmem) or `ChatAnthropic` as the token counter?

FWIW when I encountered this error, I was using `ChatAnthropic` for token counting. Approximate token counting doesn't have this error, but also doesn't count tokens accurately for images and files.

**shivamtiwari3:**
Hi @ccurme, I've submitted a fix for this issue in PR #35896. The PR addresses both the reversed-message ordering problem (Example 1) and the orphaned-ToolMessage edge case by wrapping the token counter inside `_last_max_tokens` with a `_suffix_token_counter` that re-reverses before counting and returns a sentinel for invalid suffixes.

Could you please assign me to this issue so the PR can be reopened? Happy to make any changes based on your feedback. Thanks!
