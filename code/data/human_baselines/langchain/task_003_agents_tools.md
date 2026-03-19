---
source_url: https://blog.langchain.com/structured-tools/
author: "LangChain team"
platform: blog.langchain.com
scope_notes: "Trimmed from the 'Structured Tools' blog post. Focused on the core structured tool abstraction, what defines a tool, and how to implement one. Removed lengthy code examples for advanced subclassing and FAQ section to stay within 300-500 words."
---

Way back in November 2022 when we first launched LangChain, agent and tool utilization played a central role in our design. We built one of the first chains based on ReAct, a groundbreaking paper that brought tool use to the forefront of prompting frameworks.

In the early days, tool use was simplistic. A model would generate two strings: a tool name and an input string for the chosen tool. This approach confined the agent to one tool per turn, and the input to that tool was restricted to a single string. These limitations were primarily due to the model's constraints; models struggled to perform even these basic tasks proficiently.

However, the rapid development of more advanced language models like `text-davinci-003`, `gpt-3.5-turbo`, and `gpt-4` has raised the floor of what available models can reliably achieve. Building on the success of our "multi-action" agent framework, we are now breaking free from the single-string input constraint and offering structured tool support.

## What is a "Structured Tool"?

A structured tool represents an action an agent can take. It wraps any function you provide to let an agent easily interface with it. A Structured Tool object is defined by its:

1. `name`: a label telling the agent which tool to pick. A tool called "GetCurrentWeather" is much more useful than "GCTW". If a tool's name isn't clear to you, it probably isn't clear to the agent either.
2. `description`: a short instruction manual that explains when and why the agent should use the tool.
3. `args_schema`: a Pydantic `BaseModel` that defines the arguments and their types. It communicates what information is required from the agent and validates those inputs before executing the tool.
4. `_run` and `_arun` functions: these define the tool's inner workings, from arithmetic to API requests to calls to other LLM Chains.

The fastest way to get started is by calling `StructuredTool.from_function(your_callable)`, which automatically infers the `args_schema` from the function's signature.

We also added a new `StructuredChatAgent` that works natively with these structured tools. To get started:

```python
from langchain.agents import initialize_agent, AgentType
tools = []  # Add any tools here
llm = ChatAnthropic(temperature=0)
agent_chain = initialize_agent(
    tools, llm,
    agent=AgentType.STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION
)
```

Older string-based tools remain forwards compatible. The original `Tool` class shares the same base class as the `StructuredTool`, so your existing tools should work out of the box.
