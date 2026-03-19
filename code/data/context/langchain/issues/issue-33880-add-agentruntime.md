# Add AgentRuntime

**Issue #33880** | State: open | Created: 2025-11-07 | Updated: 2026-03-11
**Author:** sydney-runkle
**Labels:** langchain, feature request, candidate, internal

Enhanced w/ things like agent name, perhaps config, state, etc

Analogous to ToolRuntime, sorta. 

To be spec-ed out further before I take this up. Not looking for contributions at this time.

## Comments

**sydney-runkle:**
Got a start here, but now out of date: https://github.com/langchain-ai/langchain/pull/33689

**ziye122:**
I understand that the core of the AgentRuntime enhancement is to implement modular capabilities like ToolRuntime to manage agent names, configurations, and runtime states. Combined with this direction, there are several design ideas for reference:
1. AgentMetadata class can be abstracted, agent names, static configurations (such as model types, temperature parameters) can be uniformly encapsulated, and serialization and cross-environment reuse can be supported. 2. The runtime state (such as the number of calls, error statistics, and context lifecycle) can be dynamically tracked through the AgentState class, and the state isolation mechanism in multi-agent concurrency scenarios is considered. 3. Refer to the BaseTool interface design of ToolRuntime to define a standardized abstraction layer for AgentRuntime to ensure compatibility and scalability with existing Agent classes.
If the implementation is promoted in the future, the unit tests will be supplemented synchronously (covering core scenarios such as configuration loading and state changes), and a new user guide document will be added in the docs/agents directory. Are these ideas consistent with the expected direction of the maintainer's view of the feature?

**passionworkeer:**
This AgentRuntime sounds like a great addition! Having a unified runtime would simplify agent implementations significantly. Looking forward to seeing this evolve.
