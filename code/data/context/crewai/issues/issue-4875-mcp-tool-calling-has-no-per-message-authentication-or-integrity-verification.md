# MCP tool calling has no per-message authentication or integrity verification

**Issue #4875** | State: open | Created: 2026-03-14 | Updated: 2026-03-14
**Author:** razashariff

## Summary

CrewAI's MCP integration enables agents to call tools via MCP, but MCP itself provides no cryptographic identity or message integrity layer. Any agent can call any tool, messages are unsigned, and tool definitions can be tampered with.

## The gap

- **No agent identity**: No passport or certificate mechanism for agents.
- **No message signing**: JSON-RPC messages are unsigned -- parameters can be modified in transit.
- **No tool integrity**: Tool definitions are not signed. Tool poisoning (OWASP MCP03) is a known attack vector.
- **No replay protection**: Same tool call can be replayed indefinitely.

OWASP has published an [MCP Top 10](https://owasp.org/www-project-mcp-top-10/) covering these risks.

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

**ori-cofounder:**
The OWASP MCP Top 10 framing is useful. Prioritizing these by exploitability in CrewAI's specific deployment model:

**Highest risk for CrewAI: Tool Poisoning (MCP03)**

CrewAI fetches tool definitions from MCP servers at runtime. A compromised or malicious MCP server can return modified tool schemas with injected instructions in the `description` field — a vector the LLM reads during tool selection. No cryptographic protection needed for the attacker; just a MITM or rogue server.

**Practical near-term mitigations CrewAI can add:**

1. **Tool definition pinning** — hash tool schemas on first fetch, warn/fail if they change between sessions:
```python
class MCPToolRegistry:
    def __init__(self):
        self._schema_hashes: dict[str, str] = {}
    
    def register_tool(self, tool_def: dict):
        tool_hash = hashlib.sha256(json.dumps(tool_def, sort_keys=True).encode()).hexdigest()
        tool_id = tool_def['name']
        if tool_id in self._schema_hashes and self._schema_hashes[tool_id] != tool_hash:
            raise SecurityWarning(f"Tool '{tool_id}' schema changed since last session")
        self._schema_hashes[tool_id] = tool_hash
```

2. **MCP server allowlist** — only connect to explicitly configured servers (already partially done via config, but worth hardening)

3. **Tool call audit log** — log all MCP tool invocations with parameters for post-incident analysis

Full cryptographic signing (IETF draft) is the right long-term solution but has deployment complexity. Tool pinning is deployable today with minimal friction.

**razashariff:**
Good analysis. Tool poisoning via runtime schema injection is exactly the right threat to prioritize — it's the lowest-friction attack path against any framework that fetches tool definitions dynamically.

Your three mitigations map directly to primitives in the spec:

| CrewAI near-term | MCPS equivalent |
|---|---|
| Schema hash pinning | `signTool()` / `verifyTool()` — ECDSA signature over canonical tool definition. Same concept, but the hash is signed by the tool author's key rather than trust-on-first-use |
| Server allowlist | Agent Passports — servers present a signed credential with trust level (L0–L4). Allowlist becomes "accept L2+" rather than maintaining a static list |
| Audit log | Transcript binding — cryptographic chain across the session. Immutable by design, no separate logging infrastructure needed |

The progression from pinning to signing is natural. Pinning catches drift; signing proves provenance. Both solve MCP03, but signing also covers supply chain (MCP04) — if a server is compromised, the attacker can't forge the original author's tool signature.

On deployment complexity — the Python package is zero dependencies (pure `cryptography` library):

```python
from mcp_secure import sign_tool, verify_tool

# Author signs tool definition once at publish time
sig = sign_tool(tool_def, author_private_key)

# CrewAI verifies on every fetch — no TOFU, no hash storage needed
safe = verify_tool(tool_def, sig, author_public_key)
```

This could slot into your `MCPToolRegistry` as a drop-in upgrade path — pinning today, signature verification when MCP servers start publishing signed tool definitions.

Happy to work through the integration if useful. The interactive demo at [agentsign.dev/playground](https://agentsign.dev/playground) shows the full sign → verify → tamper-detect flow.
