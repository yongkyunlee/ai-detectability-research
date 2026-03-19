# core: `missing_required_parameter` when using LangGraph to pass multimodal data to models

**Issue #31505** | State: open | Created: 2025-06-05 | Updated: 2026-03-11
**Author:** brunoshine
**Labels:** help wanted, investigate, core, external

### Checked other resources

- [x] I added a very descriptive title to this issue.
- [x] I used the GitHub search to find a similar question and didn't find it.
- [x] I am sure that this is a bug in LangChain rather than my code.
- [x] The bug is not resolved by updating to the latest stable version of LangChain (or the specific integration package).
- [x] I posted a self-contained, minimal, reproducible example. A maintainer can copy it and run it AS IS.

### Example Code

Hi all,

```python
 messages = prompt + state["messages"]
 chat = ChatPromptTemplate.from_messages(messages)
logger.debug("-------------------------------------------------------------------------------->> invoking LLM with config")
logger.debug(f"{chat}")
logger.debug("-------------------------------------------------------------------------------->> invoking LLM...")
response = await model.ainvoke(chat.format_prompt(), config)
```

### Error Message and Stack Trace (if applicable)

this outputs:
```bash
== APP == -------------------------------------------------------------------------------->> invoking LLM with config
== APP == input_variables=[] input_types={} partial_variables={} messages=[SystemMessage(content="You are a concierge agent. You are very helpful and friendly. You are very polite and respectful. You are always ready to help.\n\ncurrent date/time: 2025-06-05 19:32:40\n\nuser context: {'id': '123123123', 'name': 'Bruno Figueiredo', 'avatar': ''}", additional_kwargs={}, response_metadata={}), HumanMessage(content='olá', additional_kwargs={}, response_metadata={}, id='8fa5db18-69b0-4085-9d4e-aa16847da243'), AIMessage(content='Olá, Bruno! 😊 Como posso ajudar você hoje?', additional_kwargs={}, response_metadata={'finish_reason': 'stop', 'model_name': 'gpt-4o-2024-11-20', 'system_fingerprint': 'fp_ee1d74bde0'}, id='run-2df83ba9-a843-4029-a020-0d41465fddf3'), HumanMessage(content=[{'type': 'text', 'text': 'resume'}, {'type': 'file', 'source_type': 'url', 'url': 'https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf'}], additional_kwargs={}, response_metadata={}, id='363b871a-d9bc-4f40-ab56-5138486e7f07')]
== APP == -------------------------------------------------------------------------------->> invoking LLM...
== APP == Error invoking model: Error code: 400 - {'error': {'message': "Missing required parameter: 'messages[3].content[1].file'.", 'type': 'invalid_request_error', 'param': 'messages[3].content[1].file', 'code': 'missing_required_parameter'}}
```

### Description

Hi all,

I have a langgraph agent with several nodes and I'm calling the graph via `agent.astream_events(**kwargs, version="v2")`.

Tested with GPT4o and gemini-1.5-flash

If I use an image the code works well
```python
HumanMessage(
                    content=[
                        {"type": "text", "text": user_input.message},
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{user_input.file_type};base64,{user_input.file}"
                            },
                        }
                    ]
                )
```

but if I use a file I get the error above

```python
 HumanMessage(
                        content=[
                            {"type": "text", "text": user_input.message},
                            {
                                "type": "file",
                                "source_type": "url",
                                "url": "https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf",
                            },
                        ]
                    )
```

Any thoughs? thanks

### System Info

== APP == 
== APP == System Information
== APP == ------------------
== APP == > OS:  Linux
== APP == > OS Version:  #1 SMP PREEMPT_DYNAMIC Mon Apr 21 17:08:54 UTC 2025
== APP == > Python Version:  3.12.3 (main, Feb  4 2025, 14:48:35) [GCC 13.3.0]
== APP == 
== APP == Package Information
== APP == -------------------
== APP == > langchain_core: 0.3.48
== APP == > langchain: 0.3.15
== APP == > langchain_community: 0.3.15
== APP == > langsmith: 0.2.11
== APP == > langchain_chroma: 0.1.4
== APP == > langchain_google_genai: 2.1.1
== APP == > langchain_groq: 0.3.1
== APP == > langchain_mcp_adapters: 0.0.5
== APP == > langchain_ollama: 0.3.0
== APP == > langchain_openai: 0.2.14
== APP == > langchain_postgres: 0.0.13
== APP == > langchain_text_splitters: 0.3.5
== APP == > langgraph_sdk: 0.1.51
== APP == 
== APP == Optional packages not installed
== APP == -------------------------------
== APP == > langserve
== APP == 
== APP == Other Dependencies
== APP == ------------------
== APP == > aiohttp: 3.11.11
== APP == > async-timeout: Installed. No version info available.
== APP == > chromadb: 0.5.0
== APP == > dataclasses-json: 0.6.7
== APP == > fastapi: 0.115.6
== APP == > filetype: 1.2.0
== APP == > google-ai-generativelanguage: 0.6.17
== APP == > groq=0.4.1: Installed. No version info available.
== APP == > httpx: 0.28.1
== APP == > httpx-sse: 0.4.0
== APP == > jsonpatch=1.33: Installed. No version info available.
== APP == > langchain-core=0.3.36: Installed. No version info available.
== APP == > langchain-core=0.3.47: Installed. No version info available.
== APP == > langsmith-pyo3: Installed. No version info available.
== APP == > langsmith=0.1.125: Installed. No version info available.
== APP == > mcp=1.4.1: Installed. No version info available.
== APP == > numpy: 1.26.4
== APP == > ollama=0.4.4: Installed. No version info available.
== APP == > openai: 1.59.9
== APP == > orjson: 3.10.15
== APP == > packaging=23.2: Installed. No version info available.
== APP == > pgvector: 0.2.5
== APP == > psycopg: 3.2.6
== APP == > psycopg-pool: 3.2.6
== APP == > pydantic: 2.10.5
== APP == > pydantic-settings: 2.7.1
== APP == > pydantic=2.5.2;: Installed. No version info available.
== APP == > pydantic=2.7.4;: Installed. No version info available.
== APP == > PyYAML: 6.0.2
== APP == > PyYAML>=5.3: Installed. No version info available.
== APP == > requests: 2.32.3
== APP == > requests-toolbelt: 1.0.0
== APP == > SQLAlchemy: 2.0.37
== APP == > sqlalchemy: 2.0.37
== APP == > tenacity: 9.0.0
== APP == > tenacity!=8.4.0,=8.1.0: Installed. No version info available.
== APP == > tiktoken: 0.8.0
== APP == > typing-extensions>=4.7: Installed. No version info available.
== APP == > zstandard: Installed. No version info available.

## Comments

**ccurme:**
Hello, thanks for reporting this. Could you upgrade your `langchain-core` to latest to see if that resolves your issue? I see you have 0.3.48 installed, but the format used for the PDF there was introduced in 0.3.52.

**FedericoCampe8:**
same here with version 0.3.63 (for core)

**EandrewJones:**
Version 0.3.63, minimum reproducible example.
```python
from dotenv import load_dotenv
import os
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI

load_dotenv('../')
key = os.getenv('OPENAI_API_KEY')

llm: ChatOpenAI = ChatOpenAI(
    model="gpt-4o-2024-08-06",
    seed=42,
    openai_api_key=key,  # type: ignore
)

content_array = [
    {
        "type": "file",
        "file": {
            "filename": "4251bdfa8240ecbed84028ec4372beb2.pdf",
            "file_data": "data:application/pdf;base64,JVBERi0xLjQKMSAwIG9iago8PC9UeXBlIC9DYXRhbG9nCi9QYWdlcyAyIDAgUgo+PgplbmRvYmoKMiAwIG9iago8PC9UeXBlIC9QYWdlcwovS2lkcyBbMyAwIFJdCi9Db3VudCAxCj4+CmVuZG9iagozIDAgb2JqCjw8L1R5cGUgL1BhZ2UKL1BhcmVudCAyIDAgUgovTWVkaWFCb3ggWzAgMCA1OTUgODQyXQovQ29udGVudHMgNSAwIFIKL1Jlc291cmNlcyA8PC9Qcm9jU2V0IFsvUERGIC9UZXh0XQovRm9udCA8PC9GMSA0IDAgUj4+Cj4+Cj4+CmVuZG9iago0IDAgb2JqCjw8L1R5cGUgL0ZvbnQKL1N1YnR5cGUgL1R5cGUxCi9OYW1lIC9GMQovQmFzZUZvbnQgL0hlbHZldGljYQovRW5jb2RpbmcgL01hY1JvbWFuRW5jb2RpbmcKPj4KZW5kb2JqCjUgMCBvYmoKPDwvTGVuZ3RoIDUzCj4+CnN0cmVhbQpCVAovRjEgMjAgVGYKMjIwIDQwMCBUZAooRHVtbXkgUERGKSBUagpFVAplbmRzdHJlYW0KZW5kb2JqCnhyZWYKMCA2CjAwMDAwMDAwMDAgNjU1MzUgZgowMDAwMDAwMDA5IDAwMDAwIG4KMDAwMDAwMDA2MyAwMDAwMCBuCjAwMDAwMDAxMjQgMDAwMDAgbgowMDAwMDAwMjc3IDAwMDAwIG4KMDAwMDAwMDM5MiAwMDAwMCBuCnRyYWlsZXIKPDwvU2l6ZSA2Ci9Sb290IDEgMCBSCj4+CnN0YXJ0eHJlZgo0OTUKJSVFT0YK"
        }
    },
    {
        "type": "text",
        "text": "What does this PDF say?"
    }
]
message = HumanMessage(content=content_array)
response = llm.invoke([message])
```
The above fails with:
```
---------------------------------------------------------------------------
BadRequestError                           Traceback (most recent call last)
Cell In[9], line 32
     18 content_array = [
     19     {
     20         "type": "file",
   (...)     29     }
     30 ]
     31 message = HumanMessage(content=content_array)
---> 32 response = llm.invoke([message])

File /data/project-repos/homa/homa-analytics/.venv/lib/python3.12/site-packages/langchain_core/language_models/chat_models.py:371, in BaseChatModel.invoke(self, input, config, stop, **kwargs)
    359 @override
    360 def invoke(
    361     self,
   (...)    366     **kwargs: Any,
    367 ) -> BaseMessage:
    368     config = ensure_config(config)
    369     return cast(
    370         "ChatGeneration",
--> 371         self.generate_prompt(
    372             [self._convert_input(input)],
    373             stop=stop,
    374             callbacks=config.get("callbacks"),
    375             tags=config.get("tags"),
    376             metadata=config.get("metadata"),
    377             run_name=config.get("run_name"),
    378             run_id=config.pop("run_id", None),
    379             **kwargs,
    380         ).generations[0][0],
    381     ).message

File /data/project-repos/homa/homa-analytics/.venv/lib/python3.12/site-packages/langchain_core/language_models/chat_models.py:956, in BaseChatModel.generate_prompt(self, prompts, stop, callbacks, **kwargs)
    947 @override
    948 def generate_prompt(
    949     self,
   (...)    953     **kwargs: Any,
    954 ) -> LLMResult:
    955     prompt_messages = [p.to_messages() for p in prompts]
--> 956     return self.generate(prompt_messages, stop=stop, callbacks=callbacks, **kwargs)

File /data/project-repos/homa/homa-analytics/.venv/lib/python3.12/site-packages/langchain_core/language_models/chat_models.py:775, in BaseChatModel.generate(self, messages, stop, callbacks, tags, metadata, run_name, run_id, **kwargs)
    772 for i, m in enumerate(input_messages):
    773     try:
    774         results.append(
--> 775             self._generate_with_cache(
    776                 m,
    777                 stop=stop,
    778                 run_manager=run_managers[i] if run_managers else None,
    779                 **kwargs,
    780             )
    781         )
    782     except BaseException as e:
    783         if run_managers:

File /data/project-repos/homa/homa-analytics/.venv/lib/python3.12/site-packages/langchain_core/language_models/chat_models.py:1021, in BaseChatModel._generate_with_cache(self, messages, stop, run_manager, **kwargs)
   1019     result = generate_from_stream(iter(chunks))
   1020 elif inspect.signature(self._generate).parameters.get("run_manager"):
-> 1021     result = self._generate(
   1022         messages, stop=stop, run_manager=run_manager, **kwargs
   1023     )
   1024 else:
   1025     result = self._generate(messages, stop=stop, **kwargs)

File /data/project-repos/homa/homa-analytics/.venv/lib/python3.12/site-packages/langchain_openai/chat_models/base.py:717, in BaseChatOpenAI._generate(self, messages, stop, run_manager, **kwargs)
    715     generation_info = {"headers": dict(raw_response.headers)}
    716 else:
--> 717     response = self.client.create(**payload)
    718 return self._create_chat_result(response, generation_info)

File /data/project-repos/homa/homa-analytics/.venv/lib/python3.12/site-packages/openai/_utils/_utils.py:287, in required_args..inner..wrapper(*args, **kwargs)
    285             msg = f"Missing required argument: {quote(missing[0])}"
    286     raise TypeError(msg)
--> 287 return func(*args, **kwargs)

File /data/project-repos/homa/homa-analytics/.venv/lib/python3.12/site-packages/openai/resources/chat/completions/completions.py:925, in Completions.create(self, messages, model, audio, frequency_penalty, function_call, functions, logit_bias, logprobs, max_completion_tokens, max_tokens, metadata, modalities, n, parallel_tool_calls, prediction, presence_penalty, reasoning_effort, response_format, seed, service_tier, stop, store, stream, stream_options, temperature, tool_choice, tools, top_logprobs, top_p, user, web_search_options, extra_headers, extra_query, extra_body, timeout)
    882 @required_args(["messages", "model"], ["messages", "model", "stream"])
    883 def create(
    884     self,
   (...)    922     timeout: float | httpx.Timeout | None | NotGiven = NOT_GIVEN,
    923 ) -> ChatCompletion | Stream[ChatCompletionChunk]:
    924     validate_response_format(response_format)
--> 925     return self._post(
    926         "/chat/completions",
    927         body=maybe_transform(
    928             {
    929                 "messages": messages,
    930                 "model": model,
    931                 "audio": audio,
    932                 "frequency_penalty": frequency_penalty,
    933                 "function_call": function_call,
    934                 "functions": functions,
    935                 "logit_bias": logit_bias,
    936                 "logprobs": logprobs,
    937                 "max_completion_tokens": max_completion_tokens,
    938                 "max_tokens": max_tokens,
    939                 "metadata": metadata,
    940                 "modalities": modalities,
    941                 "n": n,
    942                 "parallel_tool_calls": parallel_tool_calls,
    943                 "prediction": prediction,
    944                 "presence_penalty": presence_penalty,
    945                 "reasoning_effort": reasoning_effort,
    946                 "response_format": response_format,
    947                 "seed": seed,
    948                 "service_tier": service_tier,
    949                 "stop": stop,
    950                 "store": store,
    951                 "stream": stream,
    952                 "stream_options": stream_options,
    953                 "temperature": temperature,
    954                 "tool_choice": tool_choice,
    955                 "tools": tools,
    956                 "top_logprobs": top_logprobs,
    957                 "top_p": top_p,
    958                 "user": user,
    959                 "web_search_options": web_search_options,
    960             },
    961             completion_create_params.CompletionCreateParamsStreaming
    962             if stream
    963             else completion_create_params.CompletionCreateParamsNonStreaming,
    964         ),
    965         options=make_request_options(
    966             extra_headers=extra_headers, extra_query=extra_query, extra_body=extra_body, timeout=timeout
    967         ),
    968         cast_to=ChatCompletion,
    969         stream=stream or False,
    970         stream_cls=Stream[ChatCompletionChunk],
    971     )

File /data/project-repos/homa/homa-analytics/.venv/lib/python3.12/site-packages/openai/_base_client.py:1242, in SyncAPIClient.post(self, path, cast_to, body, options, files, stream, stream_cls)
   1228 def post(
   1229     self,
   1230     path: str,
   (...)   1237     stream_cls: type[_StreamT] | None = None,
   1238 ) -> ResponseT | _StreamT:
   1239     opts = FinalRequestOptions.construct(
   1240         method="post", url=path, json_data=body, files=to_httpx_files(files), **options
   1241     )
-> 1242     return cast(ResponseT, self.request(cast_to, opts, stream=stream, stream_cls=stream_cls))

File /data/project-repos/homa/homa-analytics/.venv/lib/python3.12/site-packages/openai/_base_client.py:1037, in SyncAPIClient.request(self, cast_to, options, stream, stream_cls)
   1034             err.response.read()
   1036         log.debug("Re-raising status error")
-> 1037         raise self._make_status_error_from_response(err.response) from None
   1039     break
   1041 assert response is not None, "could not resolve response (should never happen)"

BadRequestError: Error code: 400 - {'error': {'message': "Missing required parameter: 'messages[0].content[0].file'.", 'type': 'invalid_request_error', 'param': 'messages[0].content[0].file', 'code': 'missing_required_parameter'}}
```

But calling openai `chat/completions` with the same payload:
```json
{
    "model": "gpt-4o-2024-08-06",
    "messages": [
        {
            "role": "user",
            "content": [
                {
                    "type": "file",
                    "file": {
                        "filename": "4251bdfa8240ecbed84028ec4372beb2.pdf",
                        "file_data": "data:application/pdf;base64,JVBERi0xLjQKMSAwIG9iago8PC9UeXBlIC9DYXRhbG9nCi9QYWdlcyAyIDAgUgo+PgplbmRvYmoKMiAwIG9iago8PC9UeXBlIC9QYWdlcwovS2lkcyBbMyAwIFJdCi9Db3VudCAxCj4+CmVuZG9iagozIDAgb2JqCjw8L1R5cGUgL1BhZ2UKL1BhcmVudCAyIDAgUgovTWVkaWFCb3ggWzAgMCA1OTUgODQyXQovQ29udGVudHMgNSAwIFIKL1Jlc291cmNlcyA8PC9Qcm9jU2V0IFsvUERGIC9UZXh0XQovRm9udCA8PC9GMSA0IDAgUj4+Cj4+Cj4+CmVuZG9iago0IDAgb2JqCjw8L1R5cGUgL0ZvbnQKL1N1YnR5cGUgL1R5cGUxCi9OYW1lIC9GMQovQmFzZUZvbnQgL0hlbHZldGljYQovRW5jb2RpbmcgL01hY1JvbWFuRW5jb2RpbmcKPj4KZW5kb2JqCjUgMCBvYmoKPDwvTGVuZ3RoIDUzCj4+CnN0cmVhbQpCVAovRjEgMjAgVGYKMjIwIDQwMCBUZAooRHVtbXkgUERGKSBUagpFVAplbmRzdHJlYW0KZW5kb2JqCnhyZWYKMCA2CjAwMDAwMDAwMDAgNjU1MzUgZgowMDAwMDAwMDA5IDAwMDAwIG4KMDAwMDAwMDA2MyAwMDAwMCBuCjAwMDAwMDAxMjQgMDAwMDAgbgowMDAwMDAwMjc3IDAwMDAwIG4KMDAwMDAwMDM5MiAwMDAwMCBuCnRyYWlsZXIKPDwvU2l6ZSA2Ci9Sb290IDEgMCBSCj4+CnN0YXJ0eHJlZgo0OTUKJSVFT0YK"
                    }
                },
                {
                    "type": "text",
                    "text": "What does this say?"
                }
            ]
        }
    ]
}
```
Response:
```json
{
    "id": "chatcmpl-BfD5RLiOYlfcsy22Hoi9adf6S6veJ",
    "object": "chat.completion",
    "created": 1749161453,
    "model": "gpt-4o-2024-08-06",
    "choices": [
        {
            "index": 0,
            "message": {
                "role": "assistant",
                "content": "The document contains the text \"Dummy PDF.\"",
                "refusal": null,
                "annotations": []
            },
            "logprobs": null,
            "finish_reason": "stop"
        }
    ],
    "usage": {
        "prompt_tokens": 230,
        "completion_tokens": 9,
        "total_tokens": 239,
        "prompt_tokens_details": {
            "cached_tokens": 0,
            "audio_tokens": 0
        },
        "completion_tokens_details": {
            "reasoning_tokens": 0,
            "audio_tokens": 0,
            "accepted_prediction_tokens": 0,
            "rejected_prediction_tokens": 0
        }
    },
    "service_tier": "default",
    "system_fingerprint": "fp_07871e2ad8"
}

**ccurme:**
@EandrewJones I'm unable to reproduce the error on latest `langchain-openai`, can you confirm what version you're running?

@brunoshine I see your version of `langchain-openai` is also old, are you able to update as well?

Thanks all for the reports!

**EandrewJones:**
@ccurme, I updated to latest and it's working now. Thanks.

Best

Evan Jones


On Thu, Jun 5, 2025 at 3:22 PM ccurme ***@***.***> wrote:

> *ccurme* left a comment (langchain-ai/langchain#31505)
> 
>
> @EandrewJones  I'm unable to reproduce
> the error on latest langchain-openai, can you confirm what version you're
> running?
>
> @brunoshine  I see your version of
> langchain-openai is also old, are you able to update as well?
>
> Thanks all for the reports!
>
> —
> Reply to this email directly, view it on GitHub
> ,
> or unsubscribe
> 
> .
> You are receiving this because you were mentioned.Message ID:
> ***@***.***>
>

**brunoshine:**
Hi @ccurme thanks for the quick response.
some updates:

## Updated packages to latest versions
```
== APP == Package Information
== APP == -------------------
== APP == > langchain_core: 0.3.64
== APP == > langchain: 0.3.25
== APP == > langchain_community: 0.3.24
== APP == > langsmith: 0.3.45
== APP == > langchain_chroma: 0.1.4
== APP == > langchain_google_genai: 2.1.5
== APP == > langchain_groq: 0.3.2
== APP == > langchain_mcp_adapters: 0.0.5
== APP == > langchain_ollama: 0.3.3
== APP == > langchain_openai: 0.3.19
== APP == > langchain_postgres: 0.0.13
== APP == > langchain_text_splitters: 0.3.8
== APP == > langgraph_sdk: 0.1.51
```

Google model: gemini-1.5-flash
(Azure) OpenAI model: GPT-4o

## URL Path Test
```python
input_messages.append(
    {
        "role": "user",
        "content": [
            {
                "type": "text",
                "text": user_input.message,
            },
            {
                "type": "file",
                "source_type": "url",
                "url": user_input.file_path,
            },
        ],
    }
)
```

**Google** ✅

**(Azure) OpenAI** 🛑
error:
```
== APP == Error invoking model: source_type base64 or id is required for file blocks.
```

## Base64 Test
if I use:
```python
file_data = base64.b64encode(
    httpx.get(user_input.file_path).content
).decode("utf-8")
input_messages.append(
    {
        "role": "user",
        "content": [
            {
                "type": "text",
                "text": user_input.message,
            },
            {
                "type": "file",
                "source_type": "base64",
                "data": file_data,
                "mime_type": user_input.file_type,
            },
        ],
    }
)
```

**Google** ✅

**(Azure) OpenAI** 🛑
error:
```
== APP == Error invoking model: Error code: 400 - {'error': {'message': "Missing required parameter: 'messages[1].content[1].file.file_id'.", 'type': 'invalid_request_error', 'param': 'messages[1].content[1].file.file_id', 'code': 'missing_required_parameter'}}
```

Any thoughts? Thanks

**brunoshine:**
As additional support, here is a notebook that showcases the error:
[gist](https://gist.github.com/brunoshine/c1870f503b095a4ff4a79bf45c14dab2)

I can also confirm that:

- the error also happens with the `ChatOpenAI` class (additionally to the Azure one shown above)
- if I change the message format from the one [described on the documentation](https://python.langchain.com/docs/how_to/multimodal_inputs/#documents-from-base64-data) to the [example above](https://github.com/langchain-ai/langchain/issues/31505#issuecomment-2946528242) provided by @EandrewJones, the model starts responding correctly **but only** for `ChatOpenAI` class. For the `AzureChatOpenAI` it throws `{'error': {'message': "Invalid Value: 'file'. This model does not support file content types.", 'type': 'invalid_request_error', 'param': 'messages[0].content[1].type', 'code': 'invalid_value'}}`

**ccurme:**
Hi @brunoshine,

I believe the first example fails because OpenAI does not support loading PDFs from URLs (see their docs [here](https://platform.openai.com/docs/guides/pdf-files)). LangChain's Google integration may have extra logic to pull the PDF client-side and upload the bytes in-line.

For the second issue, OpenAI requires a filename attached to PDFs. You should be seeing a warning with your requests. There's a note on this in the guide here: https://python.langchain.com/docs/how_to/multimodal_inputs/#example-openai-file-names

**brunoshine:**
Hi @ccurme, thank you for the reply.

I've updated the tests and these are the results. Google and OpenAI works. Azure OpenAI **does not work**.

> I believe the first example fails because OpenAI does not support loading PDFs from URLs (see their docs [here](https://platform.openai.com/docs/guides/pdf-files)). LangChain's Google integration may have extra logic to pull the PDF client-side and upload the bytes in-line.

Shouldn't this work the same across the board? Meaning, LangChain model providers have the same behaviour, being that its already making an abstraction over how to send the files to the models.

Thanks

## Message format

```python
pdf_url = public_url
pdf_data = base64.b64encode(httpx.get(pdf_url).content).decode("utf-8")

message = {
    "role": "user",
    "content": [
        {
            "type": "text",
            "text": "Describe the document:",
        },
        {
            "type": "file",
            "source_type": "base64",
            "data": pdf_data,
            "mime_type": "application/pdf",
            "filename": "file_name.pdf",
        }
        
    ],
}
```

## Google ✅

```python
# Pass to LLM
llmGoogle = ChatGoogleGenerativeAI(
    model="gemini-1.5-flash",
    api_key=os.getenv("GOOGLE_API_KEY"),
)

print("Sending message to azure model...")
response = await llmGoogle.ainvoke([message])
print(response.text())
```
Output:
```bash
Sending message to azure model...
This is a three-page document outlining the rules and regulations for a ....
```

## OpenAI ✅

```python
llmOAI = ChatOpenAI(
    api_key=api_key_secret,
    model=os.getenv("MODEL_NAME"),
    streaming=True,
)

print("Sending message to OAI model...")
response = await llmOAI.ainvoke([message])
print(response.text())
```
Output:
```bash
Sending message to OAI model...
The document is a regulation for a promotional campaign titled  ....
```

## Azure OpenAI 🛑

```python
llmAOAI = AzureChatOpenAI(
    azure_deployment=os.getenv("DEPLOYMENT_NAME"),
    api_key=os.getenv("AZURE_API_KEY"),
    model=os.getenv("AZURE_MODEL"),
    azure_endpoint=os.getenv("AZURE_ENDPOINT"),
    api_version=os.getenv("AZURE_API_VERSION"),
    streaming=True,
)

print("Sending message to Azure OAI model...")
response = await llmAOAI.ainvoke([message])
print(response.text())
```
Output:
```bash
Sending message to Azure OAI model...
BadRequestError: Error code: 400 - {'error': {'message': "Invalid Value: 'file'. This model does not support file content types.", 'type': 'invalid_request_error', 'param': 'messages[0].content[1].type', 'code': 'invalid_value'}}

```

**ccurme:**
What model is deployed under `azure_deployment`? That error is from the server and is saying that file inputs aren't compatible with that specific model.
