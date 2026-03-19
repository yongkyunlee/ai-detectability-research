# ChatAnthropic fails to handle empty HumanMessage content, leading to BadRequestError (400) from Anthropic API

**Issue #35081** | State: open | Created: 2026-02-09 | Updated: 2026-03-08
**Author:** graylin-byte
**Labels:** bug, anthropic, external

### Checked other resources

- [x] This is a bug, not a usage question.
- [x] I added a clear and descriptive title that summarizes this issue.
- [x] I used the GitHub search to find a similar question and didn't find it.
- [x] I am sure that this is a bug in LangChain rather than my code.
- [x] The bug is not resolved by updating to the latest stable version of LangChain (or the specific integration package).
- [x] This is not related to the langchain-community package.
- [x] I posted a self-contained, minimal, reproducible example. A maintainer can copy it and run it AS IS.

### Package (Required)

- [ ] langchain
- [ ] langchain-openai
- [x] langchain-anthropic
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
- [ ] langchain-perplexity
- [ ] langchain-qdrant
- [ ] langchain-xai
- [ ] Other / not sure / general

### Related Issues / PRs

_No response_

### Reproduction Steps / Example Code (Python)

```python
from langchain.chat_models import init_chat_model
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
import os

llm = init_chat_model(
    model="claude-haiku-3",
    api_key=os.getenv('ANTHROPIC_API_KEY'),
    max_retries=0,
    max_tokens=100
)

print(type(llm))

messages = [
    HumanMessage(content="", source="Alice"),
]

response = llm.invoke(messages)
print(response)
```

### Error Message and Stack Trace (if applicable)

```shell
---------------------------------------------------------------------------
BadRequestError                           Traceback (most recent call last)
Cell In[14], line 18
     12 print(type(llm))
     14 messages = [
     15     HumanMessage(content="", source="Alice"),
     16 ]
---> 18 response = llm.invoke(messages)
     19 print(response)

File /opt/homebrew/Caskroom/miniconda/base/envs/langchain/lib/python3.12/site-packages/langchain_core/language_models/chat_models.py:402, in BaseChatModel.invoke(self, input, config, stop, **kwargs)
    388 @override
    389 def invoke(
    390     self,
   (...)    395     **kwargs: Any,
    396 ) -> AIMessage:
    397     config = ensure_config(config)
    398     return cast(
    399         "AIMessage",
    400         cast(
    401             "ChatGeneration",
--> 402             self.generate_prompt(
    403                 [self._convert_input(input)],
    404                 stop=stop,
    405                 callbacks=config.get("callbacks"),
    406                 tags=config.get("tags"),
    407                 metadata=config.get("metadata"),
    408                 run_name=config.get("run_name"),
    409                 run_id=config.pop("run_id", None),
    410                 **kwargs,
    411             ).generations[0][0],
    412         ).message,
    413     )

File /opt/homebrew/Caskroom/miniconda/base/envs/langchain/lib/python3.12/site-packages/langchain_core/language_models/chat_models.py:1121, in BaseChatModel.generate_prompt(self, prompts, stop, callbacks, **kwargs)
   1112 @override
   1113 def generate_prompt(
   1114     self,
   (...)   1118     **kwargs: Any,
   1119 ) -> LLMResult:
   1120     prompt_messages = [p.to_messages() for p in prompts]
-> 1121     return self.generate(prompt_messages, stop=stop, callbacks=callbacks, **kwargs)

File /opt/homebrew/Caskroom/miniconda/base/envs/langchain/lib/python3.12/site-packages/langchain_core/language_models/chat_models.py:931, in BaseChatModel.generate(self, messages, stop, callbacks, tags, metadata, run_name, run_id, **kwargs)
    928 for i, m in enumerate(input_messages):
    929     try:
    930         results.append(
--> 931             self._generate_with_cache(
    932                 m,
    933                 stop=stop,
    934                 run_manager=run_managers[i] if run_managers else None,
    935                 **kwargs,
    936             )
    937         )
    938     except BaseException as e:
    939         if run_managers:

File /opt/homebrew/Caskroom/miniconda/base/envs/langchain/lib/python3.12/site-packages/langchain_core/language_models/chat_models.py:1233, in BaseChatModel._generate_with_cache(self, messages, stop, run_manager, **kwargs)
   1231     result = generate_from_stream(iter(chunks))
   1232 elif inspect.signature(self._generate).parameters.get("run_manager"):
-> 1233     result = self._generate(
   1234         messages, stop=stop, run_manager=run_manager, **kwargs
   1235     )
   1236 else:
   1237     result = self._generate(messages, stop=stop, **kwargs)

File /opt/homebrew/Caskroom/miniconda/base/envs/langchain/lib/python3.12/site-packages/langchain_anthropic/chat_models.py:1396, in ChatAnthropic._generate(self, messages, stop, run_manager, **kwargs)
   1394     data = self._create(payload)
   1395 except anthropic.BadRequestError as e:
-> 1396     _handle_anthropic_bad_request(e)
   1397 return self._format_output(data, **kwargs)

File /opt/homebrew/Caskroom/miniconda/base/envs/langchain/lib/python3.12/site-packages/langchain_anthropic/chat_models.py:1394, in ChatAnthropic._generate(self, messages, stop, run_manager, **kwargs)
   1392 payload = self._get_request_payload(messages, stop=stop, **kwargs)
   1393 try:
-> 1394     data = self._create(payload)
   1395 except anthropic.BadRequestError as e:
   1396     _handle_anthropic_bad_request(e)

File /opt/homebrew/Caskroom/miniconda/base/envs/langchain/lib/python3.12/site-packages/langchain_anthropic/chat_models.py:1250, in ChatAnthropic._create(self, payload)
   1248 if "betas" in payload:
   1249     return self._client.beta.messages.create(**payload)
-> 1250 return self._client.messages.create(**payload)

File /opt/homebrew/Caskroom/miniconda/base/envs/langchain/lib/python3.12/site-packages/anthropic/_utils/_utils.py:282, in required_args..inner..wrapper(*args, **kwargs)
    280             msg = f"Missing required argument: {quote(missing[0])}"
    281     raise TypeError(msg)
--> 282 return func(*args, **kwargs)

File /opt/homebrew/Caskroom/miniconda/base/envs/langchain/lib/python3.12/site-packages/anthropic/resources/messages/messages.py:950, in Messages.create(self, max_tokens, messages, model, metadata, output_config, service_tier, stop_sequences, stream, system, temperature, thinking, tool_choice, tools, top_k, top_p, extra_headers, extra_query, extra_body, timeout)
    943 if model in DEPRECATED_MODELS:
    944     warnings.warn(
    945         f"The model '{model}' is deprecated and will reach end-of-life on {DEPRECATED_MODELS[model]}.\nPlease migrate to a newer model. Visit https://docs.anthropic.com/en/docs/resources/model-deprecations for more information.",
    946         DeprecationWarning,
    947         stacklevel=3,
    948     )
--> 950 return self._post(
    951     "/v1/messages",
    952     body=maybe_transform(
    953         {
    954             "max_tokens": max_tokens,
    955             "messages": messages,
    956             "model": model,
    957             "metadata": metadata,
    958             "output_config": output_config,
    959             "service_tier": service_tier,
    960             "stop_sequences": stop_sequences,
    961             "stream": stream,
    962             "system": system,
    963             "temperature": temperature,
    964             "thinking": thinking,
    965             "tool_choice": tool_choice,
    966             "tools": tools,
    967             "top_k": top_k,
    968             "top_p": top_p,
    969         },
    970         message_create_params.MessageCreateParamsStreaming
    971         if stream
    972         else message_create_params.MessageCreateParamsNonStreaming,
    973     ),
    974     options=make_request_options(
    975         extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
    976     ),
    977     cast_to=Message,
    978     stream=stream or False,
    979     stream_cls=Stream[RawMessageStreamEvent],
    980 )

File /opt/homebrew/Caskroom/miniconda/base/envs/langchain/lib/python3.12/site-packages/anthropic/_base_client.py:1364, in SyncAPIClient.post(self, path, cast_to, body, content, options, files, stream, stream_cls)
   1355     warnings.warn(
   1356         "Passing raw bytes as `body` is deprecated and will be removed in a future version. "
   1357         "Please pass raw bytes via the `content` parameter instead.",
   1358         DeprecationWarning,
   1359         stacklevel=2,
   1360     )
   1361 opts = FinalRequestOptions.construct(
   1362     method="post", url=path, json_data=body, content=content, files=to_httpx_files(files), **options
   1363 )
-> 1364 return cast(ResponseT, self.request(cast_to, opts, stream=stream, stream_cls=stream_cls))

File /opt/homebrew/Caskroom/miniconda/base/envs/langchain/lib/python3.12/site-packages/anthropic/_base_client.py:1137, in SyncAPIClient.request(self, cast_to, options, stream, stream_cls)
   1134             err.response.read()
   1136         log.debug("Re-raising status error")
-> 1137         raise self._make_status_error_from_response(err.response) from None
   1139     break
   1141 assert response is not None, "could not resolve response (should never happen)"

BadRequestError: Error code: 400 - {'type': 'error', 'error': {'type': 'invalid_request_error', 'message': 'messages.0: all messages must have non-empty content except for the optional final assistant message'}, 'request_id': 'req_011CXwcCtGAdF1FBGvBeYtPy'}
```

### Description

When using ChatAnthropic (or init_chat_model with an Anthropic model), providing a HumanMessage with empty string content (content="") results in a BadRequestError from the Anthropic API.

Anthropic's API enforced a strict rule: "all messages must have non-empty content except for the optional final assistant message". Currently, langchain-anthropic passes the empty content directly to the API instead of providing a helpful validation error or handling it gracefully (e.g., stripping the message or raising a more descriptive ValueError).

This is particularly relevant for developers building agents where a tool or a previous step might accidentally produce an empty string.

### System Info

System Information
------------------
> OS:  Darwin
> OS Version:  Darwin Kernel Version 24.6.0: Mon Jul 14 11:29:54 PDT 2025; root:xnu-11417.140.69~1/RELEASE_ARM64_T8122
> Python Version:  3.12.12 | packaged by Anaconda, Inc. | (main, Oct 21 2025, 20:07:49) [Clang 20.1.8 ]

Package Information
-------------------
> langchain_core: 1.2.7
> langchain: 1.2.7
> langsmith: 0.6.8
> langchain_anthropic: 1.3.1
> langchain_chroma: 1.1.0
> langchain_deepseek: 1.0.1
> langchain_google_genai: 4.2.0
> langchain_mcp_adapters: 0.2.1
> langchain_openai: 1.1.7
> langgraph_sdk: 0.3.3

Optional packages not installed
-------------------------------
> langserve

Other Dependencies
------------------
> anthropic: 0.77.0
> chromadb: 1.4.1
> filetype: 1.2.0
> google-genai: 1.62.0
> httpx: 0.28.1
> jsonpatch: 1.33
> langgraph: 1.0.7
> mcp: 1.26.0
> numpy: 2.4.2
> openai: 2.16.0
> opentelemetry-api: 1.39.1
> opentelemetry-sdk: 1.39.1
> orjson: 3.11.6
> packaging: 25.0
> pydantic: 2.12.5
> pyyaml: 6.0.3
> requests: 2.32.5
> requests-toolbelt: 1.0.0
> rich: 14.3.2
> tenacity: 9.1.2
> tiktoken: 0.12.0
> typing-extensions: 4.15.0
> uuid-utils: 0.14.0
> xxhash: 3.6.0
> zstandard: 0.25.0

## Comments

**keenborder786:**
@graylin-byte We do not need to patch a fix for it, and/or it is not clear how this is a issue, as from the 400 error it is quite clear what the user is doing wrong.... And why would you pass in a empty message like what's the use case for that.

**Mary904:**
> [@graylin-byte](https://github.com/graylin-byte) We do not need to patch a fix for it, and/or it is not clear how this is a issue, as from the 400 error it is quite clear what the user is doing wrong.... And why would you pass in a empty message like what's the use case for that.

In some output-to-input pipelines, the output of one agent (which happens to be empty) becomes the user input for the next.

**ccurme:**
@Mary904 thanks for suggesting that use case. What do you propose ChatAnthropic should do in that case? If we skip those messages there will just be no input to the agent.

**Mary904:**
> [@Mary904](https://github.com/Mary904) thanks for suggesting that use case. What do you propose ChatAnthropic should do in that case? If we skip those messages there will just be no input to the agent.

Thanks for considering the use case! I actually found a similar bug and fix in the Microsoft AutoGen framework (https://github.com/microsoft/autogen/pull/6063). It faced the exact same issue with Anthropic and Gemini models, where empty strings caused a Bad Request error. Its developer took this as a "compatibility issue" and their solution was to explicitly replace falsy/empty content with a single whitespace (" ").

Following that same approach in ChatAnthropic would ensure consistency with other providers (like OpenAI) and prevent automated pipelines from hard-crashing when a message turn happens to be empty

**dalimao404:**
This is a valuable edge case to handle properly. In real-world agent systems, empty messages can occur naturally in several scenarios:

**Common scenarios where empty content appears:**

1. **Multi-turn conversations with metadata**: An agent might want to pass contextual information (like `source` in your example) without actual text content
2. **Tool-based workflows**: When an agent transitions between tool calls, intermediate messages might be empty placeholders
3. **Streaming contexts**: In streaming scenarios, message objects might be created before content is fully populated

**Suggested handling approach:**

Rather than letting this fail at the API level, ChatAnthropic could implement early validation:

- **Option 1 (Strict)**: Raise a clear `ValueError` with a helpful message like "HumanMessage content cannot be empty for Anthropic models"
- **Option 2 (Graceful)**: Filter out or skip empty messages with a warning, allowing the conversation to continue
- **Option 3 (Smart default)**: Replace empty content with a minimal placeholder like "[no content]" or allow configuration of default behavior

Option 1 seems most appropriate here since empty messages likely indicate a bug in the calling code rather than intentional behavior. The current 400 error from Anthropic is cryptic for users who don't immediately recognize the root cause.

Looking forward to seeing this resolved!

**keenborder786:**
@dalimao404 But don't you think the default error raised by Anthropic is clear enough for the user...

**ccurme:**
@Mary904 can you say more about the scenario where this comes up?

Anthropic appears unfazed by `""` content in tool responses. This is often how agent-to-agent communication is implemented. Here I adapt an [example from the docs](https://docs.langchain.com/oss/python/langchain/multi-agent/subagents):
```python
from langchain.agents import create_agent

def get_weather(location: str) -> str:
    """Get the weather at a location."""
    return ""

agent = create_agent("anthropic:claude-haiku-4-5", [get_weather])

input_query = {
    "role": "user",
    "content": "What's the weather in Boston?",
}

result = agent.invoke({"messages": [input_query]})

for message in result["messages"]:
    message.pretty_print()

# ================================ Human Message =================================

# Use the tool to research AI frameworks.
# ================================== Ai Message ==================================

# [{'text': "I'll research AI frameworks for you using the available tool.", 'type': 'text'}, {'id': 'toolu_01Fp7dycUJZBrWMHXaueu8zB', 'caller': {'type': 'direct'}, 'input': {'query': 'AI frameworks'}, 'name': 'research', 'type': 'tool_use'}]
# Tool Calls:
#   research (toolu_01Fp7dycUJZBrWMHXaueu8zB)
#  Call ID: toolu_01Fp7dycUJZBrWMHXaueu8zB
#   Args:
#     query: AI frameworks
# ================================= Tool Message =================================
# Name: research

# ================================== Ai Message ==================================

# The research tool ran successfully, though it didn't return visible output. This could mean the research is being processed or the results are being handled internally.

# Let me provide you with some key information about popular AI frameworks based on general knowledge...
```
Do you have a minimal reproducible example of the setup that would fail here?

**graylin-byte:**
@ccurme Thanks for the example! I see that Anthropic handles empty tool responses gracefully, but the failure I report specifically involves the HumanMessage (user role) having empty content. 

In Human-in-the-loop scenarios, it's easy for an empty string to slip through. Furthermore, in some multi-agent designs, developers treat the output of 'Agent A' as the 'User input' for 'Agent B' to maintain a clear dialogue history. If Agent A returns an empty string, the chain breaks.

I’d appreciate your thoughts on whether LangChain should handle accidental empty user inputs to prevent crashes, or leave it as is.

**jackjin1997:**
fixed here https://github.com/langchain-ai/langchain/pull/35412
