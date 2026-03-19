# HuggingFaceEndpointEmbeddings fails with self-hosted inference server and huggingface-hub==0.28.1

**Issue #29787** | State: open | Created: 2025-02-13 | Updated: 2026-03-07
**Author:** shkarupa-alex
**Labels:** bug, huggingface, external

### Checked other resources

- [x] I added a very descriptive title to this issue.
- [x] I searched the LangChain documentation with the integrated search.
- [x] I used the GitHub search to find a similar question and didn't find it.
- [x] I am sure that this is a bug in LangChain rather than my code.
- [x] The bug is not resolved by updating to the latest stable version of LangChain (or the specific integration package).

### Example Code

The following code works well with `huggingface-hub==0.27.0`, but fails with the latest one (0.28.1)

```python
from langchain_huggingface.embeddings import HuggingFaceEndpointEmbeddings

embedding_url = "http://localhost:8081" # this a docker container with ghcr.io/huggingface/text-embeddings-inference:cpu-sha-13dddbd

embeddings = HuggingFaceEndpointEmbeddings(model=embedding_url)
print(embeddings.embed_documents(["dummy_text"]))
```

### Error Message and Stack Trace (if applicable)

```python
[/Users/alex/.pyenv/versions/3.11.2/lib/python3.11/site-packages/huggingface_hub/utils/_deprecation.py:131](http://localhost:8888/Users/alex/.pyenv/versions/3.11.2/lib/python3.11/site-packages/huggingface_hub/utils/_deprecation.py#line=130): FutureWarning: 'post' (from 'huggingface_hub.inference._client') is deprecated and will be removed from version '0.31.0'. Making direct POST requests to the inference server is not supported anymore. Please use task methods instead (e.g. `InferenceClient.chat_completion`). If your use case is not supported, please open an issue in https://github.com/huggingface/huggingface_hub.
  warnings.warn(warning_message, FutureWarning)
---------------------------------------------------------------------------
HTTPError                                 Traceback (most recent call last)
File [~/.pyenv/versions/3.11.2/lib/python3.11/site-packages/huggingface_hub/utils/_http.py:406](http://localhost:8888/~/.pyenv/versions/3.11.2/lib/python3.11/site-packages/huggingface_hub/utils/_http.py#line=405), in hf_raise_for_status(response, endpoint_name)
    405 try:
--> 406     response.raise_for_status()
    407 except HTTPError as e:

File [~/.pyenv/versions/3.11.2/lib/python3.11/site-packages/requests/models.py:1024](http://localhost:8888/~/.pyenv/versions/3.11.2/lib/python3.11/site-packages/requests/models.py#line=1023), in Response.raise_for_status(self)
   1023 if http_error_msg:
-> 1024     raise HTTPError(http_error_msg, response=self)

HTTPError: 429 Client Error: Too Many Requests for url: https://api-inference.huggingface.co/pipeline/feature-extraction/facebook/bart-base

The above exception was the direct cause of the following exception:

HfHubHTTPError                            Traceback (most recent call last)
Cell In[1], line 13
     10 embedding_url = "http://localhost:8081/" # this a docker container with ghcr.io[/huggingface/text-embeddings-inference](http://localhost:8888/huggingface/text-embeddings-inference):cpu-sha-13dddbd
     12 embeddings = HuggingFaceEndpointEmbeddings(model=embedding_url)
---> 13 print(embeddings.embed_documents(["dummy_text"]))

File [~/.pyenv/versions/3.11.2/lib/python3.11/site-packages/langchain_huggingface/embeddings/huggingface_endpoint.py:112](http://localhost:8888/~/.pyenv/versions/3.11.2/lib/python3.11/site-packages/langchain_huggingface/embeddings/huggingface_endpoint.py#line=111), in HuggingFaceEndpointEmbeddings.embed_documents(self, texts)
    110 _model_kwargs = self.model_kwargs or {}
    111 #  api doc: https://huggingface.github.io/text-embeddings-inference/#/Text%20Embeddings%20Inference/embed
--> 112 responses = self.client.post(
    113     json={"inputs": texts, **_model_kwargs}, task=self.task
    114 )
    115 return json.loads(responses.decode())

File ~/.pyenv/versions/3.11.2/lib/python3.11/site-packages/huggingface_hub/utils/_deprecation.py:132, in _deprecate_method.._inner_deprecate_method..inner_f(*args, **kwargs)
    130     warning_message += " " + message
    131 warnings.warn(warning_message, FutureWarning)
--> 132 return f(*args, **kwargs)

File [~/.pyenv/versions/3.11.2/lib/python3.11/site-packages/huggingface_hub/inference/_client.py:272](http://localhost:8888/~/.pyenv/versions/3.11.2/lib/python3.11/site-packages/huggingface_hub/inference/_client.py#line=271), in InferenceClient.post(self, json, data, model, task, stream)
    270 url = provider_helper.build_url(provider_helper.map_model(model))
    271 headers = provider_helper.prepare_headers(headers=self.headers, api_key=self.token)
--> 272 return self._inner_post(
    273     request_parameters=RequestParameters(
    274         url=url,
    275         task=task or "unknown",
    276         model=model or "unknown",
    277         json=json,
    278         data=data,
    279         headers=headers,
    280     ),
    281     stream=stream,
    282 )

File [~/.pyenv/versions/3.11.2/lib/python3.11/site-packages/huggingface_hub/inference/_client.py:327](http://localhost:8888/~/.pyenv/versions/3.11.2/lib/python3.11/site-packages/huggingface_hub/inference/_client.py#line=326), in InferenceClient._inner_post(self, request_parameters, stream)
    324         raise InferenceTimeoutError(f"Inference call timed out: {request_parameters.url}") from error  # type: ignore
    326 try:
--> 327     hf_raise_for_status(response)
    328     return response.iter_lines() if stream else response.content
    329 except HTTPError as error:

File [~/.pyenv/versions/3.11.2/lib/python3.11/site-packages/huggingface_hub/utils/_http.py:477](http://localhost:8888/~/.pyenv/versions/3.11.2/lib/python3.11/site-packages/huggingface_hub/utils/_http.py#line=476), in hf_raise_for_status(response, endpoint_name)
    473     raise _format(HfHubHTTPError, message, response) from e
    475 # Convert `HTTPError` into a `HfHubHTTPError` to display request information
    476 # as well (request id and[/or](http://localhost:8888/or) server error message)
--> 477 raise _format(HfHubHTTPError, str(e), response) from e

HfHubHTTPError: 429 Client Error: Too Many Requests for url: https://api-inference.huggingface.co/pipeline/feature-extraction/facebook/bart-base (Request ID: RzoUHJ)

TooManyRequests: Please log in or use a HF access token
```

### Description

`HuggingFaceEndpointEmbeddings` uses `InferenceClient` from `huggingface_hub`.
But since the last update, it always send embedding requests to HF and not in my local embedding server.

### System Info

System Information
------------------
> OS:  Darwin
> OS Version:  Darwin Kernel Version 23.5.0: Wed May  1 20:09:52 PDT 2024; root:xnu-10063.121.3~5/RELEASE_X86_64
> Python Version:  3.11.2 (main, Apr 17 2023, 23:33:17) [Clang 14.0.3 (clang-1403.0.22.14.1)]

Package Information
-------------------
> langchain_core: 0.3.35
> langchain: 0.3.18
> langchain_community: 0.3.16
> langsmith: 0.3.3
> langchain_experimental: 0.3.4
> langchain_huggingface: 0.1.2
> langchain_ollama: 0.2.3
> langchain_openai: 0.3.3
> langchain_qdrant: 0.2.0
> langchain_text_splitters: 0.3.6
> langgraph_sdk: 0.1.51

Optional packages not installed
-------------------------------
> langserve

Other Dependencies
------------------
> aiohttp: 3.8.4
> aiohttp=3.8.3: Installed. No version info available.
> async-timeout=4.0.0;: Installed. No version info available.
> dataclasses-json: 0.6.7
> fastembed: Installed. No version info available.
> httpx: 0.27.2
> httpx-sse: 0.4.0
> huggingface-hub: 0.28.1
> jsonpatch=1.33: Installed. No version info available.
> langchain-anthropic;: Installed. No version info available.
> langchain-aws;: Installed. No version info available.
> langchain-cohere;: Installed. No version info available.
> langchain-community;: Installed. No version info available.
> langchain-core=0.3.34: Installed. No version info available.
> langchain-deepseek;: Installed. No version info available.
> langchain-fireworks;: Installed. No version info available.
> langchain-google-genai;: Installed. No version info available.
> langchain-google-vertexai;: Installed. No version info available.
> langchain-groq;: Installed. No version info available.
> langchain-huggingface;: Installed. No version info available.
> langchain-mistralai;: Installed. No version info available.
> langchain-ollama;: Installed. No version info available.
> langchain-openai;: Installed. No version info available.
> langchain-text-splitters=0.3.6: Installed. No version info available.
> langchain-together;: Installed. No version info available.
> langsmith-pyo3: Installed. No version info available.
> langsmith=0.1.125: Installed. No version info available.
> langsmith=0.1.17: Installed. No version info available.
> numpy: 1.26.4
> numpy=1.26.4;: Installed. No version info available.
> numpy=1.26.2;: Installed. No version info available.
> ollama: 0.4.7
> openai: 1.61.0
> orjson: 3.10.15
> packaging=23.2: Installed. No version info available.
> pydantic: 2.10.4
> pydantic-settings: 2.7.1
> pydantic=2.5.2;: Installed. No version info available.
> pydantic=2.7.4: Installed. No version info available.
> pydantic=2.7.4;: Installed. No version info available.
> pytest: 7.4.0
> PyYAML: 6.0
> PyYAML>=5.3: Installed. No version info available.
> qdrant-client: 1.13.2
> requests: 2.32.3
> requests-toolbelt: 1.0.0
> requests=2: Installed. No version info available.
> rich: 13.4.2
> sentence-transformers: 3.4.1
> SQLAlchemy: 2.0.38
> SQLAlchemy=1.4: Installed. No version info available.
> tenacity: 8.2.3
> tenacity!=8.4.0,=8.1.0: Installed. No version info available.
> tenacity!=8.4.0,=8.1.0: Installed. No version info available.
> tiktoken: 0.8.0
> tokenizers: 0.21.0
> transformers: 4.48.3
> typing-extensions>=4.7: Installed. No version info available.
> zstandard: 0.23.0

## Comments

**MhdAdnan-404:**
+1

**tomaarsen:**
cc @hanouticelina is this issue familiar to you? I think it could be `huggingface_hub`-related.

- Tom Aarsen

**hanouticelina:**
Hi @shkarupa-alex,
Upgrading `langchain-huggingface` package should fix the issue:
```
pip install -U langchain-huggingface==0.2.0
````

let us know if you still have the same bug after that.
