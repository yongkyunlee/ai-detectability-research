# AzureChatOpenAI initialization is not backwards compatible - forcing User-Agent header override

**Issue #35521** | State: open | Created: 2026-03-02 | Updated: 2026-03-09
**Author:** appliraz
**Labels:** external

https://github.com/langchain-ai/langchain/blob/11270174aa857c517ea755b4f50a7b23e018e995/libs/partners/openai/langchain_openai/chat_models/azure.py#L676

Upgrading `langchain_openai` from v0.2.2 to v1.1.9 caused our previously working calls to a custom `azure_endpoint` to start returning 403. Debugging the package showed that it forcibly overrides the `User-Agent` header to `"langchain-partner-python-azure-openai"`, which some endpoints (including our custom one) do not accept.

In order to move past this issue - one will have to pass an http_client to AzureChatOpenAI, so it would be used to override the override:

```python
def _inject_user_agent(_request: httpx.Request) -> None:
    _request.headers["User-Agent"] = HTTP_USER_AGENT

_azure_http_client_cached: httpx.Client | None = None

def _get_azure_http_client() -> httpx.Client | None:
    global _azure_http_client_cached

    if _azure_http_client_cached is None:
        _azure_http_client_cached = httpx.Client(event_hooks={"request": [_inject_user_agent]})
    return _azure_http_client_cached
```

This change is not backwards compatible in this sense and it seems like the author desire was to set this header as default, and not override the existing default. Otherwise there should've been at least a note added in the constructor's attribute of 'default_headers' regarding the fact that passing user-agent header won't have effect. 
Also, it was done specifically for the client_params, where if one would inspect the azure instance's default_headers, he will see the user-agent header he set himself, and not the actual one that is used in the http client.

Possible fix would be to check for existence of this header and set it according to the author's request if not set:

```python
              # before line 662
              client_headers = self.default_headers or {}
              client_headers =  {k.lower(): v for k, v in client_headers.items()}
              if 'user-agent' not in client_headers:
                   client_headers['user-agent'] = "langchain-partner-python-azure-openai"
             # line 667
             'default_headers': client_headers
```
