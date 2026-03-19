# [BUG] AnthropicCompletion fails to handle empty user message content

**Issue #4427** | State: closed | Created: 2026-02-09 | Updated: 2026-03-17
**Author:** graylin-byte
**Labels:** bug, no-issue-activity

### Description

When using `AnthropicCompletion`, providing a user message with an empty string ("") as its content results in a BadRequestError returned by the Anthropic API. In some output-to-input pipelines, the output of one agent (which happens to be empty) becomes the user input for the next.

Anthropic enforces a strict validation rule: all messages must have non-empty content, except for an optional final assistant message. However, `AnthropicCompletion` currently forwards empty user message content to the API without validation or normalization, causing avoidable request failures.

### Steps to Reproduce

Execute the minimal reproduction code, then will see the error

### Expected behavior

The framework should gracefully handle empty content—via normalization or filtering—to avoid unnecessary API overhead and predictable 400 errors

### Screenshots/Code snippets

```py
from crewai import LLM  
import os

llm = LLM(  
    model="claude-3-haiku-20240307",  
    api_key=os.getenv('ANTHROPIC_API_KEY'),
    max_retries=0,
    max_tokens=100
)  

print(type(llm))
  
messages = [ 
    {"role": "user", "content": ""}
]  
  

result = llm.call(messages)  
print(result)
```

### Operating System

macOS Sonoma

### Python Version

3.12

### crewAI Version

1.9.2

### crewAI Tools Version

1.9.2

### Virtual Environment

Conda

### Evidence

output
```

ERROR:root:Anthropic API call failed: Error code: 400 - {'type': 'error', 'error': {'type': 'invalid_request_error', 'message': 'messages.0: all messages must have non-empty content except for the optional final assistant message'}, 'request_id': 'req_011CXy2Dhve1bt5pTfoXAsxN'}
```

Traceback

```sh
---------------------------------------------------------------------------
BadRequestError                           Traceback (most recent call last)
    [... skipping hidden 1 frame]

Cell In[13], [line 19](vscode-notebook-cell:?execution_count=13&line=19)
     14 messages = [ 
     15     {"role": "user", "content": ""}
     16 ]  
---> [19](vscode-notebook-cell:?execution_count=13&line=19) result = llm.call(messages)  
     20 print(result)

File /opt/homebrew/Caskroom/miniconda/base/envs/crewai/lib/python3.12/site-packages/crewai/llms/providers/anthropic/completion.py:305, in AnthropicCompletion.call(self, messages, tools, callbacks, available_functions, from_task, from_agent, response_model)
    297         return self._handle_streaming_completion(
    298             completion_params,
    299             available_functions,
   (...)    302             effective_response_model,
    303         )
--> [305](https://file+.vscode-resource.vscode-cdn.net/opt/homebrew/Caskroom/miniconda/base/envs/crewai/lib/python3.12/site-packages/crewai/llms/providers/anthropic/completion.py:305)     return self._handle_completion(
    306         completion_params,
    307         available_functions,
    308         from_task,
    309         from_agent,
    310         effective_response_model,
    311     )
    313 except Exception as e:

File /opt/homebrew/Caskroom/miniconda/base/envs/crewai/lib/python3.12/site-packages/crewai/llms/providers/anthropic/completion.py:673, in AnthropicCompletion._handle_completion(self, params, available_functions, from_task, from_agent, response_model)
    672         raise LLMContextLengthExceededError(str(e)) from e
--> [673](https://file+.vscode-resource.vscode-cdn.net/opt/homebrew/Caskroom/miniconda/base/envs/crewai/lib/python3.12/site-packages/crewai/llms/providers/anthropic/completion.py:673)     raise e from e
    675 usage = self._extract_anthropic_token_usage(response)

File /opt/homebrew/Caskroom/miniconda/base/envs/crewai/lib/python3.12/site-packages/crewai/llms/providers/anthropic/completion.py:667, in AnthropicCompletion._handle_completion(self, params, available_functions, from_task, from_agent, response_model)
    666     else:
--> [667](https://file+.vscode-resource.vscode-cdn.net/opt/homebrew/Caskroom/miniconda/base/envs/crewai/lib/python3.12/site-packages/crewai/llms/providers/anthropic/completion.py:667)         response = self.client.messages.create(**params)
    669 except Exception as e:

File /opt/homebrew/Caskroom/miniconda/base/envs/crewai/lib/python3.12/site-packages/anthropic/_utils/_utils.py:282, in required_args..inner..wrapper(*args, **kwargs)
    281     raise TypeError(msg)
--> [282](https://file+.vscode-resource.vscode-cdn.net/opt/homebrew/Caskroom/miniconda/base/envs/crewai/lib/python3.12/site-packages/anthropic/_utils/_utils.py:282) return func(*args, **kwargs)

File /opt/homebrew/Caskroom/miniconda/base/envs/crewai/lib/python3.12/site-packages/anthropic/resources/messages/messages.py:930, in Messages.create(self, max_tokens, messages, model, metadata, service_tier, stop_sequences, stream, system, temperature, thinking, tool_choice, tools, top_k, top_p, extra_headers, extra_query, extra_body, timeout)
    924     warnings.warn(
    925         f"The model '{model}' is deprecated and will reach end-of-life on {DEPRECATED_MODELS[model]}.\nPlease migrate to a newer model. Visit https://docs.anthropic.com/en/docs/resources/model-deprecations for more information.",
    926         DeprecationWarning,
    927         stacklevel=3,
    928     )
--> [930](https://file+.vscode-resource.vscode-cdn.net/opt/homebrew/Caskroom/miniconda/base/envs/crewai/lib/python3.12/site-packages/anthropic/resources/messages/messages.py:930) return self._post(
    931     "/v1/messages",
    932     body=maybe_transform(
    933         {
    934             "max_tokens": max_tokens,
    935             "messages": messages,
    936             "model": model,
    937             "metadata": metadata,
    938             "service_tier": service_tier,
    939             "stop_sequences": stop_sequences,
    940             "stream": stream,
    941             "system": system,
    942             "temperature": temperature,
    943             "thinking": thinking,
    944             "tool_choice": tool_choice,
    945             "tools": tools,
    946             "top_k": top_k,
    947             "top_p": top_p,
    948         },
    949         message_create_params.MessageCreateParamsStreaming
    950         if stream
    951         else message_create_params.MessageCreateParamsNonStreaming,
    952     ),
    953     options=make_request_options(
    954         extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
    955     ),
    956     cast_to=Message,
    957     stream=stream or False,
    958     stream_cls=Stream[RawMessageStreamEvent],
    959 )

File /opt/homebrew/Caskroom/miniconda/base/envs/crewai/lib/python3.12/site-packages/anthropic/_base_client.py:[1326](https://file+.vscode-resource.vscode-cdn.net/opt/homebrew/Caskroom/miniconda/base/envs/crewai/lib/python3.12/site-packages/anthropic/_base_client.py:1326), in SyncAPIClient.post(self, path, cast_to, body, options, files, stream, stream_cls)
   1323 opts = FinalRequestOptions.construct(
   1324     method="post", url=path, json_data=body, files=to_httpx_files(files), **options
   1325 )
-> 1326 return cast(ResponseT, self.request(cast_to, opts, stream=stream, stream_cls=stream_cls))

File /opt/homebrew/Caskroom/miniconda/base/envs/crewai/lib/python3.12/site-packages/anthropic/_base_client.py:[1114](https://file+.vscode-resource.vscode-cdn.net/opt/homebrew/Caskroom/miniconda/base/envs/crewai/lib/python3.12/site-packages/anthropic/_base_client.py:1114), in SyncAPIClient.request(self, cast_to, options, stream, stream_cls)
   1113     log.debug("Re-raising status error")
-> 1114     raise self._make_status_error_from_response(err.response) from None
   1116 break

BadRequestError: Error code: 400 - {'type': 'error', 'error': {'type': 'invalid_request_error', 'message': 'messages.0: all messages must have non-empty content except for the optional final assistant message'}, 'request_id': 'req_011CXy2Dhve1bt5pTfoXAsxN'}

The above exception was the direct cause of the following exception:

BadRequestError                           Traceback (most recent call last)
    [... skipping hidden 1 frame]

Cell In[13], [line 19](vscode-notebook-cell:?execution_count=13&line=19)
     14 messages = [ 
     15     {"role": "user", "content": ""}
     16 ]  
---> [19](vscode-notebook-cell:?execution_count=13&line=19) result = llm.call(messages)  
     20 print(result)

File /opt/homebrew/Caskroom/miniconda/base/envs/crewai/lib/python3.12/site-packages/crewai/llms/providers/anthropic/completion.py:305, in AnthropicCompletion.call(self, messages, tools, callbacks, available_functions, from_task, from_agent, response_model)
    297         return self._handle_streaming_completion(
    298             completion_params,
    299             available_functions,
   (...)    302             effective_response_model,
    303         )
--> [305](https://file+.vscode-resource.vscode-cdn.net/opt/homebrew/Caskroom/miniconda/base/envs/crewai/lib/python3.12/site-packages/crewai/llms/providers/anthropic/completion.py:305)     return self._handle_completion(
    306         completion_params,
    307         available_functions,
    308         from_task,
    309         from_agent,
    310         effective_response_model,
    311     )
    313 except Exception as e:

File /opt/homebrew/Caskroom/miniconda/base/envs/crewai/lib/python3.12/site-packages/crewai/llms/providers/anthropic/completion.py:673, in AnthropicCompletion._handle_completion(self, params, available_functions, from_task, from_agent, response_model)
    672         raise LLMContextLengthExceededError(str(e)) from e
--> [673](https://file+.vscode-resource.vscode-cdn.net/opt/homebrew/Caskroom/miniconda/base/envs/crewai/lib/python3.12/site-packages/crewai/llms/providers/anthropic/completion.py:673)     raise e from e
    675 usage = self._extract_anthropic_token_usage(response)

File /opt/homebrew/Caskroom/miniconda/base/envs/crewai/lib/python3.12/site-packages/crewai/llms/providers/anthropic/completion.py:667, in AnthropicCompletion._handle_completion(self, params, available_functions, from_task, from_agent, response_model)
    666     else:
--> [667](https://file+.vscode-resource.vscode-cdn.net/opt/homebrew/Caskroom/miniconda/base/envs/crewai/lib/python3.12/site-packages/crewai/llms/providers/anthropic/completion.py:667)         response = self.client.messages.create(**params)
    669 except Exception as e:

File /opt/homebrew/Caskroom/miniconda/base/envs/crewai/lib/python3.12/site-packages/anthropic/_utils/_utils.py:282, in required_args..inner..wrapper(*args, **kwargs)
    281     raise TypeError(msg)
--> [282](https://file+.vscode-resource.vscode-cdn.net/opt/homebrew/Caskroom/miniconda/base/envs/crewai/lib/python3.12/site-packages/anthropic/_utils/_utils.py:282) return func(*args, **kwargs)

File /opt/homebrew/Caskroom/miniconda/base/envs/crewai/lib/python3.12/site-packages/anthropic/resources/messages/messages.py:930, in Messages.create(self, max_tokens, messages, model, metadata, service_tier, stop_sequences, stream, system, temperature, thinking, tool_choice, tools, top_k, top_p, extra_headers, extra_query, extra_body, timeout)
    924     warnings.warn(
    925         f"The model '{model}' is deprecated and will reach end-of-life on {DEPRECATED_MODELS[model]}.\nPlease migrate to a newer model. Visit https://docs.anthropic.com/en/docs/resources/model-deprecations for more information.",
    926         DeprecationWarning,
    927         stacklevel=3,
    928     )
--> [930](https://file+.vscode-resource.vscode-cdn.net/opt/homebrew/Caskroom/miniconda/base/envs/crewai/lib/python3.12/site-packages/anthropic/resources/messages/messages.py:930) return self._post(
    931     "/v1/messages",
    932     body=maybe_transform(
    933         {
    934             "max_tokens": max_tokens,
    935             "messages": messages,
    936             "model": model,
    937             "metadata": metadata,
    938             "service_tier": service_tier,
    939             "stop_sequences": stop_sequences,
    940             "stream": stream,
    941             "system": system,
    942             "temperature": temperature,
    943             "thinking": thinking,
    944             "tool_choice": tool_choice,
    945             "tools": tools,
    946             "top_k": top_k,
    947             "top_p": top_p,
    948         },
    949         message_create_params.MessageCreateParamsStreaming
    950         if stream
    951         else message_create_params.MessageCreateParamsNonStreaming,
    952     ),
    953     options=make_request_options(
    954         extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
    955     ),
    956     cast_to=Message,
    957     stream=stream or False,
    958     stream_cls=Stream[RawMessageStreamEvent],
    959 )

File /opt/homebrew/Caskroom/miniconda/base/envs/crewai/lib/python3.12/site-packages/anthropic/_base_client.py:[1326](https://file+.vscode-resource.vscode-cdn.net/opt/homebrew/Caskroom/miniconda/base/envs/crewai/lib/python3.12/site-packages/anthropic/_base_client.py:1326), in SyncAPIClient.post(self, path, cast_to, body, options, files, stream, stream_cls)
   1323 opts = FinalRequestOptions.construct(
   1324     method="post", url=path, json_data=body, files=to_httpx_files(files), **options
   1325 )
-> 1326 return cast(ResponseT, self.request(cast_to, opts, stream=stream, stream_cls=stream_cls))

File /opt/homebrew/Caskroom/miniconda/base/envs/crewai/lib/python3.12/site-packages/anthropic/_base_client.py:[1114](https://file+.vscode-resource.vscode-cdn.net/opt/homebrew/Caskroom/miniconda/base/envs/crewai/lib/python3.12/site-packages/anthropic/_base_client.py:1114), in SyncAPIClient.request(self, cast_to, options, stream, stream_cls)
   1113     log.debug("Re-raising status error")
-> 1114     raise self._make_status_error_from_response(err.response) from None
   1116 break

BadRequestError: Error code: 400 - {'type': 'error', 'error': {'type': 'invalid_request_error', 'message': 'messages.0: all messages must have non-empty content except for the optional final assistant message'}, 'request_id': 'req_011CXy2Dhve1bt5pTfoXAsxN'}

The above exception was the direct cause of the following exception:

BadRequestError                           Traceback (most recent call last)
Cell In[13], [line 19](vscode-notebook-cell:?execution_count=13&line=19)
     12 print(type(llm))
     14 messages = [ 
     15     {"role": "user", "content": ""}
     16 ]  
---> [19](vscode-notebook-cell:?execution_count=13&line=19) result = llm.call(messages)  
     20 print(result)

File /opt/homebrew/Caskroom/miniconda/base/envs/crewai/lib/python3.12/site-packages/crewai/llms/providers/anthropic/completion.py:305, in AnthropicCompletion.call(self, messages, tools, callbacks, available_functions, from_task, from_agent, response_model)
    296     if self.stream:
    297         return self._handle_streaming_completion(
    298             completion_params,
    299             available_functions,
   (...)    302             effective_response_model,
    303         )
--> [305](https://file+.vscode-resource.vscode-cdn.net/opt/homebrew/Caskroom/miniconda/base/envs/crewai/lib/python3.12/site-packages/crewai/llms/providers/anthropic/completion.py:305)     return self._handle_completion(
    306         completion_params,
    307         available_functions,
    308         from_task,
    309         from_agent,
    310         effective_response_model,
    311     )
    313 except Exception as e:
    314     error_msg = f"Anthropic API call failed: {e!s}"

File /opt/homebrew/Caskroom/miniconda/base/envs/crewai/lib/python3.12/site-packages/crewai/llms/providers/anthropic/completion.py:673, in AnthropicCompletion._handle_completion(self, params, available_functions, from_task, from_agent, response_model)
    671         logging.error(f"Context window exceeded: {e}")
    672         raise LLMContextLengthExceededError(str(e)) from e
--> [673](https://file+.vscode-resource.vscode-cdn.net/opt/homebrew/Caskroom/miniconda/base/envs/crewai/lib/python3.12/site-packages/crewai/llms/providers/anthropic/completion.py:673)     raise e from e
    675 usage = self._extract_anthropic_token_usage(response)
    676 self._track_token_usage_internal(usage)

File /opt/homebrew/Caskroom/miniconda/base/envs/crewai/lib/python3.12/site-packages/crewai/llms/providers/anthropic/completion.py:667, in AnthropicCompletion._handle_completion(self, params, available_functions, from_task, from_agent, response_model)
    663         response = self.client.beta.messages.create(
    664             **params, extra_body=extra_body
    665         )
    666     else:
--> [667](https://file+.vscode-resource.vscode-cdn.net/opt/homebrew/Caskroom/miniconda/base/envs/crewai/lib/python3.12/site-packages/crewai/llms/providers/anthropic/completion.py:667)         response = self.client.messages.create(**params)
    669 except Exception as e:
    670     if is_context_length_exceeded(e):

File /opt/homebrew/Caskroom/miniconda/base/envs/crewai/lib/python3.12/site-packages/anthropic/_utils/_utils.py:282, in required_args..inner..wrapper(*args, **kwargs)
    280             msg = f"Missing required argument: {quote(missing[0])}"
    281     raise TypeError(msg)
--> [282](https://file+.vscode-resource.vscode-cdn.net/opt/homebrew/Caskroom/miniconda/base/envs/crewai/lib/python3.12/site-packages/anthropic/_utils/_utils.py:282) return func(*args, **kwargs)

File /opt/homebrew/Caskroom/miniconda/base/envs/crewai/lib/python3.12/site-packages/anthropic/resources/messages/messages.py:930, in Messages.create(self, max_tokens, messages, model, metadata, service_tier, stop_sequences, stream, system, temperature, thinking, tool_choice, tools, top_k, top_p, extra_headers, extra_query, extra_body, timeout)
    923 if model in DEPRECATED_MODELS:
    924     warnings.warn(
    925         f"The model '{model}' is deprecated and will reach end-of-life on {DEPRECATED_MODELS[model]}.\nPlease migrate to a newer model. Visit https://docs.anthropic.com/en/docs/resources/model-deprecations for more information.",
    926         DeprecationWarning,
    927         stacklevel=3,
    928     )
--> [930](https://file+.vscode-resource.vscode-cdn.net/opt/homebrew/Caskroom/miniconda/base/envs/crewai/lib/python3.12/site-packages/anthropic/resources/messages/messages.py:930) return self._post(
    931     "/v1/messages",
    932     body=maybe_transform(
    933         {
    934             "max_tokens": max_tokens,
    935             "messages": messages,
    936             "model": model,
    937             "metadata": metadata,
    938             "service_tier": service_tier,
    939             "stop_sequences": stop_sequences,
    940             "stream": stream,
    941             "system": system,
    942             "temperature": temperature,
    943             "thinking": thinking,
    944             "tool_choice": tool_choice,
    945             "tools": tools,
    946             "top_k": top_k,
    947             "top_p": top_p,
    948         },
    949         message_create_params.MessageCreateParamsStreaming
    950         if stream
    951         else message_create_params.MessageCreateParamsNonStreaming,
    952     ),
    953     options=make_request_options(
    954         extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
    955     ),
    956     cast_to=Message,
    957     stream=stream or False,
    958     stream_cls=Stream[RawMessageStreamEvent],
    959 )

File /opt/homebrew/Caskroom/miniconda/base/envs/crewai/lib/python3.12/site-packages/anthropic/_base_client.py:[1326](https://file+.vscode-resource.vscode-cdn.net/opt/homebrew/Caskroom/miniconda/base/envs/crewai/lib/python3.12/site-packages/anthropic/_base_client.py:1326), in SyncAPIClient.post(self, path, cast_to, body, options, files, stream, stream_cls)
   1312 def post(
   1313     self,
   1314     path: str,
   (...)   1321     stream_cls: type[_StreamT] | None = None,
   1322 ) -> ResponseT | _StreamT:
   1323     opts = FinalRequestOptions.construct(
   1324         method="post", url=path, json_data=body, files=to_httpx_files(files), **options
   1325     )
-> 1326     return cast(ResponseT, self.request(cast_to, opts, stream=stream, stream_cls=stream_cls))

File /opt/homebrew/Caskroom/miniconda/base/envs/crewai/lib/python3.12/site-packages/anthropic/_base_client.py:[1114](https://file+.vscode-resource.vscode-cdn.net/opt/homebrew/Caskroom/miniconda/base/envs/crewai/lib/python3.12/site-packages/anthropic/_base_client.py:1114), in SyncAPIClient.request(self, cast_to, options, stream, stream_cls)
   1111             err.response.read()
   1113         log.debug("Re-raising status error")
-> 1114         raise self._make_status_error_from_response(err.response) from None
   1116     break
   1118 assert response is not None, "could not resolve response (should never happen)"

BadRequestError: Error code: 400 - {'type': 'error', 'error': {'type': 'invalid_request_error', 'message': 'messages.0: all messages must have non-empty content except for the optional final assistant message'}, 'request_id': 'req_011CXy2Dhve1bt5pTfoXAsxN'}
```

### Possible Solution

None

### Additional context

None

## Comments

**Chase-Xuu:**
I've submitted a fix for this issue in PR #4429

**github-actions[bot]:**
This issue is stale because it has been open for 30 days with no activity. Remove stale label or comment or this will be closed in 5 days.

**github-actions[bot]:**
This issue was closed because it has been stalled for 5 days with no activity.

**Jairooh:**
This issue got auto-closed before getting resolved — the root cause is that Anthropic's API requires at least one non-empty content block in the `messages` array, so when CrewAI passes an empty string for a user message it throws a validation error. A quick workaround is to add a guard before the API call: if `message.content` is empty or whitespace, replace it with a single space or a placeholder like `"."` to satisfy the schema requirement. If you're still hitting this, it's worth opening a fresh issue with a minimal reproduction so it doesn't get stale-closed again.

**Jairooh:**
This issue being closed as "not planned" is a bit frustrating if you're hitting it in production — a quick workaround is to filter your message list before passing to the Anthropic client and ensure no `HumanMessage` has an empty `content` string (e.g., replace `""` with `" "` or strip those messages entirely). The root cause is that Anthropic's API strictly rejects empty content blocks, unlike OpenAI, so the validation gap is on CrewAI's side when constructing the message payload.

**Jairooh:**
This issue got auto-closed, but for anyone hitting the `AnthropicCompletion` empty user message error — the fix is to ensure at least one non-empty `user` message exists before sending to the Anthropic API, since it strictly rejects empty `content` arrays. A quick workaround is to add a guard in your task/agent definition that falls back to a whitespace-free placeholder or restructures the message chain so the final user turn always has content. If the CrewAI core fix is still pending, you can also patch it locally by subclassing the completion handler and filtering out empty messages before the API call.
