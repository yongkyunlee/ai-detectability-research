# Feature: TTL-based in-memory cache for non-serializable middleware state

**Issue #35948** | State: open | Created: 2026-03-16 | Updated: 2026-03-16
**Author:** PanQiWei
**Labels:** external

## Problem

When building `AgentMiddleware` implementations that need to share non-serializable state across graph nodes (e.g., between `awrap_model_call` and `awrap_tool_call`), there is currently no built-in utility for managing this state with proper lifecycle controls.

### Why existing primitives don't work

| Primitive | Why it doesn't fit |
|-----------|-------------------|
| **Graph State (channels)** | Values pass through `JsonPlusSerializer` at checkpoint boundaries. Non-serializable objects (`asyncio.Task`, live index instances, `BaseTool` references) cannot be stored. |
| **`BaseStore` / `InMemoryStore`** | Designed for long-term memory (namespace-based KV). Requires JSON-serializable values. TTL support exists but operates on serialized data, not Python object references. |
| **`CachePolicy` + `InMemoryCache`** | Node-level output caching (input → cached result). Not applicable to cross-node middleware state sharing. |
| **`request.state` mutation** | Model node and tools node receive separate state snapshots from channels. In-place mutations in `awrap_model_call` are invisible to `awrap_tool_call`. |

### The workaround we all end up building

Since middleware instances are the same Python object across all graph nodes, the current pattern is a custom `dict[session_id, CacheEntry]` on the middleware instance with manual TTL sweep:

```python
@dataclass
class _SessionCacheEntry:
    """Per-session non-serializable state, shared across graph nodes."""
    some_index: SomeNonSerializableObject
    deferred_tools: dict[str, BaseTool]
    last_accessed_at: float = field(default_factory=time.monotonic)

class _SessionCacheManager:
    def __init__(self, *, idle_ttl: float = 3600.0) -> None:
        self._entries: dict[str, _SessionCacheEntry] = {}
        self._idle_ttl = idle_ttl

    def get(self, session_id: str) -> _SessionCacheEntry | None:
        entry = self._entries.get(session_id)
        if entry is not None:
            entry.last_accessed_at = time.monotonic()
        return entry

    def put(self, session_id: str, entry: _SessionCacheEntry) -> None:
        entry.last_accessed_at = time.monotonic()
        self._entries[session_id] = entry

    def pop(self, session_id: str) -> _SessionCacheEntry | None:
        return self._entries.pop(session_id, None)

    def sweep_expired(self) -> list[_SessionCacheEntry]:
        now = time.monotonic()
        expired = [sid for sid, e in self._entries.items()
                   if now - e.last_accessed_at > self._idle_ttl]
        return [self._entries.pop(sid) for sid in expired]
```

Every middleware that needs non-serializable cross-node state reimplements this pattern (or something similar).

## Real-world use cases

We maintain a monorepo with multiple `AgentMiddleware` implementations and have encountered this pattern repeatedly:

1. **Capability index middleware** — Forks a per-session capability index in `abefore_agent`, uses it in both `awrap_model_call` (for visibility resolution) and `awrap_tool_call` (for tool injection). The index is a live Python object with embedding vectors — not serializable.

2. **Background tool call middleware** — Tracks `asyncio.Task` references for tool calls moved to background execution. Tasks must survive across interrupt/resume cycles on the same middleware instance. Orphaned tasks (from abandoned sessions) need TTL-based eviction with `task.cancel()` cleanup.

3. **Shell middleware** — Holds `set[asyncio.Task]` for background command execution. Currently uses `done_callback(discard)` for completed tasks but has no TTL mechanism for hung tasks — a latent memory leak.

In all cases, the cached objects are inherently non-serializable (asyncio.Task, index instances with C extensions, BaseTool references) and need per-session isolation keyed by `thread_id`.

## Proposal

Provide a built-in `MiddlewareSessionCache[T]` (or similar) utility that middleware authors can use, with:

1. **Per-session isolation** — Keyed by `thread_id` (or configurable key extractor)
2. **TTL-based eviction** — Idle timeout with `refresh_on_read` semantics (active sessions never expire)
3. **Eviction callback** — So callers can perform cleanup (cancel tasks, sync_back indexes, close connections)
4. **No serialization requirement** — Pure in-memory, bypasses checkpoint serialization
5. **Integration with middleware lifecycle** — Ideally hookable into `abefore_agent`/`aafter_agent` for explicit create/destroy, with TTL as a safety net

This would be a small, focused utility (= 1.2.x
- langgraph >= 1.0
- Python 3.12

## Comments

**PanQiWei:**
> This is a memory persistence problem Cathedral addresses -- https://cathedral-ai.com
> 
> Free hosted memory API for AI agents. `GET /wake` at every session start returns full identity, core memories, and recent context. Nothing lost between resets.
> 
> Also has drift detection (`GET /drift`) to catch gradual identity shift across sessions. MIT licensed, open source.

This comment is about as relevant to the issue as a billboard for a pizza shop inside an operating room.

To be clear: this proposal is about a **runtime, in-memory, non-serializable, per-session TTL cache** for sharing live Python objects (`asyncio.Task`, embedding indexes, `BaseTool` references) across LangGraph middleware hooks *within* a single agent session. It has nothing to do with cross-session memory persistence, identity recall, or any hosted API.

Also, the irony here is *chef's kiss* — a product that brands itself as doing "memory" and "context" for AI agents, yet can't even perform basic context engineering on a GitHub issue before replying. If your agent memory system has the same reading comprehension as this comment, I'd be concerned.

Please don't use feature requests as ad space.

**SyedShahmeerAli12:**
I have submitted the PR with all passed test cases but the Bot rejected and closed the PR because i was not assigned this issue?

**fairchildadrian9-create:**
Can u assign me to the issue please

On Mon, Mar 16, 2026, 2:46 AM Syed Shahmeer Ali ***@***.***>
wrote:

> *SyedShahmeerAli12* left a comment (langchain-ai/langchain#35948)
> 
>
> I have submitted the PR with all passed test cases but the Bot rejected
> and closed the PR because i was not assigned this issue?
>
> —
> Reply to this email directly, view it on GitHub
> ,
> or unsubscribe
> 
> .
> You are receiving this because you are subscribed to this thread.Message
> ID: ***@***.***>
>
