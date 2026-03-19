# [BUG] Conflicting versions for openai when using OpenLit

**Issue #4270** | State: closed | Created: 2026-01-23 | Updated: 2026-03-12
**Author:** titimoby
**Labels:** bug, no-issue-activity

### Description

Currently using crewai == 1.8.1
Following the [OpenLit integration](https://docs.crewai.com/en/observability/openlit) documentation, I added the package openlit to my project.
The version is openlit==1.36.3

The issue is that crewai depends on openai>=1.83.0,= 1.92.0

Running a Crew with OpenLit activated results in a message:
```Overriding of current TracerProvider is not allowed
DependencyConflict: requested: "openai >= 1.92.0" but found: "openai 1.83.0"
OpenLIT metrics setup failed. Metrics will not be available: 'NoneType' object has no attribute 'create_histogram'
DependencyConflict: requested: "openai >= 1.92.0" but found: "openai 1.83.0"```

And then a bunch of:
```Attempting to instrument while already instrumented
Attempting to instrument while already instrumented
Attempting to instrument while already instrumented```

The Crew executes but all logs are still pure CrewAI logs and traces.

### Steps to Reproduce

Follow the [OpenLit integration](https://docs.crewai.com/en/observability/openlit) documentation:
- pip install openlit
- add the activation code in the project
- run the project

### Expected behavior

CrewAI Crew runs and OpenLit collect the telemetry information.

### Screenshots/Code snippets

import openlit
openlit.init(otlp_endpoint="http://127.0.0.1:4318")
openlit.init(disable_metrics=True)

...
crew.kickoff(inputs={"customer_query": customer_query})

### Operating System

Other (specify in additional context)

### Python Version

3.10

### crewAI Version

1.8.1

### crewAI Tools Version

1.8.1

### Virtual Environment

Venv

### Evidence

```❯ uv run 03-MultiAgentsCrew.py
Overriding of current TracerProvider is not allowed
DependencyConflict: requested: "openai >= 1.92.0" but found: "openai 1.83.0"
OpenLIT metrics setup failed. Metrics will not be available: 'NoneType' object has no attribute 'create_histogram'
DependencyConflict: requested: "openai >= 1.92.0" but found: "openai 1.83.0"
Attempting to instrument while already instrumented
Attempting to instrument while already instrumented
Attempting to instrument while already instrumented
Attempting to instrument while already instrumented
Attempting to instrument while already instrumented
Attempting to instrument while already instrumented
Attempting to instrument while already instrumented
Attempting to instrument while already instrumented
Attempting to instrument while already instrumented```

### Possible Solution

a fix needs to be done in dependencies

### Additional context

macOS Sequoia
Python 3.13

## Comments

**joaquinariasco-lab:**
Hi @titimoby,

You’re hitting a real and common problem in today’s agent ecosystem: tight dependency coupling between agent frameworks and observability tooling.

What you’re seeing is essentially:
- CrewAI pins openai to a narrow range
- OpenLit moves faster and requires a newer SDK
- Result: partial execution works, but instrumentation breaks and you get double-instrumentation warnings

Even when it “runs”, the observability layer is effectively unreliable.

One thing we’re experimenting with in a separate open repo is decoupling agent coordination and execution from framework-specific internals. Instead of instrumenting inside the agent framework, agents expose a minimal HTTP interface (receive_message, run_task) and observability can live outside the agent runtime entirely.

This avoids:
- SDK version lock-in
- Double instrumentation
- Framework-specific tracing assumptions

If you’re interested in experimenting, here’s the repo:

You can run two agents locally in minutes and observe interactions without touching CrewAI / LangChain internals at all.

Totally experimental, but your issue is exactly the kind of real-world pain point this approach is trying to explore.

Happy to hear your thoughts if you try it.

Joaquin

**github-actions[bot]:**
This issue is stale because it has been open for 30 days with no activity. Remove stale label or comment or this will be closed in 5 days.

**github-actions[bot]:**
This issue was closed because it has been stalled for 5 days with no activity.
