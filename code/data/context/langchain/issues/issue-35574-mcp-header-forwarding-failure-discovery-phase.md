# MCP Header Forwarding Failure (Discovery Phase)

**Issue #35574** | State: open | Created: 2026-03-05 | Updated: 2026-03-09
**Author:** amelmgn
**Labels:** bug, langchain, external

### Checked other resources

- [x] This is a bug, not a usage question.
- [x] I added a clear and descriptive title that summarizes this issue.
- [x] I used the GitHub search to find a similar question and didn't find it.
- [x] I am sure that this is a bug in LangChain rather than my code.
- [x] The bug is not resolved by updating to the latest stable version of LangChain (or the specific integration package).
- [x] This is not related to the langchain-community package.
- [x] I posted a self-contained, minimal, reproducible example. A maintainer can copy it and run it AS IS.

### Package (Required)

- [x] langchain
- [ ] langchain-openai
- [ ] langchain-anthropic
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
- [ ] langchain-openrouter
- [ ] langchain-perplexity
- [ ] langchain-qdrant
- [ ] langchain-xai
- [x] Other / not sure / general

### Related Issues / PRs

_No response_

### Reproduction Steps / Example Code (Python)

```python
1. User adds a remote MCP server in the Agent Builder UI.
2. User provides correct Authorization: Bearer  and Accept: application/json headers (tried via raw string and Workspace Secrets).
3. The Agent Builder attempts to discover tools but fails because the outgoing probe request lacks the required headers.
4. Discovery fails to populate the toolbox, despite the server being accessible via curl and other MCP clients.
```

### Error Message and Stack Trace (if applicable)

```shell
Nginx log:
34.59.65.97 - - [05/Mar/2026:07:44:21 +0000] "GET /mcp HTTP/1.1" 403 102 "-" "python-httpx/0.28.1"                              
34.59.65.97 - - [05/Mar/2026:07:44:22 +0000] "POST /mcp HTTP/1.1" 403 102 "-" "python-httpx/0.28.1"

Response from the MCP server:
{"detail":"Could not fetch tools from MCP server"}
```

### Description

The LangSmith Agent Builder backend proxy does not forward custom static headers (specifically Authorization and Accept) during the initial discovery request to remote MCP servers using the HTTP Streamable transport. This causes servers with strict authentication requirements (like Directus 11.14+) to return a 403 Forbidden, preventing tool discovery.
Internal Workaround Status: The only current workaround is injecting headers at the target server's Nginx/load-balancer layer for the LangSmith egress IP, which is identified as a security risk and fragile.

### System Info

Egress IP: 34.59.65.97
Observed User-Agent: python-httpx/0.28.1
Endpoint: GET /mcp or POST /mcp (Discovery Phase)
Symptom: Nginx logs on the target server confirm that requests from the LangSmith proxy arrive with zero of the custom headers configured in the UI.
Environment: Hosted LangSmith (smith.langchain.com)

## Comments

**SentryNodeAI:**
his is a classic Automation Ops failure mode: header propagation bugs become “invisible” in production without tracing at the boundary. Suggest:

add a minimal repro with a single tool call + deterministic headers
instrument request/response headers at each hop (client → tool server → downstream)
add a regression test to lock the expected forwarding behavior
Check my pinned thread for the full observability runbook.

**amelmgn:**
Thanks for your answer, will try this approach

**JiwaniZakir:**
I have some ideas on how to approach this — can I get assigned?
