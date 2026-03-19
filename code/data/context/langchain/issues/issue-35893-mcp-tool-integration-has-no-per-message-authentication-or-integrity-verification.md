# MCP tool integration has no per-message authentication or integrity verification

**Issue #35893** | State: open | Created: 2026-03-14 | Updated: 2026-03-14
**Author:** razashariff
**Labels:** external

## Summary

LangChain's MCP tool integration enables agents to call tools via MCP, but MCP itself provides no cryptographic identity or message integrity layer. Any agent can call any tool, messages are unsigned, and tool definitions can be tampered with.

## The gap

- **No agent identity**: No passport or certificate mechanism for agents calling MCP tools.
- **No message signing**: JSON-RPC messages are unsigned -- parameters can be modified in transit.
- **No tool integrity**: Tool definitions from `tools/list` are not signed. Tool poisoning (OWASP MCP03) is a known attack vector.
- **No replay protection**: Same tool call can be replayed indefinitely.

OWASP has published an [MCP Top 10](https://owasp.org/www-project-mcp-top-10/) covering these risks. CVEs with CVSS 9.6 have been filed against MCP implementations.

## Existing work

An IETF Internet-Draft has been published to address this:

- **IETF Datatracker**: https://datatracker.ietf.org/doc/draft-sharif-mcps-secure-mcp/
- **Reference implementations**: [npm](https://www.npmjs.com/package/mcp-secure) / [PyPI](https://pypi.org/project/mcp-secure/) (zero dependencies)
- **Interactive demo**: https://agentsign.dev/playground

The spec adds agent passports (ECDSA P-256), per-message signing, tool definition signatures, and nonce-based replay protection -- fully backward-compatible with current MCP.

Happy to discuss integration approaches.

## Comments

**razashariff:**
**Update: Real-world MCP security incidents now documented**

Since filing this issue, multiple real-world MCP security incidents have been publicly disclosed:

- **CVE-2025-6514** (CVSS 9.6) -- mcp-remote RCE via crafted OAuth URL. 437,000+ downloads affected.
- **CVE-2025-49596** (CVSS 9.4) -- Anthropic MCP Inspector unauthenticated RCE. 38,000 weekly downloads.
- **CVE-2025-68145/68143/68144** -- Anthropic mcp-server-git chain. Full RCE via path bypass + git_init + argument injection.
- **Smithery.ai breach** -- Path traversal exposed 3,243 MCP servers and thousands of API keys.
- **Asana cross-tenant leak** -- MCP server bug exposed ~1,000 customers' data across organisations for 34 days.
- **postmark-mcp backdoor** -- First malicious MCP server in the wild. BCC'd every email to attacker.

The full specification for addressing these at the protocol level is now an IETF Internet-Draft:
https://datatracker.ietf.org/doc/draft-sharif-mcps-secure-mcp/

Interactive playground (no install): https://agentsign.dev/playground

**razashariff:**
**Update: CrewAI co-founder endorses IETF draft as long-term solution**

CrewAI's co-founder has independently reviewed the MCP security threat model and prioritised Tool Poisoning (MCP03) as the highest-risk vector for agent frameworks that fetch tool definitions at runtime.

His assessment:

> "Full cryptographic signing (IETF draft) is the right long-term solution"

CrewAI is implementing near-term tool definition pinning (schema hashing on first fetch) as a stepping stone, with the full cryptographic signing spec as the target architecture.

Reference: https://github.com/crewAIInc/crewAI/issues/4875#issuecomment-2826498498

The specification and implementations are available:

- **IETF Internet-Draft**: https://datatracker.ietf.org/doc/draft-sharif-mcps-secure-mcp/
- **Python package** (zero deps): https://pypi.org/project/mcp-secure/
- **npm package** (zero deps): https://www.npmjs.com/package/mcp-secure
- **Interactive playground**: https://agentsign.dev/playground
- **Contact**: raza.sharif@outlook.com
