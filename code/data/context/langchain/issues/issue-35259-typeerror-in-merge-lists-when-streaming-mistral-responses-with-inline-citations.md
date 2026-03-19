# TypeError in merge_lists when streaming Mistral responses with inline citations

**Issue #35259** | State: open | Created: 2026-02-16 | Updated: 2026-03-14
**Author:** GhaziBenDahmane
**Labels:** bug, langchain, mistralai, external

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
- [x] langchain-mistralai
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
from langchain_core.utils._merge import merge_lists

merged = [
    "start answer...",
    {"type": "reference", "index": 0, "reference_ids": ["iKcb2CAQ7"]},
    "other answer..."
]

# Another reference to merge (from streaming chunk)
other = [{"type": "reference", "index": 0, "reference_ids": ["DGqzzmqc3"]}]

# This raises TypeError
result = merge_lists(merged, other)
```

### Error Message and Stack Trace (if applicable)

```shell
File ".../langchain_core/utils/_merge.py", line 114, in 
      if "index" in e_left and e_left["index"] == e["index"]
                               ~~~~~~~^^^^^^^^^
  TypeError: string indices must be integers, not 'str'
```

### Description

  Model: mistral-medium-2505 (but likely affects any Mistral model returning citations)

  The error occurs when:
  - Using LangGraph's create_react_agent with Mistral
  - Streaming mode enabled
  - Tools like Tavily search that return results the model cites

### System Info

System Information
------------------
> OS:  Linux
> OS Version:  #1 SMP Thu Oct 5 21:02:42 UTC 2023
> Python Version:  3.11.13 (main, Jun 20 2025, 10:35:36) [GCC 11.4.0]

Package Information
-------------------
> langchain_core: 1.2.5
> langchain: 1.2.0
> langchain_community: 0.4.1
> langsmith: 0.3.45
> langchain_classic: 1.0.1
> langchain_elasticsearch: 1.0.0
> langchain_experimental: 0.4.1
> langchain_mcp_adapters: 0.2.1
> langchain_mistralai: 1.1.1
> langchain_openai: 1.1.6
> langchain_tavily: 0.2.16
> langchain_text_splitters: 1.1.0
> langchain_unstructured: 1.0.1
> langgraph_sdk: 0.3.1
> langgraph_supervisor: 0.0.31

Optional packages not installed
-------------------------------
> langserve

Other Dependencies
------------------
> aiohttp: 3.11.14
> dataclasses-json: 0.6.7
> elasticsearch: 8.19.3
> httpx: 0.28.1
> httpx-sse: 0.4.1
> jsonpatch: 1.33
> langgraph: 1.0.5
> mcp: 1.17.0
> numpy: 2.2.6
> openai: 2.14.0
> opentelemetry-api: 1.34.1
> opentelemetry-exporter-otlp-proto-http: 1.34.1
> opentelemetry-sdk: 1.34.1
> orjson: 3.10.18
> packaging: 24.2
> pydantic: 2.11.7
> pydantic-settings: 2.10.1
> pytest: 7.4.0
> pyyaml: 6.0.3
> PyYAML: 6.0.3
> requests: 2.32.5
> requests-toolbelt: 1.0.0
> rich: 14.0.0
> SQLAlchemy: 2.0.41
> sqlalchemy: 2.0.41
> tenacity: 8.2.3
> tiktoken: 0.9.0
> tokenizers: 0.21.2
> typing-extensions: 4.14.0
> unstructured: 0.18.21
> unstructured-client: 0.39.1
> uuid-utils: 0.12.0
> zstandard: 0.23.0

## Comments

**keenborder786:**
@GhaziBenDahmane can you please post the `create_react_agent` code itself, so I can reproduce the bug end to end to better identifity the root cause on my own.

**ccurme:**
@GhaziBenDahmane could you provide a minimal reproducible example?

Here's my attempt, adapted from [Mistral's docs](https://docs.mistral.ai/capabilities/citations):
```python
import json
from langchain.agents import create_agent
from langchain.chat_models import init_chat_model

references = {
  "0": {
    "url": "https://en.wikipedia.org/wiki/2024_Nobel_Peace_Prize",
    "title": "2024 Nobel Peace Prize",
    "snippets": [
      [
        "The 2024 Nobel Peace Prize, an international peace prize established according to Alfred Nobel's will, was awarded to Nihon Hidankyo (the Japan Confederation of A- and H-Bomb Sufferers Organizations), for their activism against nuclear weapons, assisted by victim/survivors (known as Hibakusha) of the atomic bombings of Hiroshima and Nagasaki in 1945.",
        "They will receive the prize at a ceremony on 10 December 2024 at Oslo, Norway."
      ]
    ],
    "description": None,
    "date": "2024-11-26T17:39:55.057454",
    "source": "wikipedia"
  },
  "1": {
    "url": "https://en.wikipedia.org/wiki/Climate_Change",
    "title": "Climate Change",
    "snippets": [
      [
        "Present-day climate change includes both global warming—the ongoing increase in global average temperature—and its wider effects on Earth’s climate system. Climate change in a broader sense also includes previous long-term changes to Earth's climate. The current rise in global temperatures is driven by human activities, especially fossil fuel burning since the Industrial Revolution. Fossil fuel use, deforestation, and some agricultural and industrial practices release greenhouse gases. These gases absorb some of the heat that the Earth radiates after it warms from sunlight, warming the lower atmosphere. Carbon dioxide, the primary gas driving global warming, has increased in concentration by about 50% since the pre-industrial era to levels not seen for millions of years."
      ]
    ],
    "description": None,
    "date": "2024-11-26T17:39:55.057454",
    "source": "wikipedia"
  },
  "2": {
    "url": "https://en.wikipedia.org/wiki/Artificial_Intelligence",
    "title": "Artificial Intelligence",
    "snippets": [
      [
        "Artificial intelligence (AI) refers to the capability of computational systems to perform tasks typically associated with human intelligence, such as learning, reasoning, problem-solving, perception, and decision-making. It is a field of research in computer science that develops and studies methods and software that enable machines to perceive their environment and use learning and intelligence to take actions that maximize their chances of achieving defined goals. Such machines may be called AIs."
      ]
    ],
    "description": None,
    "date": "2024-11-26T17:39:55.057454",
    "source": "wikipedia"
  }
}

def get_information():
    """Use this function to get required information."""
    return json.dumps(references)

agent = create_agent(
    model=init_chat_model("mistralai:mistral-medium-2505", streaming=True),
    tools=[get_information],
    system_prompt="Always cite your sources.",
)

result = agent.invoke(
    {"messages": [{"role": "user", "content": "Who won the Nobel Prize in 2024?"}]}
)

result["messages"][-1]
```

I don't doubt you're running into the TypeError but would be good to reproduce it first. There are tests added in https://github.com/langchain-ai/langchain/pull/35265 but they are passing on master.

**ccurme:**
I'm not sure the final result will look reasonable unless we update Mistral to return `{'type": "text", "text": "..."}` when streaming from this model. Put another way, calling `invoke` and aggregating `stream` should generate the same types of content. Currently, `invoke` generates `list[dict]`, but `stream` generates `str` with interspersed dicts representing references. IMO we should update `stream` to conform to `invoke`.

**giulio-leone:**
I have opened a fix for this in #35623.

**Root cause:** The guard `"index" in e_left` in `merge_lists` performs substring containment when `e_left` is a string (Python's `in` operator on strings), not dict key lookup. When any string element contains `"index"` as a substring, the check passes and `e_left["index"]` fails with `TypeError`.

**Fix:** Add `isinstance(e_left, dict)` before the `"index" in e_left` check to skip non-dict elements.

**alvinttang:**
Hi, I'd like to be assigned to this issue. I have a fix ready in PR #35876 that adds an `isinstance(e_left, dict)` guard before accessing dict keys in `merge_lists`. Happy to address any feedback.
