# [Suggestion] Pre-install security scanning for LangChain community tools

**Issue #35827** | State: open | Created: 2026-03-13 | Updated: 2026-03-13
**Author:** elliotllliu
**Labels:** external

## Suggestion: Security scanning for LangChain community tools and integrations

### Problem

LangChain's ecosystem includes hundreds of community-contributed tools, integrations, and agents. Users install and execute these with `Tool`, `StructuredTool`, or via MCP connections — giving third-party code access to prompts, API keys, file systems, and network.

There's currently no standard way to verify the security of a tool before using it in a chain or agent.

### Proposal

[AgentShield](https://github.com/elliotllliu/agent-shield) is an open-source (MIT) static security scanner with 30 rules that detects:

- **Backdoors**: eval(), exec(), dynamic code execution with tainted input
- **Data exfiltration**: reads credentials/sensitive files + sends HTTP requests
- **Prompt injection**: 55+ patterns across 8 languages
- **Python AST taint tracking**: traces data flow through eval, pickle, subprocess, SQL injection, SSTI, path traversal
- **Cross-file attack chains**: multi-step kill chain detection
- **Tool shadowing**: tool name conflicts and override attacks

It runs 100% offline — no data leaves the machine.

```bash
# Scan a tool before using it
npx @elliotllliu/agent-shield scan ./my-langchain-tool/

# JSON output for automation
npx @elliotllliu/agent-shield scan ./tool/ --format json --fail-under 70
```

### Real-World Validation

Scanned 493 Dify plugins (9,862 files, 939K lines) — found 6 high-risk plugins with eval(), exec(), pipe-to-shell, and reverse shell patterns. [Full report](https://github.com/elliotllliu/agent-shield/blob/main/reports/dify-plugins-report.md).

### Possible Integration Points

1. Recommended pre-check in docs for community tools
2. CI step for `langchain-community` contributions
3. Security metadata in tool/integration listings

GitHub: https://github.com/elliotllliu/agent-shield
