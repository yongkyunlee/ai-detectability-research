# In streaming mode, allow the agent to output content only in the final response

**Issue #34491** | State: open | Created: 2025-12-26 | Updated: 2026-03-05
**Author:** worldback
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

### Feature Description

In streaming mode, only the agent's final output should be retrieved, not any intermediate output, such as tool calls. Note that this is in streaming mode.

### Use Case

from langchain.agents import create_agent
from langchain_core.messages import HumanMessage, TextContentBlock
import os
from langchain.chat_models import init_chat_model
from langchain.tools import tool
model = init_chat_model(
    model="glm-4.6v",
    model_provider="openai",
    base_url="https://open.bigmodel.cn/api/paas/v4/",
    api_key=os.getenv("ZHIPUAI_API_KEY"),
)

@tool
def query_fabric(name: str) -> str:
    """get fabric info"""
    return f"{name} is good."

agent = create_agent(
    model=model,
    tools=[query_fabric],
)

messages = [HumanMessage(content_blocks=[TextContentBlock(text="How is the linen herringbone fabric?", type="text")])]
async for stream_mode, chunk in agent.astream(
        {"messages": messages},  stream_mode=["messages"]
):
    token, metadata = chunk
    if metadata.get("tool_calls"):
        continue
    if getattr(token, "tool_calls", []):
        continue
    if metadata['langgraph_node'] == "tools":
        continue
    if not token.content_blocks:
        continue
    if token.content_blocks[0]["type"] == "text":
        print(token.content_blocks[0]["text"], end="")

The above is the test code, and the output is as follows：

"""
I'll help you find information about linen herringbone fabric.

Based on the information available, linen herringbone fabric is considered good. Linen herringbone is typically known for its durability, breathability, and classic textured appearance. The herringbone pattern gives it a distinctive V-shaped weave that adds visual interest and texture to the fabric. Linen is a natural fiber that's highly absorbent and gets softer with wear, making it a popular choice for various applications including clothing, home textiles, and upholstery.
"""

Because some LLM have non-empty content when calling the tool, as shown below:

 AIMessage(content="\nI'll help you find information about the linen herringbone fabric.\n", additional_kwargs={}, response_metadata={'finish_reason': 'tool_calls', 'model_name': 'glm-4.6v', 'model_provider': 'openai'}, id='lc_run--019b5a5b-1d9d-7a20-962a-247b2901755b', tool_calls=[{'name': 'query_fabric', 'args': {'name': 'linen herringbone'}, 'id': 'call_3506c63fc43f4951854b454b', 'type': 'tool_call'}], usage_metadata={'input_tokens': 165, 'output_tokens': 94, 'total_tokens': 259, 'input_token_details': {'cache_read': 43}, 'output_token_details': {}})
 
This causes the output of what should be an intermediate process (\nI'll help you find information about the linen herringbone fabric.\n) to also be displayed in streaming mode.
However, I only want to stream the agent's final response, i.e., the following:

"""
Based on the information available, linen herringbone fabric is considered good. Linen herringbone is typically known for its durability, breathability, and classic textured appearance. The herringbone pattern gives it a distinctive V-shaped weave that adds visual interest and texture to the fabric. Linen is a natural fiber that's highly absorbent and gets softer with wear, making it a popular choice for various applications including clothing, home textiles, and upholstery.
"""

I have tried many methods, such as astream_events or middleware, but none of them can achieve this. Are there any other methods to do this, or can this be added as a new feature?

### Proposed Solution

_No response_

### Alternatives Considered

_No response_

### Additional Context

_No response_

## Comments

**keenborder786:**
If you only need the final output, you can just keep skipping the intermediate steps and display the final message ?

**worldback:**
> If you only need the final output, you can just keep skipping the intermediate steps and display the final message ?

In non-streaming mode, intermediate steps can be skipped, and the final information can be displayed directly. However, this seems impossible in streaming mode.
 This is because some llm also output a piece of text when making tool call requests, and in the above example, I am unable to filter it out.

**keenborder786:**
@worldback you can do something like this:

```python

from langchain.agents import create_agent
from langchain.tools import tool
from langchain.messages import AIMessage

@tool
def weather(location: str) -> str:
    """Get the weather in a location"""
    return f"The weather in {location} is sunny"
agent = create_agent(
    model="gpt-4o-mini",
    tools=[weather],
    system_prompt="You are a helpful assistant",
)
result = agent.stream({"messages": [{"role": "user", "content": "What's the weather in San Francisco?"}]})
for chunk in result:
    if "model" in chunk and isinstance(chunk["model"]['messages'][-1], AIMessage) and chunk["model"]['messages'][-1].content and not chunk["model"]['messages'][-1].tool_calls:
        print(chunk["model"])
```

**worldback:**
@keenborder786 It works, but it loses the real-time, token-by-token streaming effect.

**keenborder786:**
What do you mean by `token-by-token` streaming effect?

**LLLzxx:**
@keenborder786 
token-by-token maybe like this：Hi | I | 'm | …
`Hi` 、`I`、`’m` Both are tokens, separated by`|`

**keenborder786:**
Ahhh I see, @LLLzxx but why don't you just stream word by word using a command like `.split(" ")`.

Something like this:

```python
from langchain.agents import create_agent
from langchain.tools import tool
from langchain.messages import AIMessage

@tool
def weather(location: str) -> str:
    """Get the weather in a location"""
    return f"The weather in {location} is sunny"
agent = create_agent(
    model="gpt-4o-mini",
    tools=[weather],
    system_prompt="You are a helpful assistant",
)
result = agent.stream({"messages": [{"role": "user", "content": "What's the weather in San Francisco?"}]})
for chunk in result:
    if "model" in chunk and isinstance(chunk["model"]['messages'][-1], AIMessage) and chunk["model"]['messages'][-1].content and not chunk["model"]['messages'][-1].tool_calls:
        data = chunk["model"]["messages"][0].content.split(" ")
        for word in data:
            print(word)

```

**hai-x:**
@worldback  Hi, sorry to bother you. It seems like glm llm has this issue, do you find any workaround?

**hai-x:**
It seems that when the LLM returns `tool_calls` together with `text`, it splits the response into two parts.

For the LLM response example above: 
```
AIMessage(content="\nI'll help you find information about the linen herringbone fabric.\n", additional_kwargs={}, response_metadata={'finish_reason': 'tool_calls', 'model_name': 'glm-4.6v', 'model_provider': 'openai'}, id='lc_run--019b5a5b-1d9d-7a20-962a-247b2901755b', tool_calls=[{'name': 'query_fabric', 'args': {'name': 'linen herringbone'}, 'id': 'call_3506c63fc43f4951854b454b', 'type': 'tool_call'}], usage_metadata={'input_tokens': 165, 'output_tokens': 94, 'total_tokens': 259, 'input_token_details': {'cache_read': 43}, 'output_token_details': {}})
```
We end up receiving tokens twice: first `AIMessage(text="\nI'll help you find information about the linen herringbone fabric.\n")` with empty `tool_calls`, and then `AIMessage(tool_calls=["query_fabric"])` with empty text.

I’m not very familiar with `langchain/langgraph`, but perhaps we could merge these two parts and return a single message here.
