---
source_url: https://blog.langchain.com/langchain-expression-language/
author: "Nuno Campos"
platform: blog.langchain.com
scope_notes: "Trimmed from the original 'LangChain Expression Language' announcement post. Focused on motivation, core syntax, interface methods (invoke/batch/stream/async), and benefits. Removed references to webinars, LangChain Teacher app, and hiring to stay within 300-500 words."
---

We're excited to announce a new syntax to create chains with composition. This comes along with a new interface that supports batch, async, and streaming out of the box. We're calling this syntax LangChain Expression Language (LCEL).

The idea of chaining has proven popular when building applications with language models. Chaining can mean making multiple LLM calls in a sequence to check previous outputs or break down larger tasks. It can mean combining data transformation with a call to an LLM — for example, formatting a prompt template with user input or using retrieval to look up additional information. And it can mean passing the output of an LLM call to a downstream application, such as generating Python code and running it, or generating SQL and executing it against a database.

LangChain was born from the idea of making these operations easy. We factored common patterns into pre-built chains: LLMChain, ConversationalRetrievalChain, SQLQueryChain. But these chains weren't really composable. Under the hood they involved a lot of custom code, which made it tough to enforce a common interface and ensure equal levels of batch, streaming, and async support.

Today we're announcing a new way of constructing chains — a declarative way to truly compose chains and get streaming, batch, and async support out of the box:

```python
from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate

model = ChatOpenAI()
prompt = ChatPromptTemplate.from_template("tell me a joke about {foo}")
chain = prompt | model

chain.invoke({"foo": "bears"})
```

This uses the pipe operator (`|`) for composition. We can also get batch, stream, and async support automatically:

**Batch** takes in a list of inputs, with internal optimizations for batching calls to LLM providers:

```python
chain.batch([{"foo": "bears"}, {"foo": "cats"}])
```

**Stream** returns an iterable for token-by-token consumption:

```python
for s in chain.stream({"foo": "bears"}):
    print(s.content, end="")
```

**Async** methods (`ainvoke`, `abatch`, `astream`) are exposed for all operations.

Since the chain is expressed in a declarative and composable nature, it is much more clear how to swap certain components out. It also brings prompts front and center — making it more clear how to modify those. The prompts in LangChain are just defaults, largely intended to be modified for your particular use case. Previously, the prompts were a bit hidden and hard to change. With LCEL, they are more prominent and easily swappable.

LCEL chains also integrate seamlessly with LangSmith. Previously, when creating a custom chain there was a good bit of work to make sure callbacks were passed through correctly for tracing. With LangChain Expression Language that happens automatically.
