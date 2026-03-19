# **Title:** feat(mistralai): implement retry logic for HTTP errors, add concurrency control, and update AGENTS.md and README.md with new partner integrations and usage examples

**Issue #35735** | State: closed | Created: 2026-03-11 | Updated: 2026-03-11
**Author:** JehoXYZ
**Labels:** feature request, mistralai, external

### Checked other resources

- [x] This is a feature request, not a bug report or usage question.
- [x] I added a clear and descriptive title that summarizes the feature request.
- [x] I used the GitHub search to find a similar feature request and didn't find it.
- [x] I checked the LangChain documentation and API reference to see if this feature already exists.
- [x] This is not related to the langchain-community package.

### Package (Required)

- [ ] langchain
- [ ] langchain-openai
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
- [x] langchain-mistralai
- [ ] langchain-nomic
- [ ] langchain-ollama
- [ ] langchain-openrouter
- [ ] langchain-perplexity
- [ ] langchain-qdrant
- [ ] langchain-xai
- [ ] Other / not sure / general

### Feature Description

I would like LangChain to support automatic retry logic for transient HTTP errors and concurrency control in the MistralAI integration.

This feature would allow users to handle unstable network conditions and rate-limited environments more gracefully by automatically retrying failed requests, while concurrency control prevents request flooding under high load. Additionally, AGENTS.md and README.md should be updated to document new MistralAI partner integrations and include practical usage examples to help users get started quickly.

### Use Case

relying on ChatMistralAI in production environments frequently encounter transient HTTP errors such as 429 rate limits and 5xx server errors that cause requests to fail permanently without any recovery mechanism. Additionally, applications sending high volumes of concurrent async requests have no built-in way to throttle simultaneous calls, leading to request flooding, API quota exhaustion, and degraded reliability.

### Proposed Solution

This has already been implemented in chat_models.py. The fix introduces _RetryableHTTPStatusError as a thin wrapper around httpx.HTTPStatusError so tenacity can match and retry on HTTP 429 and 5xx responses through _create_retry_decorator. Both _raise_retryable_status_error and _araise_retryable_status_error wrap retryable status codes before raising, while non-retryable errors surface immediately. Concurrency is enforced by an asyncio.Semaphore initialized in validate_environment and sized to max_concurrent_requests (default 64), acquired inside acompletion_with_retry before every async API call ensuring at most max_concurrent_requests requests are in-flight at any time. The implementation is scoped entirely to the mistralai package.

### Alternatives Considered

Yes, several alternatives were considered:

**For retry logic:**
- I considered using the official `mistralai` SDK's built-in retry mechanism, but it would have reduced my control over which specific HTTP status codes trigger retries, specifically the 429, 500, 502, 503, and 504 codes I needed to target in my `_raise_retryable_status_error` and `_araise_retryable_status_error` functions.
- I also thought about catching and retrying inside `_generate` and `_agenerate` directly, but this would have scattered retry logic across multiple methods rather than centralizing it in my `completion_with_retry` and `acompletion_with_retry` functions where it belongs.
- I considered using `urllib3`'s retry adapter but since my implementation is built entirely on `httpx`, it was not applicable.

**For concurrency control:**
- I considered delegating concurrency control entirely to the caller, but in my opinion this places an unreasonable burden on users and makes the integration unreliable out of the box.
- I looked at `asyncio.BoundedSemaphore` as an alternative to `asyncio.Semaphore`, but since I initialize the semaphore once inside `validate_environment` with a fixed `max_concurrent_requests` value defaulting to 64, there is no risk of over-releasing, making `BoundedSemaphore` unnecessary overhead.
- I considered using `asyncio.gather` with a bounded pool but it would have required significantly restructuring my existing call sites in `_astream` and `_agenerate`.

### Additional Context

**Pros:**

- My retry logic is centralized in `completion_with_retry` and `acompletion_with_retry`, making it easy to maintain and modify without touching individual call sites like `_generate`, `_agenerate`, or `_astream`.
- My use of `_RetryableHTTPStatusError` as a thin subclass gives tenacity a concrete type to match against, meaning I have precise control over which HTTP status codes (429, 500, 502, 503, 504) trigger retries and which surface immediately.
- My `asyncio.Semaphore` approach is lightweight and transparent, requiring no changes to existing call sites since it is initialized once in `validate_environment` and acquired inside `acompletion_with_retry`.
- Both sync and async paths are covered, meaning users get consistent retry behavior regardless of whether they use `invoke` or `ainvoke`.
- My default values of `max_retries=5` and `max_concurrent_requests=64` are fully configurable, giving users control without requiring them to understand the internals.

**Cons:**

- My semaphore is initialized in `validate_environment` which means it is tied to the model instance lifecycle, so users who recreate the model frequently may not get the concurrency behavior they expect.
- The sync path in `completion_with_retry` does not have concurrency control, only the async path does, which could be a limitation for users running sync workloads at high volume.
- My retry logic only covers `httpx.RequestError`, `httpx.StreamError`, and `_RetryableHTTPStatusError`, meaning other transient failures outside these types will not be retried automatically.
- Streaming responses in the async path acquire the semaphore but release it before the stream is fully consumed, which could allow more concurrent streams than intended.

## Comments

**JehoXYZ:**
Hi, I'd like to work on this issue. Could a any maintainer please assign it to me? I already have a fix ready in my PR. plssssssssssssssssss

**JehoXYZ:**
THank you
