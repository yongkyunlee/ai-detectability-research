# LangChain Agent Testing Guide Tool (Free)

**HN** | Points: 1 | Comments: 0 | Date: 2026-02-13
**Author:** exordex
**HN URL:** https://news.ycombinator.com/item?id=47004292

Hey HN,
                                                                                                                                      If you're building LangChain agents, you've probably seen them break in creative ways - prompt injection bypassing your chain logic, tools getting called with bad parameters, or cascading failures when an API times out mid-chain.I built Khaos to test these failure modes before production.Example LangChain agent:
  ```python
  from langchain.agents import AgentExecutor, create_openai_functions_agent
  from khaos import khaosagent  @khaosagent(name="research-agent", framework="langgraph")
  def agent(query: str) -> dict:
      executor = AgentExecutor(agent=agent, tools=tools)
      result = executor.invoke({"input": query})
      return {"response": result["output"]}

Test it:
  pip install khaos-agent
  khaos discover
  khaos run research-agent --pack securityKhaos injects:
  - 242+ security attacks - Prompt injection variations that bypass LangChain's prompt templates
  - Tool misuse - Malicious parameters in tool calls (e.g., os.system injection in code execution tools)
  - Chain failures - What happens when your 3rd step in a 5-step chain times out?
  - LLM faults - Rate limits, token overflows, model unavailability  Why this matters for LangChain specifically:

  LangChain's abstraction layers can hide vulnerabilities:
  - Prompt templates can still be injected via tool outputs
  - AgentExecutor doesn't validate tool parameters
  - Chains fail silently or propagate corrupted state
  - ReAct&#x2F;Plan-and-Execute patterns have unique attack surfaces

  Works with LangGraph, LCEL chains, and classic LangChain agents. Auto-instruments your chains to inject faults at each step.

  Repo: https:&#x2F;&#x2F;github.com&#x2F;ExordexLabs&#x2F;khaos-sdk
  Examples: https:&#x2F;&#x2F;github.com&#x2F;ExordexLabs&#x2F;khaos-examples&#x2F;tree&#x2F;master&#x2F;code-execution-agent
