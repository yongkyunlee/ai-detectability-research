# core, openai: asyncio.get_event_loop() deprecated in async contexts

**Issue #35726** | State: open | Created: 2026-03-10 | Updated: 2026-03-10
**Author:** alvinttang
**Labels:** external

**Description**

Several async functions use `asyncio.get_event_loop()` which has been deprecated since Python 3.10. Inside `async def`, `asyncio.get_running_loop()` is the correct replacement — it's guaranteed to work and won't trigger deprecation warnings.

**Affected files**
- `libs/core/langchain_core/callbacks/manager.py` — `_ahandle_event_for_handler()`
- `libs/core/langchain_core/runnables/graph_mermaid.py` — `_render_mermaid_using_pyppeteer()`
- `libs/partners/openai/langchain_openai/chat_models/_client_utils.py` — `async_api_key_wrapper()`

**Suggested fix**
Replace `asyncio.get_event_loop()` with `asyncio.get_running_loop()` in these async contexts. No behavior change when called from a running event loop.

## Comments

**JiwaniZakir:**
Mind assigning this to me? I think I know where the issue is.
