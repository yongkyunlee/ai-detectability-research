# Add support for /responses websocket

**Issue #35415** | State: open | Created: 2026-02-24 | Updated: 2026-03-09
**Author:** RodriMora
**Labels:** langchain, feature request, openai, external

### Checked other resources

- [x] This is a feature request, not a bug report or usage question.
- [x] I added a clear and descriptive title that summarizes the feature request.
- [x] I used the GitHub search to find a similar feature request and didn't find it.
- [x] I checked the LangChain documentation and API reference to see if this feature already exists.
- [x] This is not related to the langchain-community package.

### Package (Required)

- [x] langchain
- [x] langchain-openai
- [ ] langchain-anthropic
- [ ] langchain-classic
- [ ] langchain-core
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
- [ ] langchain-openrouter
- [ ] langchain-perplexity
- [ ] langchain-qdrant
- [ ] langchain-xai
- [x] Other / not sure / general

### Feature Description

Openai released support for websockets for the /responses API, it's supposed to increase speed, specially in TTFT and tool calling:

Relevant resources:
https://github.com/openai/openai-python/releases/tag/v2.22.0
https://developers.openai.com/api/docs/guides/websocket-mode/

### Use Case

When using the OpenAI /responses API via the websockets instead of HTTPS

### Proposed Solution

Implement support for it. 

### Alternatives Considered

Not applicable

### Additional Context

I'm not sure just updating the dependency to would be enough, or if more work is required
   ` "openai>=2.22.0,<3.0.0",`
https://github.com/langchain-ai/langchain/blob/0b975d4d1ba532d4da16af222824951aeabba9d6/libs/partners/openai/pyproject.toml#L27

## Comments

**xXMrNidaXx:**
Great feature request! OpenAI's WebSocket mode for /responses is a significant improvement for latency-sensitive applications.

## What This Enables

Based on [OpenAI's docs](https://developers.openai.com/api/docs/guides/websocket-mode/):
- **TTFT improvement** — persistent WebSocket connection eliminates HTTP handshake per request
- **Faster tool call streaming** — tool use responses come through incrementally
- **Connection reuse** — especially valuable for high-frequency agentic workflows

## Implementation Considerations

A few things that might need attention beyond just bumping the dependency:

### 1. Connection Management
WebSockets require different lifecycle handling than HTTP:
```python
# HTTP: stateless, each request is independent
# WebSocket: persistent connection, needs:
#   - Connection pooling
#   - Reconnection logic
#   - Keepalive handling
```

### 2. Streaming Interface
Current `.astream()` returns `AsyncIterator[AIMessageChunk]`. WebSocket mode might benefit from an option to return richer stream events (like OpenAI's SDK now does):
```python
async for event in llm.astream_events(prompt, mode="websocket"):
    if event.type == "tool_call_start":
        # Handle incrementally
```

### 3. Fallback Behavior
Graceful fallback to HTTPS if WebSocket connection fails (firewalls, proxies that don't support upgrade).

### 4. Provider Abstraction
Would this be OpenAI-specific, or would there be a protocol-agnostic interface for providers that add WebSocket support? (Anthropic and others may follow.)

---

At [RevolutionAI](https://revolutionai.io), we've built real-time AI systems with WebSocket backends — happy to help test or contribute if there's a draft implementation. The latency gains are real, especially for tool-calling agents where you're round-tripping multiple times.

**ander-db:**
I'd like to work on this. The plan is to wire WebSocket streaming into the existing _stream_responses / _astream_responses pipeline using the websockets library for both sync and async paths, so token deltas and end-of-stream handling stay consistent with the HTTP path, backed by unit tests covering event parsing and finish conditions.
For the sync path, websockets can be used via websockets.sync.client.connect. For the async path, it provides a native async implementation with websockets.connect. This keeps the dependency surface to a single library (websockets) added as an optional dependency under the websocket extra.
Does this align with maintainer expectations?
