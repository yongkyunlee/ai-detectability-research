# LangChain-OpenAI raises error due to null choices when using vLLM OpenAI-compatible API

**Issue #32252** | State: closed | Created: 2025-07-26 | Updated: 2026-03-01
**Author:** escon1004
**Labels:** help wanted, bug, investigate, openai, external

### Checked other resources

- [x] This is a bug, not a usage question. For questions, please use the LangChain Forum (https://forum.langchain.com/).
- [x] I added a clear and descriptive title that summarizes this issue.
- [x] I used the GitHub search to find a similar question and didn't find it.
- [x] I am sure that this is a bug in LangChain rather than my code.
- [x] The bug is not resolved by updating to the latest stable version of LangChain (or the specific integration package).
- [x] I read what a minimal reproducible example is (https://stackoverflow.com/help/minimal-reproducible-example).
- [x] I posted a self-contained, minimal, reproducible example. A maintainer can copy it and run it AS IS.

### Example Code

```python
from langchain_openai  import ChatOpenAI
from vllm.multimodal.utils import encode_image_base64, fetch_image
from PIL import Image
from langchain_core.messages import HumanMessage, AIMessage

llm = ChatOpenAI(
    api_key="rpa_",
    base_url="https://api.runpod.ai/v2//openai/v1",
)

image = Image.open("/content/Z4_59005_P0_L0.png").convert("RGB")
image_base64 = encode_image_base64(image)

messages = [
    HumanMessage(
        content=[
            {"type": "text", "text": instruction},
            {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{image_base64}"}}
        ]
    )
]

response = llm.invoke(messages)
```
It raises an error as shown below.
```
TypeError                                 Traceback (most recent call last)
[/tmp/ipython-input-15-4196384846.py](https://localhost:8080/#) in ()
      1 # 4. 호출
----> 2 response = llm.invoke(messages)

5 frames
[/usr/local/lib/python3.11/dist-packages/langchain_core/language_models/chat_models.py](https://localhost:8080/#) in invoke(self, input, config, stop, **kwargs)
    393         return cast(
    394             "ChatGeneration",
--> 395             self.generate_prompt(
    396                 [self._convert_input(input)],
    397                 stop=stop,

[/usr/local/lib/python3.11/dist-packages/langchain_core/language_models/chat_models.py](https://localhost:8080/#) in generate_prompt(self, prompts, stop, callbacks, **kwargs)
    978     ) -> LLMResult:
    979         prompt_messages = [p.to_messages() for p in prompts]
--> 980         return self.generate(prompt_messages, stop=stop, callbacks=callbacks, **kwargs)
    981 
    982     @override

[/usr/local/lib/python3.11/dist-packages/langchain_core/language_models/chat_models.py](https://localhost:8080/#) in generate(self, messages, stop, callbacks, tags, metadata, run_name, run_id, **kwargs)
    797             try:
    798                 results.append(
--> 799                     self._generate_with_cache(
    800                         m,
    801                         stop=stop,

[/usr/local/lib/python3.11/dist-packages/langchain_core/language_models/chat_models.py](https://localhost:8080/#) in _generate_with_cache(self, messages, stop, run_manager, **kwargs)
   1043             result = generate_from_stream(iter(chunks))
   1044         elif inspect.signature(self._generate).parameters.get("run_manager"):
-> 1045             result = self._generate(
   1046                 messages, stop=stop, run_manager=run_manager, **kwargs
   1047             )

[/usr/local/lib/python3.11/dist-packages/langchain_openai/chat_models/base.py](https://localhost:8080/#) in _generate(self, messages, stop, run_manager, **kwargs)
   1130         else:
   1131             response = self.client.create(**payload)
-> 1132         return self._create_chat_result(response, generation_info)
   1133 
   1134     def _use_responses_api(self, payload: dict) -> bool:

[/usr/local/lib/python3.11/dist-packages/langchain_openai/chat_models/base.py](https://localhost:8080/#) in _create_chat_result(self, response, generation_info)
   1199 
   1200         if choices is None:
-> 1201             raise TypeError("Received response with null value for `choices`.")
   1202 
   1203         token_usage = response_dict.get("usage")

TypeError: Received response with null value for `choices`.
```

However, when making a direct request using requests, the choices field is present and accessible.
```
import requests
api_key = "rpa_"
# 요청 헤더
headers = {
    "Authorization": f"Bearer {api_key}",  # RunPod API Key
    "Content-Type": "application/json"
}

# 요청 바디
payload = {
    "model": "oyh0107/gemma3_4b_bf16_skin_dataset_1000steps_r64_b8"
    "messages": [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": instruction},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{image_base64}"
                    }
                }
            ]
        }
    ]
}

# POST 요청
response = requests.post(
    "https://api.runpod.ai/v2//openai/v1/chat/completions",
    headers=headers,
    json=payload
)
```

The JSON response is as follows:
```json
{
    "choices": [
        {
            "finish_reason": "stop",
            "index": 0,
            "logprobs": null,
            "message": {
                "content": "혈관종\n이미지에서는 붉은색의 부드러운 결절이 관찰됩니다. 혈관종은 유아형과 성인형으로 나뉘며, 일반적으로 얼굴, 두피, 몸통 등에 위치합니다. 이 경우, 붉은색과 보라색이 혼합된 특징을 보이므로, 유아형 또는 성인형 혈관종일 가능성이 있습니다. 자연적으로 소실되는 경우가 많으나, 크거나 출혈이 발생할 경우에는 레이저 치료 또는 수술적 제거를 고려할 수 있습니다.",
                "reasoning_content": null,
                "role": "assistant",
                "tool_calls": []
            },
            "stop_reason": null
        }
    ],
    "created": 1753518740,
    "id": "chatcmpl-3e43bc8507e84744b64cf4aeeaed5632",
    "kv_transfer_params": null,
    "model": "oyh0107/gemma3_4b_bf16_skin_dataset_1000steps_r64_b8",
    "object": "chat.completion",
    "prompt_logprobs": null,
    "usage": {
        "completion_tokens": 129,
        "prompt_tokens": 2037,
        "prompt_tokens_details": null,
        "total_tokens": 2166
    }
}
```
It also works correctly when using the official OpenAI library directly.
```python
from openai import OpenAI
client = OpenAI(
    api_key="rpa_",
    base_url="https://api.runpod.ai/v2//openai/v1",
)
model = client.models.list().data[0].id

chat_response = client.chat.completions.create(
    model=model,
    messages=[
        {
            "role": "user",
            "content": [
                {"type": "text", "text": instruction},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{image_base64}",
                    },
                },
                
            ],
        }
    ],
)
```

```
ChatCompletion(id='chatcmpl-5d24c941e92444d58eadb085459ce8b7', choices=[Choice(finish_reason='stop', index=0, logprobs=None, message=ChatCompletionMessage(content='혈관종\n이미지에서는 붉거나 보라색의 부드러운 결절이 관찰됩니다. 병변의 표면은 매끄럽고, 모양은 불규칙하며, 크기가 커지고 있는 것처럼 보입니다. 혈관종은 유아형과 성인형으로 나뉘며, 이 경우 성인형의 특징을 보입니다. 유아형은 대개 자연 소실되지만, 성인형은 크기나 출혈이 있는 경우 레이저, 수술, 경화요법 등의 치료가 고려될 수 있습니다.', refusal=None, role='assistant', annotations=None, audio=None, function_call=None, tool_calls=[], reasoning_content=None), stop_reason=None)], created=1753517827, model='oyh0107/gemma3_4b_bf16_skin_dataset_1000steps_r64_b8', object='chat.completion', service_tier=None, system_fingerprint=None, usage=CompletionUsage(completion_tokens=133, prompt_tokens=1912, total_tokens=2045, completion_tokens_details=None, prompt_tokens_details=None), kv_transfer_params=None, prompt_logprobs=None)
```

### Error Message and Stack Trace (if applicable)

TypeError                                 Traceback (most recent call last)
[/tmp/ipython-input-15-4196384846.py](https://localhost:8080/#) in ()
      1 # 4. 호출
----> 2 response = llm.invoke(messages)

5 frames
[/usr/local/lib/python3.11/dist-packages/langchain_core/language_models/chat_models.py](https://localhost:8080/#) in invoke(self, input, config, stop, **kwargs)
    393         return cast(
    394             "ChatGeneration",
--> 395             self.generate_prompt(
    396                 [self._convert_input(input)],
    397                 stop=stop,

[/usr/local/lib/python3.11/dist-packages/langchain_core/language_models/chat_models.py](https://localhost:8080/#) in generate_prompt(self, prompts, stop, callbacks, **kwargs)
    978     ) -> LLMResult:
    979         prompt_messages = [p.to_messages() for p in prompts]
--> 980         return self.generate(prompt_messages, stop=stop, callbacks=callbacks, **kwargs)
    981 
    982     @override

[/usr/local/lib/python3.11/dist-packages/langchain_core/language_models/chat_models.py](https://localhost:8080/#) in generate(self, messages, stop, callbacks, tags, metadata, run_name, run_id, **kwargs)
    797             try:
    798                 results.append(
--> 799                     self._generate_with_cache(
    800                         m,
    801                         stop=stop,

[/usr/local/lib/python3.11/dist-packages/langchain_core/language_models/chat_models.py](https://localhost:8080/#) in _generate_with_cache(self, messages, stop, run_manager, **kwargs)
   1043             result = generate_from_stream(iter(chunks))
   1044         elif inspect.signature(self._generate).parameters.get("run_manager"):
-> 1045             result = self._generate(
   1046                 messages, stop=stop, run_manager=run_manager, **kwargs
   1047             )

[/usr/local/lib/python3.11/dist-packages/langchain_openai/chat_models/base.py](https://localhost:8080/#) in _generate(self, messages, stop, run_manager, **kwargs)
   1130         else:
   1131             response = self.client.create(**payload)
-> 1132         return self._create_chat_result(response, generation_info)
   1133 
   1134     def _use_responses_api(self, payload: dict) -> bool:

[/usr/local/lib/python3.11/dist-packages/langchain_openai/chat_models/base.py](https://localhost:8080/#) in _create_chat_result(self, response, generation_info)
   1199 
   1200         if choices is None:
-> 1201             raise TypeError("Received response with null value for `choices`.")
   1202 
   1203         token_usage = response_dict.get("usage")

TypeError: Received response with null value for `choices`.

### Description

**Description**  
I’m trying to use `langchain-openai` to call a RunPod Serverless Endpoint that serves a vLLM model using the OpenAI-compatible API (`/v1/chat/completions`).

**What is the problem, question, or error?**  
I expected `langchain-openai.ChatOpenAI` to work seamlessly with this endpoint, as it adheres to the OpenAI-compatible API specification. However, an error is raised:

TypeError: Received response with null value for choices.

This happens even though the same request works correctly when:

- I use the `requests` library directly (the JSON response includes a valid `choices` field)
- I use the official `openai` Python SDK

**Expected behavior**  
`langchain-openai` should parse the response correctly if the `choices` field is present in the returned JSON from a fully OpenAI-compatible endpoint like RunPod’s vLLM API.

**Actual behavior**  
An exception is thrown inside LangChain’s OpenAI wrapper because it assumes `choices` is `null`, even though it is not when tested with other clients.

**Steps to reproduce**  
1. Deploy a vLLM model (e.g., Gemma 3 4B) via RunPod’s serverless API with OpenAI-compatible mode  
2. Set `base_url` to `https://api.runpod.ai/v2//openai/v1` in `ChatOpenAI`  
3. Invoke with a `HumanMessage` containing both text and image (OpenAI-style format)  
4. Observe that it raises `TypeError: Received response with null value for choices.`

### System Info

System Information
------------------
> OS:  Linux
> OS Version:  #1 SMP PREEMPT_DYNAMIC Sun Mar 30 16:01:29 UTC 2025
> Python Version:  3.11.13 (main, Jun  4 2025, 08:57:29) [GCC 11.4.0]

Package Information
-------------------
> langchain_core: 0.3.71
> langchain: 0.3.26
> langsmith: 0.4.8
> langchain_openai: 0.3.28
> langchain_runpod: 0.2.0
> langchain_text_splitters: 0.3.8

Optional packages not installed
-------------------------------
> langserve

Other Dependencies
------------------
> async-timeout=4.0.0;: Installed. No version info available.
> httpx: 0.27.2
> jsonpatch=1.33: Installed. No version info available.
> langchain-anthropic;: Installed. No version info available.
> langchain-aws;: Installed. No version info available.
> langchain-azure-ai;: Installed. No version info available.
> langchain-cohere;: Installed. No version info available.
> langchain-community;: Installed. No version info available.
> langchain-core=0.3.51: Installed. No version info available.
> langchain-core=0.3.66: Installed. No version info available.
> langchain-core=0.3.68: Installed. No version info available.
> langchain-deepseek;: Installed. No version info available.
> langchain-fireworks;: Installed. No version info available.
> langchain-google-genai;: Installed. No version info available.
> langchain-google-vertexai;: Installed. No version info available.
> langchain-groq;: Installed. No version info available.
> langchain-huggingface;: Installed. No version info available.
> langchain-mistralai;: Installed. No version info available.
> langchain-ollama;: Installed. No version info available.
> langchain-openai;: Installed. No version info available.
> langchain-perplexity;: Installed. No version info available.
> langchain-text-splitters=0.3.8: Installed. No version info available.
> langchain-together;: Installed. No version info available.
> langchain-xai;: Installed. No version info available.
> langsmith-pyo3: Installed. No version info available.
> langsmith>=0.1.17: Installed. No version info available.
> langsmith>=0.3.45: Installed. No version info available.
> openai-agents: Installed. No version info available.
> openai=1.86.0: Installed. No version info available.
> opentelemetry-api: Installed. No version info available.
> opentelemetry-exporter-otlp-proto-http: Installed. No version info available.
> opentelemetry-sdk: Installed. No version info available.
> orjson: 3.11.0
> packaging: 25.0
> packaging>=23.2: Installed. No version info available.
> pydantic: 2.11.7
> pydantic=2.7.4: Installed. No version info available.
> pydantic>=2.7.4: Installed. No version info available.
> pytest: 8.4.1
> python-dotenv: 1.1.1
> PyYAML>=5.3: Installed. No version info available.
> requests: 2.32.3
> requests-toolbelt: 1.0.0
> requests=2: Installed. No version info available.
> rich: 13.9.4
> SQLAlchemy=1.4: Installed. No version info available.
> tenacity!=8.4.0,=8.1.0: Installed. No version info available.
> tiktoken=0.7: Installed. No version info available.
> typing-extensions>=4.7: Installed. No version info available.
> zstandard: 0.23.0

## Comments

**AkibDa:**
## The Root Cause: A Parsing Mismatch
The error `TypeError: Received response with null value for choices` originates from a specific check inside the `langchain-openai` library. Here's the likely sequence of events:

Your `llm.invoke(messages)` call correctly sends the request to the RunPod API endpoint.

The RunPod endpoint processes the request and sends back a valid JSON response containing the `choices` list, as you've proven.

The underlying `openai` client within LangChain receives this response.

The `langchain-openai` wrapper then takes this response object and attempts to parse it into its internal `ChatResult` format in a method called `_create_chat_result`.

This is where the failure occurs. The parsing logic in LangChain is likely making a rigid assumption about the structure or type of the response object returned by the `openai` client. For some reason, its method of extracting the `choices` attribute fails and returns `None`, even though the data is present.

This can happen if the response object from an OpenAI-compatible endpoint isn't identical in type and structure to the one from the official OpenAI API, causing the wrapper's parsing to fail while the more resilient, native `openai` library handles it correctly.

**AkibDa:**
## Workaround: Bypass the Faulty Parsing
Since the native `openai` library works perfectly, the most reliable workaround is to use it directly for the API call and then manually construct the LangChain `AIMessage` object. This gives you the benefit of a successful API call while still integrating the result into a LangChain workflow.

Here is the code combining your working `openai` call with LangChain's message structure:

```
from openai import OpenAI
from langchain_core.messages import AIMessage
import base64
from PIL import Image

# Assume 'instruction' and 'image_path' are defined
# instruction = "What do you see in this image?"
# image_path = "/content/Z4_59005_P0_L0.png"

# 1. Setup the native OpenAI client
client = OpenAI(
    api_key="rpa_",
    base_url="https://api.runpod.ai/v2//openai/v1",
)

# 2. Prepare the image and messages
with open(image_path, "rb") as image_file:
    image_base64 = base64.b64encode(image_file.read()).decode('utf-8')

messages = [
    {
        "role": "user",
        "content": [
            {"type": "text", "text": instruction},
            {
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/png;base64,{image_base64}",
                },
            },
        ],
    }
]

# 3. Make the API call using the native client
chat_response = client.chat.completions.create(
    model="oyh0107/gemma3_4b_bf16_skin_dataset_1000steps_r64_b8", # It's good practice to specify the model
    messages=messages
)

# 4. Manually construct the LangChain AIMessage
# This bypasses the faulty parsing in langchain-openai
if chat_response.choices:
    first_choice = chat_response.choices[0]
    message_content = first_choice.message.content
    
    # Extract token usage and other metadata
    usage_metadata = chat_response.usage.model_dump() if chat_response.usage else {}
    
    response_metadata = {
        "model_name": chat_response.model,
        "finish_reason": first_choice.finish_reason,
        "token_usage": usage_metadata,
    }

    # This is the final object, fully compatible with the rest of LangChain
    langchain_response = AIMessage(
        content=message_content,
        response_metadata=response_metadata
    )

    print(langchain_response)
else:
    print("API call failed or returned no choices.")
```

This approach gives you a robust solution by using the library that works (`openai`) while formatting the output for the library you want to use (`langchain`).

**VedantMadane:**
I've identified the root cause and have a fix ready. The issue is that when using OpenAI-compatible APIs (like vLLM), model_dump() can return 
ull for choices even though the response object has valid choices accessible via direct attribute access.

My fix adds a fallback that extracts choices directly from the response object when model_dump() returns null. Opening a PR shortly.

**mdrxy:**
Putting this complexity into ChatOpenAI to handle a non-OpenAI provider is not warranted. See https://github.com/langchain-ai/langchain/issues/34328.
