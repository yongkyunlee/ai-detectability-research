# (Anthropic) Natively Support "eager_input_streaming": true for Fine Grained Tool Streaming

**Issue #35767** | State: closed | Created: 2026-03-11 | Updated: 2026-03-13
**Author:** wyatt-contio-ai
**Labels:** core, langchain, feature request, anthropic, external

### Checked other resources

- [x] This is a feature request, not a bug report or usage question.
- [x] I added a clear and descriptive title that summarizes the feature request.
- [x] I used the GitHub search to find a similar feature request and didn't find it.
- [x] I checked the LangChain documentation and API reference to see if this feature already exists.
- [x] This is not related to the langchain-community package.

### Package (Required)

- [x] langchain
- [ ] langchain-openai
- [x] langchain-anthropic
- [ ] langchain-classic
- [x] langchain-core
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

There is no way to support fine grained tool streaming for Anthropic models natively without a monkey-patch in-code, which is fragile and doesn't work properly.

The native way to support fine grained tool streaming is documented at: https://platform.claude.com/docs/en/agents-and-tools/tool-use/fine-grained-tool-streaming

This is critical for tool calling performance speed.

### Use Case

I have a supervisor agent that does a large amount of tool calling. Before Sonnet 4.6, the beta header worked just fine. But now it's first class and required on every tool definition. This would solve the current inability to have fine grained tool streaming enabled for anthropic models for anyone using >= Sonnet/Opus 4.6.

### Proposed Solution

I think this could be implemented by somehow allowing an input parameter to `init_chat_model` where `model_provider` = "anthropic" | "anthropic_bedrock" to default turn on for every tool, similar to how the beta header used to work.

Could also simply allow provider kwargs to `@tool` decorator definitions to allow enablement per-tool.

### Alternatives Considered

_No response_

### Additional Context

I'm using `anthropic_bedrock` as `model_provider` in my current setup, but think this feature would apply to `anthropic` directly as well.
