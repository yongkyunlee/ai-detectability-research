# Add One-to-Many Batch Similarity Search Against Custom Entity Lists

**Issue #36090** | State: open | Created: 2026-03-18 | Updated: 2026-03-18
**Author:** felipheggaliza
**Labels:** langchain, feature request, external

### Checked other resources

- [x] This is a feature request, not a bug report or usage question.
- [x] I added a clear and descriptive title that summarizes the feature request.
- [x] I used the GitHub search to find a similar feature request and didn't find it.
- [x] I checked the LangChain documentation and API reference to see if this feature already exists.
- [x] This is not related to the langchain-community package.

### Package (Required)

- [x] langchain
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
- [ ] Other / not sure / general

### Feature Description

Currently, LangChain supports similarity search for a single query embedding against all vectors in a vector store (top-k search), and some vector stores support multi-query (many queries at once). However, there is no native, efficient API for the following use case:

Given one query embedding and a custom list of entity embeddings (not the entire database), efficiently compute the similarity between the query and each entity in the list, ideally in a single call.

### Use Case

- Usage of different embedding strategies in multi-step ranking. One embedding for retrieval and another for re-ranking
- Efficient enrichment of previously retrieved documents with similarity scores for re-ranking or hybrid retrieval workflows

Two-stage retrieval is a common pattern in Search, Recommender Systems and RAG applications.

![Image](https://github.com/user-attachments/assets/5c0d0073-929a-449f-984c-77f8a597da45)

### Proposed Solution

- Add a method to the VectorStore interface, e.g., batch_similarity(query_embedding, entity_ids) or similarity_to_entities(query_embedding, entity_embeddings)
- The method should efficiently compute similarity scores between the query and the provided list of entities, leveraging backend capabilities where possible (e.g., SQL IN clause, vector store filtering)
- Return a list of (entity_id, similarity_score) pairs, sorted by similarity

### Alternatives Considered

_No response_

### Additional Context

_No response_
