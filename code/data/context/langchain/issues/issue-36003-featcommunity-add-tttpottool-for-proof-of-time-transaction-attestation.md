# feat(community): add TTTPoTTool for Proof-of-Time transaction attestation

**Issue #36003** | State: closed | Created: 2026-03-17 | Updated: 2026-03-17
**Author:** Heime-Jorgen
**Labels:** external

## Problem

When multiple AI agents compete for the same on-chain resource, ordering disputes arise. There is no existing LangChain tool that provides cryptographic proof of *when* a transaction was submitted — independent of any single time source.

## Proposed Solution

Add two tools to `langchain_classic/tools/`:

- **`TTTPoTTool`** (`ttt_pot_generate`) — Generate a Proof-of-Time attestation before a transaction hits the chain. Uses 4 independent HTTPS time sources (NIST, Apple, Google, Cloudflare) with Byzantine-resistant consensus.
- **`TTTPoTVerifyTool`** (`ttt_pot_verify`) — Verify a PoT attestation after transaction confirms. Detects frontrunning.

## Implementation

- File: `libs/langchain/langchain_classic/tools/ttt/ttt_pot_tool.py`
- Dependencies: `httpx` (already in langchain deps)
- Connects to a local/self-hosted OpenTTT MCP server via `TTT_MCP_URL` env var
- IETF Draft: https://datatracker.ietf.org/doc/draft-helmprotocol-tttps/
- Reference implementation: https://github.com/Helm-Protocol/OpenTTT (npm: `openttt@0.2.0`)

## Checklist

- [x] Implements `BaseTool` with both `_run` and `_arun`
- [x] Uses `raise_for_status()` for HTTP error handling
- [x] Env var `TTT_MCP_URL` for server configuration
- [x] No new required dependencies

Would appreciate maintainer review and assignment. Happy to add tests if guidance is given on the test pattern preferred for tool integrations.

## Comments

**Heime-Jorgen:**
Closing duplicate. See #35999.

**Jairooh:**
Thanks for the heads-up — following over at #35999 then.

**Jairooh:**
This is just a closed issue notification for a LangChain community tool addition — nothing to add technically here. No comment needed.

**fairchildadrian9-create:**
Thank you for the heads-up

On Tue, Mar 17, 2026, 6:59 AM Jairooh ***@***.***> wrote:

> *Jairooh* left a comment (langchain-ai/langchain#36003)
> 
>
> This is just a closed issue notification for a LangChain community tool
> addition — nothing to add technically here. No comment needed.
>
> —
> Reply to this email directly, view it on GitHub
> ,
> or unsubscribe
> 
> .
> You are receiving this because you are subscribed to this thread.Message
> ID: ***@***.***>
>
