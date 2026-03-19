# XAI: Make Responses endpoint default

**Issue #35897** | State: open | Created: 2026-03-14 | Updated: 2026-03-16
**Author:** jdcfd
**Labels:** feature request, xai, external

### Checked other resources

- [x] This is a feature request, not a bug report or usage question.
- [x] I added a clear and descriptive title that summarizes the feature request.
- [x] I used the GitHub search to find a similar feature request and didn't find it.
- [x] I checked the LangChain documentation and API reference to see if this feature already exists.
- [x] This is not related to the langchain-community package.

### Package (Required)

- [x] langchain-xai

### Feature Description

I would like to add support for using the Responses API for ChatXAI, instead of chat completions. This is the [recommended way of interacting with the models](https://docs.x.ai/developers/model-capabilities/text/generate-text). I believe this will be beneficial for agents using xAI models. 

### Use Case

I want to improve the performance of the Grok models in Deepagents CLI. My interest in these models is that Grok 4.20 is showing good performance, I would say up to par with Sonnet 4.5, but at a much lower price. However, most of the issues I encounter have to do with tool calling. However, there are some issues with tool calling. Porting to use the Responses API should be a first step for more robust performance of xAI models with Deepagents.

### Proposed Solution

I have already implemented a solution in a fork. https://github.com/jdcfd/langchain/tree/xai-responses 
It mimics the behavior of the ChatOpenAI by redefining this function:
```python
    def _use_responses_api(self, payload: dict) -> bool:
        """Determine whether to use the Responses API (the preferred API for xAI).

        xAI prefers Responses API for models starting with `grok-4` or `grok-code`.
        """
        if isinstance(self.use_responses_api, bool):
            return self.use_responses_api
        model_name = self.model_name or payload.get("model", "")
        if model_name and (model_name.startswith(("grok-4", "grok-code"))):
            return True
        return super()._use_responses_api(payload)
```
Most of the functionality is there from the parent class (`BaseChatOpenAI`), but the xai class needs to be updated to make sure it uses the responses api and to set the `metadata["model_provider"]="xai"` 

If the issue is assigned to me, I would submit a PR where people could let me know if there are missing pieces. 

### Alternatives Considered

_No response_

### Additional Context

_No response_

## Comments

**CYzhr:**
Hi! 👋 If you're tracking LLM costs or looking for optimization solutions, check out **AICostMonitor** (https://aicostmonitor.com). We help AI projects monitor and reduce API costs. Free consultation available!

**ccurme:**
Hello, does setting `use_responses_api=True` when instantiating ChatXAI work for you?

**jdcfd:**
Yes, that should work. After reviewing everything I think the only request is to make the Responses API the default. I changed the name of he issue to reflect that. Similar to what you do in `base.py` for openai. The proposed change is in the `chat_models.py` of xai :

```python
    def _use_responses_api(self, payload: dict) -> bool:
        """Determine whether to use the Responses API (the preferred API for xAI).

        xAI prefers Responses API for all purpose and intent.
        """
        if isinstance(self.use_responses_api, bool):
            return self.use_responses_api
        return True
```

Based on their documentation, **I don't see a case where Chat completions should be the default.** 

Optionally, I would propose creating a wrapper around `_convert_chunk_to_generation_chunk()`, `_create_chat_result()`, `_construct_lc_result_from_responses_api()` and `_convert_responses_chunk_to_generation_chunk()` to set `response_metadata["model_provider"]="xai"`. This is probably not necessary but nice to have (for consistency).

Again, my goal is to use this in the deepagents-cli, so I don't want to be messing with it to force it to use the responses API, it should be default. I am currently using it this way by pointing it to my local copy of the `langchain-xai` package.
