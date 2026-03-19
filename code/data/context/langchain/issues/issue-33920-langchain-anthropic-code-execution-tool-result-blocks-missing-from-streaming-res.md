# [langchain-anthropic] Code execution tool result blocks missing from streaming responses

**Issue #33920** | State: closed | Created: 2025-11-11 | Updated: 2026-03-18
**Author:** henryl
**Labels:** external

## Issue Description

Code execution tool result blocks (`bash_code_execution_tool_result`, `text_editor_code_execution_tool_result`) are present in non-streaming responses but are **missing from streaming responses** when using `langchain-anthropic` with Anthropic's code execution tools.

## Environment

- **Package**: `langchain-anthropic==1.0.2`
- **Dependencies**:
  - `anthropic==0.72.0`
  - `langchain-core==1.0.4`
- **Python**: 3.13
- **Model**: `claude-sonnet-4-20250514`
- **Beta**: `code-execution-2025-08-25`

## Expected Behavior

When streaming with `.astream()`, tool result content blocks should be included in the stream, similar to how tool use blocks are streamed. The Anthropic API returns these result blocks, and they should be exposed during streaming.

Expected result block types:
- `bash_code_execution_tool_result` - for bash command execution results
- `text_editor_code_execution_tool_result` - for file operation results
- `code_execution_tool_result` - for Python-only execution (legacy)

## Actual Behavior

**Non-streaming (`.invoke()`)**: ✅ Result blocks present
```python
Content blocks: 7
├─ Block 0: text
├─ Block 1: server_tool_use
├─ Block 2: text_editor_code_execution_tool_result ✅
├─ Block 3: text
├─ Block 4: server_tool_use
├─ Block 5: bash_code_execution_tool_result ✅
└─ Block 6: text
```

**Streaming (`.astream()`)**: ❌ Result blocks missing
```python
Tool use blocks found: 2 ✅
Result blocks found: 0 ❌
```

Only `server_tool_use` blocks are streamed. Result blocks are absent during streaming but appear in the final consolidated message.

## Reproduction Script

```python
#!/usr/bin/env python3
"""
Reproduction script for missing code execution tool result blocks during streaming.

Requirements:
    pip install langchain-anthropic python-dotenv

Environment:
    ANTHROPIC_API_KEY must be set
"""

import asyncio
import os

from dotenv import load_dotenv
from langchain_anthropic import ChatAnthropic

async def test_non_streaming():
    """Test non-streaming - result blocks SHOULD appear"""
    print("=" * 80)
    print("TEST 1: Non-Streaming (.invoke())")
    print("=" * 80)

    model = ChatAnthropic(
        model="claude-sonnet-4-20250514",
        betas=["code-execution-2025-08-25"],
    )

    tool = {"type": "code_execution_20250825", "name": "code_execution"}
    model_with_tools = model.bind_tools([tool])

    prompt = "Write a Python script that prints 'Hello, World!' and run it"

    response = model_with_tools.invoke(prompt)

    print(f"\nNumber of content blocks: {len(response.content)}\n")

    result_blocks_found = []
    for i, block in enumerate(response.content):
        if isinstance(block, dict):
            block_type = block.get("type", "")
            print(f"Block {i}: {block_type}")

            if "result" in block_type.lower():
                result_blocks_found.append(block_type)
                print(f"  ✅ RESULT BLOCK FOUND: {block_type}")
                print(f"     Keys: {list(block.keys())}")
                if "content" in block:
                    content = block["content"]
                    if isinstance(content, dict) and "stdout" in content:
                        print(f"     stdout: {content['stdout'][:100]}")

    print(f"\n{'✅' if result_blocks_found else '❌'} Result blocks in non-streaming: {len(result_blocks_found)}")
    return len(result_blocks_found)

async def test_streaming():
    """Test streaming - result blocks are MISSING (bug)"""
    print("\n" + "=" * 80)
    print("TEST 2: Streaming (.astream())")
    print("=" * 80)

    model = ChatAnthropic(
        model="claude-sonnet-4-20250514",
        betas=["code-execution-2025-08-25"],
    )

    tool = {"type": "code_execution_20250825", "name": "code_execution"}
    model_with_tools = model.bind_tools([tool])

    prompt = "Write a Python script that prints 'Hello, World!' and run it"

    chunk_count = 0
    tool_use_blocks = []
    result_blocks_found = []

    async for chunk in model_with_tools.astream(prompt):
        chunk_count += 1

        if hasattr(chunk, "content") and chunk.content:
            if isinstance(chunk.content, list):
                for content_block in chunk.content:
                    if isinstance(content_block, dict):
                        block_type = content_block.get("type", "")

                        if "tool_use" in block_type:
                            tool_use_blocks.append(block_type)
                            print(f"Chunk {chunk_count}: {block_type} (id: {content_block.get('id', 'N/A')})")

                        elif "result" in block_type.lower():
                            result_blocks_found.append(block_type)
                            print(f"Chunk {chunk_count}: ✅ {block_type}")

    print(f"\nTotal chunks processed: {chunk_count}")
    print(f"Tool use blocks found: {len(tool_use_blocks)}")
    print(f"{'❌' if len(result_blocks_found) == 0 else '✅'} Result blocks in streaming: {len(result_blocks_found)}")

    return len(result_blocks_found)

async def main():
    load_dotenv()

    if not os.getenv("ANTHROPIC_API_KEY"):
        print("ERROR: ANTHROPIC_API_KEY environment variable not set")
        return

    print("langchain-anthropic Tool Result Streaming Bug Reproduction")
    print("=" * 80)
    print("\nThis script demonstrates that code execution tool result blocks")
    print("appear in non-streaming responses but are missing during streaming.\n")

    non_streaming_results = await test_non_streaming()
    streaming_results = await test_streaming()

    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"Non-streaming result blocks: {non_streaming_results} ✅")
    print(f"Streaming result blocks:     {streaming_results} ❌")
    print("\n" + "=" * 80)

    if non_streaming_results > 0 and streaming_results == 0:
        print("❌ BUG CONFIRMED: Result blocks present in .invoke() but missing in .astream()")
        print("\nExpected behavior:")
        print("  - Tool result blocks should be streamed as content_block events")
        print("  - Result types: bash_code_execution_tool_result, text_editor_code_execution_tool_result")
        print("\nActual behavior:")
        print("  - Only tool_use blocks are streamed")
        print("  - Result blocks only appear in final consolidated response")
    else:
        print("✅ No bug detected - both methods return result blocks")

    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(main())
```

### Output

```
langchain-anthropic Tool Result Streaming Bug Reproduction
================================================================================

This script demonstrates that code execution tool result blocks
appear in non-streaming responses but are missing during streaming.

================================================================================
TEST 1: Non-Streaming (.invoke())
================================================================================

Number of content blocks: 7

Block 0: text
Block 1: server_tool_use
Block 2: text_editor_code_execution_tool_result
  ✅ RESULT BLOCK FOUND: text_editor_code_execution_tool_result
     Keys: ['content', 'tool_use_id', 'type']
Block 3: text
Block 4: server_tool_use
Block 5: bash_code_execution_tool_result
  ✅ RESULT BLOCK FOUND: bash_code_execution_tool_result
     Keys: ['content', 'tool_use_id', 'type']
     stdout: Hello, World!

Block 6: text

✅ Result blocks in non-streaming: 2

================================================================================
TEST 2: Streaming (.astream())
================================================================================
Chunk 6: server_tool_use (id: srvtoolu_019MC1Jpmrs9mXibApDAWPyv)
Chunk 25: server_tool_use (id: srvtoolu_016qccQowWZdBTGy8mU5TZrt)

Total chunks processed: 40
Tool use blocks found: 2
❌ Result blocks in streaming: 0

================================================================================
SUMMARY
================================================================================
Non-streaming result blocks: 2 ✅
Streaming result blocks:     0 ❌

================================================================================
❌ BUG CONFIRMED: Result blocks present in .invoke() but missing in .astream()

Expected behavior:
  - Tool result blocks should be streamed as content_block events
  - Result types: bash_code_execution_tool_result, text_editor_code_execution_tool_result

Actual behavior:
  - Only tool_use blocks are streamed
  - Result blocks only appear in final consolidated response
================================================================================
```

## Impact

This limitation prevents real-time UI updates for code execution results. Applications cannot show:
- "Running bash command..." → "Result: Hello, World!" progression
- Live stdout/stderr output during execution
- File creation confirmations as they happen

Users must wait for the entire response to complete before accessing tool results, defeating the purpose of streaming.

## Workaround

Currently, the only workaround is to:
1. Use the direct Anthropic SDK instead of LangChain, OR
2. Wait for the final consolidated message and extract results from there

## Related Documentation

- [Anthropic Code Execution Tool Docs](https://docs.claude.com/en/docs/agents-and-tools/tool-use/code-execution-tool)
- [LangChain Anthropic Integration](https://python.langchain.com/docs/integrations/providers/anthropic/)

## Request

Please add streaming support for server-side tool result blocks so they can be accessed in real-time during `.astream()` calls, matching the behavior of the native Anthropic SDK.

## Comments

**ccurme:**
Thanks for flagging this. We supported `code_execution_20250522` but not the newer `code_execution_20250825`. Just released support for the newer one in the latest `langchain-anthropic`. Please shout if you run into more issues!

**QuodEstDubitandum:**
## Environment

The same issue still exists in the JS SDK using:

- Node 22.20.0
- `langchain-anthropic: 1.3.3`
- `langchain-core: 1.1.8`
- Model: `claude-sonnet-4-6`
- Beta: `code-execution-2025-08-25`

## Temporary Fix

While the following code at least seems to fix the issue with the missing **bash_code_execution_tool_result** blocks and streaming seems to work on the surface, the message we are getting back still seems to indicate issues (even if code execution seems to work).

Inside `node_modules/@langchain/anthropic/dist/utils/message_output.js`:
```js
	} else if (data.type === "content_block_start" && [
		"tool_use",
		"document",
		"server_tool_use",
		"web_search_tool_result",
		// TEMPORARY FIX
		"bash_code_execution_tool_result"
	].includes(data.content_block.type)) {
```

Still faulty:
```js
"invalid_tool_calls": [{
    "name": "",
    "args": "{\"command\": \"python3 -c \\\"import math; print(math.factorial(6))\\\"\"}",
    "error": "Malformed args.",
    "type": "invalid_tool_call"
 } ],
```

It would be nice if someone could look over this issue in the JS SDK as well
