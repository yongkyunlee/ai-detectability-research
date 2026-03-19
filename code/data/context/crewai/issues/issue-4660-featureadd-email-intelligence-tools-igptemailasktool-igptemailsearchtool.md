# [FEATURE]Add email intelligence tools: IgptEmailAskTool + IgptEmailSearchTool

**Issue #4660** | State: open | Created: 2026-03-01 | Updated: 2026-03-18
**Author:** Sammy-spk
**Labels:** feature-request

### Feature Area

Integration with external tools

### Is your feature request related to a an existing bug? Please link it here.

NA

### Describe the solution you'd like

## Problem

CrewAI agents that operate on email (support triage, sales follow-ups, executive assistants) typically get raw message text via Gmail APIs or third-party connectors. That's enough to fetch emails, but not enough to reason about decisions, commitments, unresolved threads, tone changes, and repeated patterns across multiple threads.

## Proposal

Add two optional tools implemented using CrewAI's `BaseTool` + `args_schema` pattern:

**`IgptEmailAskTool`** — Natural-language Q&A over a user's full email history

- **Use cases:** "What are the open commitments with X?", "What did we decide about pricing?", "Summarize unresolved threads this week."
- **Output:** text or JSON; includes citations back to source messages (thread/message identifiers, excerpt + timestamp for each citation).

**`IgptEmailSearchTool`** — Keyword + semantic search across threads with date filters

- **Use cases:** gather context before drafting, find prior discussions, trace a topic over time.

## Implementation sketch

```python
import os
from typing import Type
from crewai.tools import BaseTool
from pydantic import BaseModel, Field

class IgptEmailAskInput(BaseModel):
    question: str = Field(..., description="Natural language question about email history")
    output_format: str = Field(default="text", description="text | json | schema")

class IgptEmailAskTool(BaseTool):
    name: str = "iGPT Email Ask"
    description: str = (
        "Ask questions over a user's email history and get answers with citations "
        "(useful for decisions, commitments, action items, sentiment, and open loops)."
    )
    args_schema: Type[BaseModel] = IgptEmailAskInput

    def _run(self, question: str, output_format: str = "text") -> str:
        from igptai import IGPT
        igpt = IGPT(
            api_key=os.environ["IGPT_API_KEY"],
            user=os.environ["IGPT_API_USER"],
        )
        return str(igpt.recall.ask(
            input=question,
            quality="cef-1-normal",
            output_format=output_format
        ))
```

## Dependencies / configuration

- **Python SDK:** `igptai` (MIT licensed) — https://pypi.org/project/igptai/
- **Env vars:** `IGPT_API_KEY`, `IGPT_API_USER`

## Why this belongs as a first-class tool

It's a thin, opt-in wrapper that adds "email intelligence" (cross-thread context + grounded citations) without changing CrewAI core behavior unless a developer installs and uses it.

## Resources

- SDK docs: https://docs.igpt.ai
- Python SDK: https://github.com/igptai/igptai-python
- LangChain integration (reference): https://pypi.org/project/langchain-igpt/

Happy to submit a PR with the full implementation if there's interest.

### Describe alternatives you've considered

The current alternatives for email-aware CrewAI agents are: (1) building a custom Gmail API + RAG pipeline from scratch, which requires handling threading, deduplication, and participant tracking manually, or (2) using raw Gmail connectors that return message text without cross-thread context. Both give agents access to individual emails but not the structured understanding (decisions, commitments, open loops) needed for reliable reasoning.

### Additional context

We've already shipped a LangChain integration (langchain-igpt v1.1.0 on PyPI) using the same BaseTool pattern, and a LlamaIndex integration was merged upstream (PR #20674). Happy to follow whatever conventions the CrewAI tools package uses.

### Willingness to Contribute

Yes, I'd be happy to submit a pull request

## Comments

**A1dityakumar:**
Hii , I would like to work with this issue!
