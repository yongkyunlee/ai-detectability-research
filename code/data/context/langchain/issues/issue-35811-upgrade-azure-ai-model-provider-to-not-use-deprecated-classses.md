# Upgrade `azure_ai` model provider to not use deprecated classses

**Issue #35811** | State: open | Created: 2026-03-13 | Updated: 2026-03-16
**Author:** santiagxf
**Labels:** langchain, feature request, langchain-classic, external

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
- [x] langchain-classic
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

The current implementation of the `azure_ai` provider in `langchain_classic` and `langchain` relies on recently deprecated classes and lacks consistent support across both chat and embeddings modules.

### Use Case

Remove reliance on deprecated Azure AI classes and provide a unified initialization experience for Azure AI across different LangChain versions.

### Proposed Solution

**Proposed Changes**
- Chat Models: Update the initialization logic to use `AzureAIOpenAIApiChatModel` for the `azure_ai` provider, replacing the deprecated `AzureAIChatCompletionsModel`.
- Embeddings: Implement missing support for the `azure_ai` provider in embeddings initialization by mapping it to the `AzureAIOpenAIApiEmbeddingsModel` class.
- Parity: Ensure these changes are reflected consistently in both `langchain_classic` and `langchain_v1` directories to prevent logic drift.

### Alternatives Considered

_No response_

### Additional Context

_No response_

## Comments

**ccurme:**
Can you link to documentation, code, etc. showing that these are deprecated? Thanks.

**santiagxf:**
Sure @ccurme. This is the official Microsoft Learn site: https://learn.microsoft.com/en-us/azure/foundry-classic/how-to/develop/langchain.

Classes in `langchain_azure_ai` have been decorated with `@deprecated`: https://github.com/langchain-ai/langchain-azure/blob/080fb3ebf0030419b21a59bb65fcdc7016a9d80a/libs/azure-ai/langchain_azure_ai/chat_models/inference.py#L312

The old classes require Azure AI Inference SDK which has been deprecated and will retire on May 30, 2026.

**santiagxf:**
@ccurme can you share any pointers about how we can move this forward?
