# Implementing the tool_select_tool tool

**Issue #34147** | State: closed | Created: 2025-11-30 | Updated: 2026-03-17
**Author:** arkonchen
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
- [ ] langchain-cli
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
- [ ] langchain-perplexity
- [ ] langchain-prompty
- [ ] langchain-qdrant
- [ ] langchain-xai
- [ ] Other / not sure / general

### Feature Description

Whether or not the tool selection tool will be realized.I think this is a very good tool, unlike LLMToolSelectorMiddleware.
And, could the type of request.tools be changed to dict to make it easier to find tools? Instead of looping through a list to find tools

### Use Case

https://platform.claude.com/docs/en/agents-and-tools/tool-use/tool-search-tool#when-to-use-tool-search

### Proposed Solution

_No response_

### Alternatives Considered

_No response_

### Additional Context

_No response_

## Comments

**towseef41:**
@arkonchen 

There’s already a tool picker (LLMToolSelectorMiddleware) that asks a model to choose the best tools before the main call, so the “select relevant tools” job is covered; if you just want quicker lookup by name we can add a small helper like request.tools_by_name while keeping the current list to avoid breaking anything, and a separate “tool search” tool only makes sense if you need something callable mid-run or a different selection strategy I am happy to add the helper or sketch that separate tool if you want.

**austinmw:**
@towseef41 Could we get an embedding based version instead of an LLM-based version too?

**arkonchen:**
@towseef41 I use middleware to implement, thanks reply

**sydney-runkle:**
Re an embedding based version, perhaps this could go in `langchain-community` as a community middleware :)

**dhanlon-intellica:**
@sydney-runkle @austinmw 

Question, this middleware appears to wrap model call. 

Wouldn't this nuke any prompt caching hits in place?

Do either of you have any suggestions how to keep context lean but also not wipe out prompt caching hits. Or personal opinions on balancing the two?
