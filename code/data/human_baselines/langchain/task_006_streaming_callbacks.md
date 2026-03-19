---
source_url: https://blog.langchain.com/callbacks/
author: "Nuno Campos"
platform: blog.langchain.com
scope_notes: "Trimmed from the 'Callbacks Improvements' blog post by Nuno Campos. Focuses on the callback system architecture, constructor vs request callbacks, the RunManager pattern, and design inspiration. Supplemented with context from the earlier 'Streaming Support in LangChain' post for streaming-specific details. Removed lengthy before/after code examples and deprecation notices to stay within 300-500 words."
---

We're announcing improvements to our callbacks system, which powers logging, tracing, streaming output, and some awesome third-party integrations. This update provides better support for concurrent runs with independent callbacks, tracing of deeply nested component trees, and request-scoped callback handlers useful for server deployments.

### Context

The callbacks mechanism was originally designed for non-async Python applications. With support for asyncio and JavaScript/TypeScript now available, we needed abstractions suitable for concurrent LangChain runs. Web developers also needed the ability to scope callbacks to individual requests.

### Constructor vs. Request Callbacks

The main improvement is a clear distinction between constructor callbacks and request callbacks. Constructor callbacks are defined when creating an object and apply to all runs of that object, scoped to that object only. Request callbacks are passed directly to `run()`, `call()`, or `apply()` methods and propagate through all sub-requests. This means passing handlers to an `AgentExecutor` via `run()` now applies to all nested objects — the LLM, tools, and any chains used internally. Previously this required tedious, ugly manual attachment of callback managers to every nested object.

### RunManager Pattern

Methods like `_call`, `_generate`, and `_run` now receive a `runManager` argument bound to that specific run. This manager contains logging methods like `handleLLMNewToken` and is useful for custom chain construction. For child runs, `runManager.getChild()` creates a properly scoped child manager, inspired by Python's logging module and the `getChild()` pattern.

### Streaming

Streaming helps reduce perceived latency by returning LLM output token by token, instead of all at once. The total time to completion doesn't change, but the user sees progress immediately. This is implemented through the `on_llm_new_token` callback, activated by setting `streaming=True` on the LLM. For web applications, the `StreamingLLMCallbackHandler` transmits tokens via WebSocket, while `QuestionGenCallbackHandler` sends intermediate messages during question-generation phases. The application leverages asyncio support to handle multiple concurrent client connections.

### Design Inspiration

We drew from Python's logging module — particularly the `getChild()` pattern — and web frameworks like Express for passing context-specific data. We considered async context variables but chose explicit function arguments for better debuggability and cross-platform compatibility between Python and JavaScript.

Tracing and other callbacks now just work with concurrency. Please let us know if you run into any issues, as this was a large change!
