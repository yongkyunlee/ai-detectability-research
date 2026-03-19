# [BUG] AWS Bedrock ValidationException with multiple tool calls - toolResult blocks not grouped

**Issue #4749** | State: closed | Created: 2026-03-06 | Updated: 2026-03-10
**Author:** MatthiasHowellYopp
**Labels:** bug

### Description

When an AWS Bedrock model makes multiple tool calls in a single response, CrewAI sends each tool result as a separate user message. Bedrock's Converse API requires all tool results for a given assistant message to be grouped together in a single user message, causing a ValidationException.

The bug is in `lib/crewai/src/crewai/llms/providers/bedrock/completion.py` (~line 1800) where tool messages are converted one at a time without buffering consecutive tool results.

### Steps to Reproduce

1. Configure CrewAI to use an AWS Bedrock model
2. Create an agent with multiple tools:
```python
from crewai import Agent, Task, Crew
from crewai.tools import tool

@tool("add_tool")
def add_tool(a: int, b: int) -> int:
    """Add two numbers."""
    return a + b

@tool("multiply_tool")
def multiply_tool(a: int, b: int) -> int:
    """Multiply two numbers."""
    return a * b

agent = Agent(
    role="Calculator",
    goal="Perform calculations",
    backstory="Math expert",
    tools=[add_tool, multiply_tool],
    llm="bedrock/us.amazon.nova-pro-v1:0"
)

task = Task(
    description="Calculate 25 + 17 AND 10 * 5",
    expected_output="Both results",
    agent=agent
)

crew = Crew(agents=[agent], tasks=[task])
result = crew.kickoff()
```

3. The model attempts to call both tools simultaneously
4. Bedrock returns ValidationException
5. Agent fails or retries with single tool calls

### Expected behavior

When the model makes multiple tool calls in one response, all tool results should be sent back to Bedrock in a single user message with multiple `toolResult` content blocks.

**Expected message structure:**
```
Message 0: user (prompt)
Message 1: assistant (toolUse A, toolUse B)
Message 2: user (toolResult A, toolResult B)  ← Both in one message
```

### Screenshots/Code snippets

**Current broken behavior:**
```
Message 0: user (prompt)
Message 1: assistant (toolUse A, toolUse B)
Message 2: user (toolResult A)  ← Separate message
Message 3: user (toolResult B)  ← Separate message - causes error
```

**Bedrock error:**
```
ValidationException: Expected toolResult blocks at messages.2.content for the following Ids: tooluse_xxx, tooluse_yyy
```

**Current code** (`bedrock/completion.py` ~line 1800):
```python
elif role == "tool":
    # Each tool result creates a separate message
    converse_messages.append({
        "role": "user",
        "content": [{
            "toolResult": {
                "toolUseId": tool_call_id,
                "content": [{"text": str(content)}]
            }
        }]
    })
```

**Proposed fix:**
```python
# Buffer tool results and flush as single message
pending_tool_results: list[dict] = []

def flush_tool_results() -> None:
    if pending_tool_results:
        converse_messages.append({
            "role": "user",
            "content": pending_tool_results.copy()
        })
        pending_tool_results.clear()

# In message loop:
elif role == "tool":
    pending_tool_results.append({
        "toolResult": {
            "toolUseId": tool_call_id,
            "content": [{"text": str(content)}]
        }
    })
elif role == "assistant":
    flush_tool_results()  # Flush before assistant message
    # ... process assistant message

# Flush at end:
flush_tool_results()
```

### Operating System

Other (specify in additional context)

### Python Version

3.11

### crewAI Version

1.10.1 - commit 87759cd from main branch

### crewAI Tools Version

N/A

### Virtual Environment

Venv

### Evidence

**AWS Bedrock Documentation:**
- [Converse API Reference](https://awscli.amazonaws.com/v2/documentation/api/latest/reference/bedrock-runtime/converse.html) - Shows content is an array within a single message
- [ToolUseBlock API](https://docs.aws.amazon.com/bedrock/latest/APIReference/API_runtime_ToolUseBlock.html) - Documents the toolUse/toolResult structure

**Community Reports:**
- [Make.com Community](https://community.make.com/t/ai-agent-new-400-error-while-parallel-tool-calls/104324) - "Expected toolResult blocks" error with parallel tool calls
- [n8n Community](https://community.n8n.io/t/ai-agent-error-when-tool-used/122570) - "Each tool_use block must have a corresponding tool_result block in the next message"
- [Agno Framework Issue #6242](https://github.com/agno-agi/agno/issues/6242) - Same bug, fixed in PR #6635

**Test Results:**
- Single tool call: ✅ Works
- Multiple tool calls (parallel): ❌ ValidationException
- Affects all Bedrock models: Nova Pro, Nova Lite, Claude Opus 4.5, Claude Sonnet 3.5

**Error message from Bedrock:**
```
ValidationException: Expected toolResult blocks at messages.2.content for the following Ids: tooluse_DR_3f80OR0aRzl1SfLr3yw
```

### Possible Solution

Implement tool result buffering in `bedrock/completion.py`:

1. Create a buffer for consecutive tool result messages
2. When processing tool messages, add them to the buffer instead of immediately appending
3. Flush the buffer as a single user message when encountering a non-tool message or end of messages
4. This groups all tool results from parallel calls into one user message

See proposed fix in "Screenshots/Code snippets" section above.

### Additional context

OS: MacOS Tahoe 26.3.1

This bug only affects AWS Bedrock models. OpenAI and Ollama models work correctly because they don't have the same message structure requirements.

The bug prevents capable models (like Claude Opus 4.5) from using their parallel tool calling abilities, forcing them to make sequential tool calls which is slower and less efficient.

## Comments

**xXMrNidaXx:**
The Bedrock Converse API requirement to group consecutive tool results into a single user message is well-documented but easy to miss. The AWS docs state: 'If the previous response included one or more tool use blocks, the following message must include the same number of toolResult blocks.'

The fix needs to buffer consecutive tool result messages and flush them as a single grouped message when a non-tool message is encountered.

Here is the pattern for the fix in the message conversion layer:

```python
def group_tool_results_for_bedrock(messages):
    '''Group consecutive tool result messages into single Bedrock-compatible user messages.'''
    grouped = []
    tool_buffer = []
    
    for msg in messages:
        if msg.get('role') == 'tool':
            # Buffer tool results
            tool_buffer.append({
                'toolResult': {
                    'toolUseId': msg.get('tool_call_id'),
                    'content': [{'text': str(msg.get('content', ''))}]
                }
            })
        else:
            # Flush buffered tool results as a single user message
            if tool_buffer:
                grouped.append({'role': 'user', 'content': tool_buffer})
                tool_buffer = []
            grouped.append(msg)
    
    # Flush any remaining tool results
    if tool_buffer:
        grouped.append({'role': 'user', 'content': tool_buffer})
    
    return grouped
```

**Workaround until this is fixed:** Limit your agent to one tool per task, or set `max_iter=1` on agents that use Bedrock models with multiple tools. This prevents the multi-tool-call pattern that triggers the grouping requirement:

```python
agent = Agent(
    role='Calculator',
    goal='Perform one calculation at a time',
    backstory='Math expert',
    tools=[add_tool, multiply_tool],
    llm='bedrock/us.amazon.nova-pro-v1:0',
    max_iter=1  # workaround: force sequential single-tool calls
)
```

Alternatively, use sequential tasks instead of a single multi-tool task to avoid the model making simultaneous tool calls.
