# Harmony: bad request on gpt-oss-120b and tool calls with `create_react_agent`

**Issue #32885** | State: open | Created: 2025-09-08 | Updated: 2026-03-17
**Author:** d-r-e
**Labels:** bug, integration, openai, external

### Checked other resources

- [x] This is a bug, not a usage question. For questions, please use the LangChain Forum (https://forum.langchain.com/).
- [x] I added a clear and detailed title that summarizes the issue.
- [x] I read what a minimal reproducible example is (https://stackoverflow.com/help/minimal-reproducible-example).
- [x] I included a self-contained, minimal example that demonstrates the issue INCLUDING all the relevant imports. The code run AS IS to reproduce the issue.

### Example Code

```python
from langgraph.prebuilt import create_react_agent
from langchain_openai import ChatOpenAI
from dotenv import load_dotenv
from os import environ
from httpx import Client, AsyncClient
from langchain_core.messages import HumanMessage
from langchain_core.tools import tool
import pprint
import httpx
import logging
from langgraph.checkpoint.memory import InMemorySaver
from threading import get_ident

reasoning = {
    "effort": "high",
    "summary": "auto",
}

model = ChatOpenAI(
    model="openai/gpt-oss-120b",
    api_key=environ.get("TOKEN"),
    streaming=True,
    base_url=environ.get("API_BASE"),
    http_async_client=AsyncClient(),
    http_client=Client(),
    reasoning=reasoning,
    use_responses_api=True,
    output_version="responses/v1", 
)

@tool
def get_cve(cve_id: str) -> dict:
    """
    Get CVE details from the MITRE API using a CVE-ID
    Args:
        cve_id (str): The CVE ID to fetch details for, e.g., "CVE-2024-0018".
    """
    cve_id = cve_id.strip().upper()
    response = httpx.get(
        f"https://cveawg.mitre.org/api/cve/{cve_id}",
    )
    if response.status_code == 200:
        return response.json()
    else:
        logging.error(f"Error fetching CVE {cve_id}: {response.status_code} - {response.text}")
        return {"error": "CVE not found or API error."}
    
max_iterations = 20
recursion_limit = 2 * max_iterations + 1

agent = create_react_agent(
    model,
    [get_cve],
    checkpointer=InMemorySaver(),  
    prompt="You are a helpful assistant.",
)

input = {"messages":[HumanMessage("Describe CVE-2024-1015.")]} 
config = {
    "configurable":{"thread_id":get_ident()},
    "recursion_limit": recursion_limit
}

res = agent.invoke(input, config=config, stream_model="values")

for m in res["messages"]:
    pprint.pprint(m)
```

### Error Message and Stack Trace (if applicable)

```shell
BadRequestError: Error code: 400 - {'error': {'message': 'No call message found for call_82802943873c42629d7e0eb32fb1d505 None', 'type': 'BadRequestError', 'param': None, 'code': 400}}
During task with name 'agent' and id '5b2e69c4-2213-c1f9-dfb3-a03297ecf790'
```

### Description

A `BadRequestError` is raised when invoking an agent using `langgraph.prebuilt.create_react_agent` with a `ChatOpenAI` model (using `use_responses_api=True` and `output_version="responses/v1"`) and a tool. The error occurs during a task named 'agent' and contains the message "No call message found for call_82802943873c42629d7e0eb32fb1d505 None".

The issue seems to be triggered when attempting to use a custom tool within an agent workflow that leverages the new responses API.

### System Info

- Repository: langchain-ai/langgraph

langgraph==0.6.7
langchain-openai==0.3.32
langchain-core==0.3.75

- Model: openai/gpt-oss-120b via ChatOpenAI wrapper (deployed using vLLM stable, with working tool calls through the official openai-agents package.
- Model settings: streaming=True, use_responses_api=True, output_version="responses/v1", reasoning={"effort":"high","summary":"auto"}
- Network/clients: httpx, Client, AsyncClient
- Agent: create_react_agent, checkpointer=InMemorySaver
- OS / Python / package versions: Please specify your Python version and versions of langgraph, langchain, langchain_openai, httpx if possible.

## Comments

**rawathemant246:**
we have to check on this!!

**starchou6:**
Hello, maybe you can try this quick fix
```
model = ChatOpenAI(
    model="openai/gpt-oss-120b",
    api_key=environ.get("TOKEN"),
    streaming=True,
    base_url=environ.get("API_BASE"),
    http_async_client=AsyncClient(),
    http_client=Client(),
    reasoning=reasoning,
    # Remove these two lines:
    # use_responses_api=True,
    # output_version="responses/v1", 
)
```

**OpenSourceGHub:**
The issue is how the agent is trying to resolve and coordinate with the OpenAI API. There's a mismatch between LangGraph's expected state with what the API provides, as it expects a valid call message. If they don't synchronize, then that's where the bug might occur. The code itself is perfectly fine. Since you are using OpenAI's API, try checking if its a sync-issue.

**GilbertKrantz:**
So is responses api not supported with GPT OSS right now?

**OpenSourceGHub:**
It is supported.

**kevincherian:**
are you sure its supported?

**OpenSourceGHub:**
Apologies, but I think they barely support it for the newer models. I've just reviewed that LangGraph's create_react_agent prebuilt does not support the newer OpenAI response API due to compatibility issues, and this code is using that prebuilt.

**OpenSourceGHub:**
That's because LangGraph has not yet been updated to be compatible with the newer APIs. Although you can use OpenAI's older Completions/Chat Completions API, that one is older.

**OpenSourceGHub:**
That's why I recommend syncing LangGraph with the newer OpenAI response API. If you don't sync them properly, then the code will not work due to incompatibility.

**GilbertKrantz:**
> That's why I recommend syncing LangGraph with the newer OpenAI response API. If you don't sync them properly, then the code will not work due to incompatibility. 

HI, I’ve tested the setup using a basic ChatOpenAI with simple tool bindings, and the issue still persists. For context, I’m hosting GPT-OSS 20B via vLLM. Is this also due to the sync issues? If it is do you have any references for fixing it.

Thank you beforehand,
