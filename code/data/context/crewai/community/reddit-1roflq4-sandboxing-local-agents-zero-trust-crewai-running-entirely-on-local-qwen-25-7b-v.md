# Sandboxing local agents: Zero-trust CrewAI running entirely on Local Qwen 2.5 7B via Ollama (no cloud APIs)

**r/ollama** | Score: 4 | Comments: 4 | Date: 2026-03-08
**Author:** Aggressive_Bed7113
**URL:** https://www.reddit.com/r/ollama/comments/1roflq4/sandboxing_local_agents_zerotrust_crewai_running/

The biggest problem with multi-agent frameworks right now is that agents share ambient OS permissions by default.

To fix this, here is an architectural approach that adds two hard checkpoints to the local execution loop to sandbox the agents:

**1. Pre-execution gate:** A local Rust sidecar evaluates every tool call against a declarative YAML policy (see attached screenshot) in `&lt;2ms`. The scraper is allowed to hit Amazon, but it physically cannot touch the host filesystem. The analyst can write reports, but it is blocked from opening a browser.

**2. Post-execution verification:** Replacing the "LLM-as-judge" guessing game with deterministic DOM assertions after the tool runs.

**3. Chain Delegation with Multi-Scope Mandates**

Instead of giving each agent its own permissions, the orchestrator gets a single signed mandate covering multiple scopes, then delegates subsets to child agents:

    POST /v1/authorize (orchestrator)
      scopes: [
        {action: "browser.*", resource: "https://www.amazon.com/*"},
        {action: "fs.*", resource: "**/workspace/data/**"}
      ]
      → mandate_token: eyJhbGci... (depth=0)
    
    POST /v1/delegate (to scraper)
      parent_mandate_token: eyJhbGci...
      action: "browser.*"
      resource: "https://www.amazon.com/*"
      → derived mandate (depth=1, TTL capped to parent)
    
    POST /v1/delegate (to analyst)
      parent_mandate_token: eyJhbGci...
      action: "fs.write"
      resource: "**/workspace/data/**"
      → derived mandate (depth=1)

Actual output from the local Qwen 2.5 run:

    Verification:
      exists(#productTitle): PASS
      exists(.a-price): PASS ($549.99)
      dom_contains('In Stock'): PASS

Here is the open-source implementation/demo of this architecture: [https://github.com/PredicateSystems/predicate-secure-crewai-demo](https://github.com/PredicateSystems/predicate-secure-crewai-demo)

Curious how everyone else is handling permission boundaries between local agents? Are you just spinning up heavy Docker containers for every agent, relying on system prompts, or something else?
