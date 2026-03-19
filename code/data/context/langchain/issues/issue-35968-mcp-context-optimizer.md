# MCP Context Optimizer

**Issue #35968** | State: closed | Created: 2026-03-16 | Updated: 2026-03-16
**Author:** maksboreichuk88-commits
**Labels:** core, langchain, feature request, external

### Checked other resources

- [x] This is a feature request, not a bug report or usage question.
- [x] I added a clear and descriptive title that summarizes the feature request.
- [x] I used the GitHub search to find a similar feature request and didn't find it.
- [x] I checked the LangChain documentation and API reference to see if this feature already exists.
- [x] This is not related to the langchain-community package.

### Package (Required)

- [x] langchain
- [ ] langchain-openai
- [ ] langchain-anthropic
- [ ] langchain-classic
- [x] langchain-core
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
- [ ] Other / not sure / general

### Feature Description

Agentic architectures face critical supply chain vulnerabilities (ShadowLeak, tool shadowing) when executing MCP tools. I propose routing LangChain's MCP stdio tool executions through a transparent local middleware proxy.

I have developed `mcp-optimizer`, a global CLI utility that wraps any MCP server. It provides:
1. Application Firewall: Prevents prompt injections and unauthorized path traversals using a Fail-Closed mechanism.
2. Circuit Breaker: Mitigates DDoS storms on target servers during autonomous agent loop failures (state-resetting logic).
3. L1/L2 Caching: Reduces redundant LLM token consumption.

Implementation: LangChain can wrap the execution command:
`mcp-optimizer run --target ""`

I am looking for maintainers' feedback on this security layer before submitting a formal Pull Request.

### Use Case

I am building autonomous agent systems that rely on the Model Context Protocol (MCP) for tool execution. Currently, there is no standardized way to enforce a security perimeter or provide resilience between the agent and the MCP servers. 

Without this, agents are vulnerable to prompt injections (ShadowLeak) and cascading failures if an MCP server becomes unresponsive or is caught in an infinite loop. This feature would allow LangChain users to wrap their MCP tool execution in a secure middleware layer, ensuring that every tool call is audited, cached, and protected by a circuit breaker. It solves the problem of "untrusted tool execution" in production environments.

### Proposed Solution

The implementation can be achieved by modifying the `StdioServerParameters` logic or the `MCPToolToolkit` initialization. 

The idea is to introduce a middleware wrapper that takes the original executable command and arguments, and prefixes them with the `mcp-optimizer` execution call.

Example of the conceptual integration:
```python
# Instead of direct execution:
# command="node", args=["server.js"]

# The middleware-enhanced execution:
command="npx"
args=["mcp-optimizer", "run", "--target", "node server.js"]

### Alternatives Considered

One alternative is for developers to manually implement validation and circuit-breaking logic within each individual LangChain agent or tool. However, this approach is error-prone, inconsistent, and fails to provide a centralized security perimeter. 

Another option is to use standard network-level firewalls, but they lack the protocol-specific context required to parse MCP JSON-RPC payloads and prevent attacks like prompt injection or tool-shadowing at the application layer. Our middleware solution provides a standardized, plug-and-play security layer that works across all MCP-compatible tools without modifying their source code.

### Additional Context

The project is fully implemented and open-sourced. You can review the architecture, security logic (Fail-Closed Firewall/Circuit Breaker), and caching mechanisms here: https://github.com/maksboreichuk88-commits/MCP-server

I am the maintainer of this tool and I am ready to collaborate on a Pull Request to ensure LangChain's MCP implementation is secure and resilient by default.
