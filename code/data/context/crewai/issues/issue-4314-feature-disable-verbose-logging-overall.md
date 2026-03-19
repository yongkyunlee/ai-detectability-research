# [FEATURE] Disable verbose logging overall

**Issue #4314** | State: closed | Created: 2026-01-30 | Updated: 2026-03-12
**Author:** ScarAnd
**Labels:** feature-request, no-issue-activity

### Feature Area

Other (please specify in additional context)

### Is your feature request related to a an existing bug? Please link it here.

I did not found a way to disable all verbose logging in my application. I would like to do that, because my own logs are being overwritten by crewai. I could not find anything related if something like that is even possible yet. I've set `verbose=False` everywhere I could but still get Flow logs in my terminal. 

### Describe the solution you'd like

Either through an env or an overall setting in crewai, I would like to be able to set `verbose=False`. 

### Describe alternatives you've considered

_No response_

### Additional context

_No response_

### Willingness to Contribute

Yes, I'd be happy to submit a pull request

## Comments

**Vidit-Ostwal:**
Verbose should do the job here,  mind sharing the configuration

**greysonlalonde:**
+ what version are you on?

**ScarAnd:**
Thanks for the answer guys! I'm on `1.9.2`

Here's a short snippet of what I have:

```python
# -------------------------------------------------------------
# IMPORTS
# -------------------------------------------------------------

from crewai.flow.flow import Flow, listen, router, start
from crewai import Task, Crew
from config import models, Agent_Provider
import logging
from pydantic import BaseModel

# -------------------------------------------------------------
# DECLARATION AND INITIALIZATION
# -------------------------------------------------------------

logger = logging.getLogger(__name__)

# -------------------------------------------------------------
# MAIN
# -------------------------------------------------------------

class UserQuestion(BaseModel):
    question: str = ""

class RouterFlow(Flow[UserQuestion]):
    tracing = False
    stream = True
    verbose = False

    @start()
    def starter_method(
        self,
    ):
        return {"question": self.state.question}

    @router(starter_method)
    async def starter(self):
        logger.info("[INFO]: Starting router")
        fallback_type = "answer"

        router_agent = Agent_Provider.router_agent

        task = Task(
            agent=router_agent,
            description=self.state.question,
            expected_output="A valid pydantic format",
            output_pydantic=models.RouteQuery,
        )

        crew = Crew(agents=[router_agent], tasks=[task], tracing=False, verbose=False)

        result = await crew.kickoff_async()

        if result.pydantic:
            logger.info("[DEBUG] ROUTER result: %s", result.pydantic.direction)

            logger.info("[INFO]: router done")
            return result.pydantic.direction
        else:
            logger.info("[INFO] FALLBACK decision (%s)", fallback_type)
            logger.info("[INFO]: router done")
            return fallback_type

    @listen("answer")
    async def get_answer(self):
        answer_agent = Agent_Provider.summary_agent

        task = Task(
            agent=answer_agent,
            description=self.state.question,
            expected_output="Answer the users question as best as possible",
        )

        crew = Crew(agents=[answer_agent], tasks=[task], tracing=True, verbose=False)
        return await crew.kickoff_async()

        # return await answer_agent.kickoff_async(self.state.question)

        # logger.info("[INFO] answer from LLM received...")
```

**greysonlalonde:**
What does `Agent_Provider` look like?

**ScarAnd:**
It looks like that:

```python
class Agent_Provider:
    """This class stores all needed Agents"""

    router_agent = Agent(
        llm=LLM_Provider.router_llm,
        role="Router agent",
        goal="Return a correct string",
        backstory="You're an agent specific made for a routing purpose.",
        verbose=False,
        tracing=False,
        system_template=PromptConfig.router_system_prompt,
    )
    summary_agent = Agent(
        llm=LLM_Provider.summary_llm,
        verbose=False,
        tracing=False,
        role="Summarize agent",
        goal="You're goal ist to answer or summarize specific topics if the user asks for",
        backstory="You're an agent specific made to summarize a users question or just answer",
    )
    math_llm = Agent(
        llm=LLM_Provider.math_llm,
        verbose=False,
        tracing=False,
        role="Math agent",
        goal="Your goal is to respond to the users math question in a perfect way. Ensure it's right, don't halucinate",
        backstory="You're an agent specific made to answer math questions and solve problems",
    )
```

**Vidit-Ostwal:**
Configuration looks good, mind sharing the logs you are seeing.

**ScarAnd:**
Sure:

```
Flow started with ID: e565b61b-ee2d-4fac-8210-a5847f9c58a4
2026-01-31 11:08:49,818 - crewai.flow.flow - INFO - [_log_flow_event] Flow started with ID: e565b61b-ee2d-4fac-8210-a5847f9c58a4
╭─────────────────────────────────────────────────────────────────────────────────────── 🔄 Flow Method Running ───────────────────────────────────────────────────────────────────────────────────────╮
│                                                                                                                                                                                                      │
│  Method: starter_method                                                                                                                                                                              │
│  Status: Running                                                                                                                                                                                     │
│                                                                                                                                                                                                      │
│                                                                                                                                                                                                      │
╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯

╭────────────────────────────────────────────────────────────────────────────────────── ✅ Flow Method Completed ──────────────────────────────────────────────────────────────────────────────────────╮
│                                                                                                                                                                                                      │
│  Method: starter_method                                                                                                                                                                              │
│  Status: Completed                                                                                                                                                                                   │
│                                                                                                                                                                                                      │
│                                                                                                                                                                                                      │
╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
2026-01-31 11:08:49,819 - flow - INFO - [starter] [INFO]: Starting router

╭─────────────────────────────────────────────────────────────────────────────────────── 🔄 Flow Method Running ───────────────────────────────────────────────────────────────────────────────────────╮
│                                                                                                                                                                                                      │
│  Method: starter                                                                                                                                                                                     │
│  Status: Running                                                                                                                                                                                     │
│                                                                                                                                                                                                      │
│                                                                                                                                                                                                      │
╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯

╭───────────────────────────────────────────────────────────────────────────────────────── 🌊 Flow Execution ──────────────────────────────────────────────────────────────────────────────────────────╮
│                                                                                                                                                                                                      │
│  Starting Flow Execution                                                                                                                                                                             │
│  Name:                                                                                                                                                                                               │
│  RouterFlow                                                                                                                                                                                          │
│  ID:                                                                                                                                                                                                 │
│  e565b61b-ee2d-4fac-8210-a5847f9c58a4                                                                                                                                                                │
│                                                                                                                                                                                                      │
│                                                                                                                                                                                                      │
╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯

╭────────────────────────────────────────────────────────────────────────────────────────── 🌊 Flow Started ───────────────────────────────────────────────────────────────────────────────────────────╮
│                                                                                                                                                                                                      │
│  Flow Started                                                                                                                                                                                        │
│  Name: RouterFlow                                                                                                                                                                                    │
│  ID: e565b61b-ee2d-4fac-8210-a5847f9c58a4                                                                                                                                                            │
│                                                                                                                                                                                                      │
│                                                                                                                                                                                                      │
╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯

2026-01-31 11:08:50,834 - flow - INFO - [starter] [DEBUG] ROUTER result: answer
2026-01-31 11:08:50,834 - flow - INFO - [starter] [INFO]: router done
╭───────────────────────────────────────────────────────────────────────────────────────── ✅ Flow Completion ─────────────────────────────────────────────────────────────────────────────────────────╮
│                                                                                                                                                                                                      │
│  Flow Execution Completed                                                                                                                                                                            │
│  Name:                                                                                                                                                                                               │
│  RouterFlow                                                                                                                                                                                          │
│  ID:                                                                                                                                                                                                 │
│  e565b61b-ee2d-4fac-8210-a5847f9c58a4                                                                                                                                                                │
│                                                                                                                                                                                                      │
│                                                                                                                                                                                                      │
╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
```

**Vidit-Ostwal:**
I honestly wasn't able to find anything suspicious.
Can you try this once to double check

import this at this very top
```
from crewai.events.event_listener import EventListener
event_listener = EventListener()
print(event_listener.formatter.verbose)
```

```
YOUR CODE
```

```
print(event_listener.formatter.verbose)
```

Share the outputs

**ScarAnd:**
Sure. This is my output. It's `True` at the beginning and `False` at the end. But I'm still seeing all the logs haha

```
True
True
INFO:     Started server process [61550]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
2026-01-31 15:14:57,467 - root - INFO - [stream_v2_query] Received streaming query: Hello
INFO:     127.0.0.1:64333 - "POST /stream HTTP/1.1" 200 OK
Flow started with ID: 67f72847-c1ef-4849-9a51-95a79ab2f9e5
2026-01-31 15:14:57,474 - crewai.flow.flow - INFO - [_log_flow_event] Flow started with ID: 67f72847-c1ef-4849-9a51-95a79ab2f9e5
╭─────────────────────────────────────────────────────────────────────────────────────── 🔄 Flow Method Running ───────────────────────────────────────────────────────────────────────────────────────╮
│                                                                                                                                                                                                      │
│  Method: starter_method                                                                                                                                                                              │
│  Status: Running                                                                                                                                                                                     │
│                                                                                                                                                                                                      │
│                                                                                                                                                                                                      │
╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯

╭────────────────────────────────────────────────────────────────────────────────────── ✅ Flow Method Completed ──────────────────────────────────────────────────────────────────────────────────────╮
│                                                                                                                                                                                                      │
│  Method: starter_method                                                                                                                                                                              │
│  Status: Completed                                                                                                                                                                                   │
│                                                                                                                                                                                                      │
│                                                                                                                                                                                                      │
╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯
2026-01-31 15:14:57,475 - flow - INFO - [starter] [INFO]: Starting router

╭─────────────────────────────────────────────────────────────────────────────────────── 🔄 Flow Method Running ───────────────────────────────────────────────────────────────────────────────────────╮
│                                                                                                                                                                                                      │
│  Method: starter                                                                                                                                                                                     │
│  Status: Running                                                                                                                                                                                     │
│                                                                                                                                                                                                      │
│                                                                                                                                                                                                      │
╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯

╭───────────────────────────────────────────────────────────────────────────────────────── 🌊 Flow Execution ──────────────────────────────────────────────────────────────────────────────────────────╮
│                                                                                                                                                                                                      │
│  Starting Flow Execution                                                                                                                                                                             │
│  Name:                                                                                                                                                                                               │
│  RouterFlow                                                                                                                                                                                          │
│  ID:                                                                                                                                                                                                 │
│  67f72847-c1ef-4849-9a51-95a79ab2f9e5                                                                                                                                                                │
│                                                                                                                                                                                                      │
│                                                                                                                                                                                                      │
╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯

╭────────────────────────────────────────────────────────────────────────────────────────── 🌊 Flow Started ───────────────────────────────────────────────────────────────────────────────────────────╮
│                                                                                                                                                                                                      │
│  Flow Started                                                                                                                                                                                        │
│  Name: RouterFlow                                                                                                                                                                                    │
│  ID: 67f72847-c1ef-4849-9a51-95a79ab2f9e5                                                                                                                                                            │
│                                                                                                                                                                                                      │
│                                                                                                                                                                                                      │
╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯

2026-01-31 15:14:58,220 - flow - INFO - [starter] [DEBUG] ROUTER result: answer
2026-01-31 15:14:58,220 - flow - INFO - [starter] [INFO]: router done
╭───────────────────────────────────────────────────────────────────────────────────────── ✅ Flow Completion ─────────────────────────────────────────────────────────────────────────────────────────╮
│                                                                                                                                                                                                      │
│  Flow Execution Completed                                                                                                                                                                            │
│  Name:                                                                                                                                                                                               │
│  RouterFlow                                                                                                                                                                                          │
│  ID:                                                                                                                                                                                                 │
│  67f72847-c1ef-4849-9a51-95a79ab2f9e5                                                                                                                                                                │
│                                                                                                                                                                                                      │
│                                                                                                                                                                                                      │
╰──────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────────╯

2026-01-31 15:15:00,912 - root - INFO - [generate_stream] [DONE] Hello! How can I help you today?
2026-01-31 15:15:00,912 - root - INFO - [generate_stream] [TEST]: False
```

**Vidit-Ostwal:**
Can't see the second False can you do this once

I honestly wasn't able to find anything suspicious.
Can you try this once to double check

import this at this very top

```
from crewai.events.event_listener import EventListener
event_listener = EventListener()
print(event_listener.formatter.verbose)
event_listener.formatter.verbose = False
```

`YOUR CODE`

`print(event_listener.formatter.verbose)`
