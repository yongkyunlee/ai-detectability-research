# Review, improvement, and migration of SemanticChunker to a non-experimental langchain pachage

**Issue #35553** | State: closed | Created: 2026-03-04 | Updated: 2026-03-08
**Author:** brocchirodrigo
**Labels:** text-splitters, feature request, external

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
- [x] langchain-text-splitters
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
- [ ] Other / not sure / general

### Feature Description

I believe it’s time we move the SemanticChunker from the experimental package into the core library. The main goal here is to provide a more sophisticated, meaning-driven standard for document splitting that finally moves beyond the limitations of simple character counts.

As it stands, the experimental implementation already does a fantastic job of using embedding similarity to find natural thematic breaks. This is absolutely critical for RAG systems, especially when we are parsing dense HTML pages or scientific articles where cutting a thought in half mid-sentence can completely ruin retrieval quality.

This isn't just a theoretical improvement; there is solid research backing this up, such as the paper "Knowledge-aware semantic chunking for enhancing retrieval-augmented generation" recently published on ScienceDirect (2025). Their findings confirm that using semantic-driven segments significantly boosts accuracy and context integrity compared to traditional recursive methods. By officializing this method and perhaps refining how it handles edge cases like merging very small residual chunks instead of just dropping them, we can offer a much more robust and **intelligent** tool for the entire community. It’s a powerful feature that deserves to be a first-class citizen in the LangChain ecosystem.

### Use Case

For applying chunks by context, before executing the embedding and preserving the semantic dialogue logic.

### Proposed Solution

The same as previously predicted:

https://github.com/langchain-ai/langchain-experimental/blob/a6c66481ee56b38166b3daeea7eb767eac92146b/libs/experimental/langchain_experimental/text_splitter.py#L99

It is appropriate to analyze areas for improvement.

### Alternatives Considered

_No response_

### Additional Context

_No response_

## Comments

**ccurme:**
Thanks for suggesting this. If you find it valuable, I'd suggest implementing it in a separate package and publishing that as described in our [contributing docs](https://docs.langchain.com/oss/python/contributing/integrations-langchain). This would let us avoid adding a new dependency into langchain-text-splitters and allow it to be versioned independently.
