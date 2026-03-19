---
source_url: https://blog.langchain.com/langchain-langchain-1-0-alpha-releases/
author: "LangChain team"
platform: blog.langchain.com
scope_notes: "Trimmed from the LangChain & LangGraph 1.0 alpha release announcement. Focused on sections covering installation, getting started, and core architecture. Original post covers both LangGraph and LangChain 1.0; trimmed to LangChain-specific content about setup and first usage."
---

Today we are announcing alpha releases of v1.0 for langgraph and langchain, in both Python and JS. The official 1.0 release is targeted for late October.

### LangChain

LangChain enables developers to ship AI features fast with standardized model abstractions and prebuilt agent patterns. Over the past three years, the package has evolved significantly. Through all the changes, the core abstraction has consolidated around one thing: giving an LLM access to tools, calling the LLM, executing the tool calls the LLM makes, feeding the results back to it, and repeating until the LLM is done.

LangChain 1.0 introduces `create_agent` — a new, recommended agent implementation. This is built on top of LangGraph's runtime, and is in fact the same implementation that has been battle tested as `langgraph.prebuilts` over the past year.

To get started in Python:

```python
pip install langchain==1.0.0a3
```

To get started in JavaScript:

```bash
npm install langchain@next
```

Usage is straightforward:

```python
from langchain.agents import create_agent
```

```javascript
import { createAgent } from "langchain"
```

We will maintain a `langchain-legacy` package for backward compatibility with existing chains and agents. This will contain all the current chains and agents that exist today.

### LangChain Core

`langchain-core` is the base package that `langchain` is built on. It contains base abstractions for chat models, tools, retrievers, and more. This package is being promoted to 1.0 with no breaking changes.

The one significant addition is structured message content. While messages historically contained a simple `.content` string field, modern LLM APIs increasingly return content as a list of content blocks rather than a single string. We are adding a new `.content_blocks` property to messages that provides a structured, typed view of message content.

### Documentation

We also are releasing a brand new documentation site that consolidates open-source documentation for both LangChain and LangGraph into a single, unified, well-organized home for both Python and JS. We've heard your feedback about our docs. We hear you. We are confident this new site will be a massive step up.
