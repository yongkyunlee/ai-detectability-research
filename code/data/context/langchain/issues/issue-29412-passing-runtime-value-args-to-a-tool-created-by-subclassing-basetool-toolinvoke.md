# Passing runtime value args to a tool created by subclassing BaseTool: tool.invoke doesn't see the runtime arg even when provided

**Issue #29412** | State: closed | Created: 2025-01-24 | Updated: 2026-03-07
**Author:** shruthiR-fauna
**Labels:** bug, external

### Discussed in https://github.com/langchain-ai/langchain/discussions/29411

Originally posted by **shruthiR-fauna** January 24, 2025
### Checked other resources

- [X] I added a very descriptive title to this question.
- [X] I searched the LangChain documentation with the integrated search.
- [X] I used the GitHub search to find a similar question and didn't find it.

### Commit to Help

- [X] I commit to help with one of those options 👆

### Example Code

```python
from typing import Annotated, Any, Dict, List, Type

from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import chain
from langchain_core.tools import BaseTool, InjectedToolArg
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field


class RobotDogStateManager:
    # Simulated state management for the robot dog
    def __init__(self):
        self.battery_level = 100
        self.current_location = ""


class GoToObjectInput(BaseModel):
    """
    Input for going to an object, visible to the model
    """

    object: str = Field(description="The object to go to")


class GoToObjectTool(BaseTool):
    name: str = "go_to_object"
    description: str = "Instruct the robot dog to go to a specific object"
    args_schema: Type[BaseModel] = GoToObjectInput

    def _run(
        self,
        object: str,
        # Use InjectedToolArg for arguments the model shouldn't see
        robot_state: Annotated[RobotDogStateManager, InjectedToolArg],
        battery_threshold: Annotated[float, InjectedToolArg] = 20.0,
    ) -> str:
        """
        Go to an object, with additional context not visible to the model
        """
        # Check battery level before proceeding
        if robot_state.battery_level  OS:  Linux
> OS Version:  #52~22.04.1-Ubuntu SMP PREEMPT_DYNAMIC Mon Dec  9 15:00:52 UTC 2
> Python Version:  3.10.12 (main, Jan 17 2025, 14:35:34) [GCC 11.4.0]

Package Information
-------------------
> langchain_core: 0.3.10
> langchain: 0.3.3
> langchain_community: 0.3.2
> langsmith: 0.1.133
> langchain_fireworks: 0.2.1
> langchain_google_genai: 2.0.1
> langchain_groq: 0.2.0
> langchain_ollama: 0.2.0
> langchain_openai: 0.2.2
> langchain_text_splitters: 0.3.0

Optional packages not installed
-------------------------------
> langgraph
> langserve

Other Dependencies
------------------
> aiohttp: 3.10.9
> async-timeout: 4.0.3
> dataclasses-json: 0.6.7
> fireworks-ai: 0.15.4
> google-generativeai: 0.8.3
> groq: 0.11.0
> httpx: 0.27.2
> jsonpatch: 1.33
> numpy: 1.26.4
> ollama: 0.3.3
> openai: 1.51.2
> orjson: 3.10.7
> packaging: 24.1
> pillow: 11.0.0
> pydantic: 2.9.2
> pydantic-settings: 2.5.2
> PyYAML: 6.0.2
> requests: 2.32.3
> requests-toolbelt: 1.0.0
> SQLAlchemy: 2.0.35
> tenacity: 8.5.0
> tiktoken: 0.8.0
> typing-extensions: 4.12.2

## Comments

**dosubot[bot]:**
Hi, @shruthiR-fauna. I'm [Dosu](https://dosu.dev), and I'm helping the LangChain team manage their backlog. I'm marking this issue as stale.

**Issue Summary**
- Problem with passing runtime arguments to a tool subclassed from `BaseTool`.
- `tool.invoke` method fails to recognize the provided runtime argument.
- Example code was shared to demonstrate the issue.
- No further comments or activity have been made on this issue.

**Next Steps**
- Please confirm if this issue is still relevant to the latest version of the LangChain repository. If so, you can keep the discussion open by commenting here.
- Otherwise, this issue will be automatically closed in 7 days.

Thank you for your understanding and contribution!
