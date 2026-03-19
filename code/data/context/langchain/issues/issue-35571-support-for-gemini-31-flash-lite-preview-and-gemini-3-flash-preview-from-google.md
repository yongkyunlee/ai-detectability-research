# Support for gemini-3.1-flash-lite-preview and gemini-3-flash-preview from Google AI Studio

**Issue #35571** | State: open | Created: 2026-03-05 | Updated: 2026-03-09
**Author:** nguyenhongson1902
**Labels:** feature request, external

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
- [ ] langchain-mistralai
- [ ] langchain-nomic
- [ ] langchain-ollama
- [ ] langchain-openrouter
- [ ] langchain-perplexity
- [ ] langchain-qdrant
- [ ] langchain-xai
- [x] Other / not sure / general

### Feature Description

I tried reading images with `gemini-3.1-flash-lite-preview` and `gemini-3-flash-preview` using the API from Google AI Studio and observed that the output of `response.content` is actually a `list`, not a `str` like model `gemini-2.5-flash`

### Use Case

I'm trying to read images with gemini. If the output format of `response.content` is not a `str`, I think it's gonna affect the `llm.with_structured_output` too (even though I haven't tested it yet). Please support it.

### Proposed Solution

Currently I need to implement a helper function to parse the `response.content`. If it a `str`, then go to normal workflow. If it's a `list`, then go to get `text` field of the `dict` in the `list`.

### Alternatives Considered

_No response_

### Additional Context

The package that I was testing with is `langchain-google-genai==3.0.0`

## Comments

**RealRaghu09:**
I would like to work on this issue. Please assign this issue to me .

**KartikPawade:**
The root cause is a missing profile entry for `gemini-3.1-flash-lite-preview` 
in `_profiles.py`. This file lives in `langchain-ai/langchain-google`, not this repo.

Fix submitted here: https://github.com/langchain-ai/langchain-google/pull/1628

**nguyenhongson1902:**
> The root cause is a missing profile entry for `gemini-3.1-flash-lite-preview` in `_profiles.py`. This file lives in `langchain-ai/langchain-google`, not this repo.
> 
> Fix submitted here: [langchain-ai/langchain-google#1628](https://github.com/langchain-ai/langchain-google/pull/1628)

Just read your submitted fix there. Idk why but I tested those models, i.e. `gemini-3.1-flash-lite-preview` and `gemini-3-flash-preview` from VertexAI and it's working fine. Anw, I'm looking forward to the fix soon.
