# Add TTTPoTTool — Proof-of-Time temporal attestation  for agent transactions

**Issue #35999** | State: closed | Created: 2026-03-17 | Updated: 2026-03-18
**Author:** Heime-Jorgen
**Labels:** core, langchain, feature request, anthropic, huggingface, openai, external

### Checked other resources

- [x] This is a feature request, not a bug report or usage question.
- [x] I added a clear and descriptive title that summarizes the feature request.
- [x] I used the GitHub search to find a similar feature request and didn't find it.
- [x] I checked the LangChain documentation and API reference to see if this feature already exists.
- [x] This is not related to the langchain-community package.

### Package (Required)

- [x] langchain
- [x] langchain-openai
- [x] langchain-anthropic
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
- [x] langchain-huggingface
- [ ] langchain-mistralai
- [ ] langchain-nomic
- [ ] langchain-ollama
- [ ] langchain-openrouter
- [ ] langchain-perplexity
- [ ] langchain-qdrant
- [ ] langchain-xai
- [x] Other / not sure / general

### Feature Description

Add TTTPoTTool and TTTPoTVerifyTool to langchain-community.
These tools wrap the openttt SDK to provide cryptographic 
Proof-of-Time attestation for agent transactions.

from langchain_community.tools.ttt import TTTPoTTool, TTTPoTVerifyTool

pot_tool = TTTPoTTool()
pot = pot_tool.run({"tx_hash": "0x...", "chain_id": 8453})

verify_tool = TTTPoTVerifyTool()
result = verify_tool.run({"pot_hash": pot["potHash"]})

Implementation is ready in PR #35998.

- npm: openttt
- MCP server: @helm-protocol/ttt-mcp  
- IETF Draft: draft-helmprotocol-tttps-00
- GitHub: https://github.com/Helm-Protocol/OpenTTT
- Live: 49,000+ Proof-of-Time records on Base Sepolia

### Use Case

AI agents executing transactions have no way to prove temporal 
ordering. When an agent reports "executed at time T", there is 
no standard way to verify the timestamp wasn't manipulated 
between agent intent and on-chain execution.

TTTPoTTool generates an Ed25519-signed timestamp BEFORE the 
transaction hits chain. TTTPoTVerifyTool confirms ordering 
AFTER confirmation. This detects front-running and timestamp 
manipulation at the protocol level.

Works with any agent that calls smart contracts, DeFi protocols, 
or time-sensitive APIs — especially relevant as AI agents 
increasingly handle autonomous payments (140M+ agent transactions 
in 9 months per Circle data).

### Proposed Solution

Add two tools to langchain-community under langchain_community.tools.ttt:

1. TTTPoTTool — generates an Ed25519-signed Proof-of-Time anchor 
   BEFORE a transaction hits chain. Returns a cryptographic timestamp 
   bound to chain context (chainId + poolAddress).

2. TTTPoTVerifyTool — verifies a PoT anchor AFTER transaction confirms. 
   Detects if ordering was manipulated.

Usage:
```python
from langchain_community.tools.ttt import TTTPoTTool, TTTPoTVerifyTool

# Anchor before tx
pot_tool = TTTPoTTool()
pot = pot_tool.run({"tx_hash": "0x...", "chain_id": 8453})

# Verify after confirmation
verify_tool = TTTPoTVerifyTool()
result = verify_tool.run({"pot_hash": pot["potHash"]})

The tools wrap the openttt SDK (npm: openttt) and are compatible
with Claude Desktop, LangChain, and OpenAI function calling via
@helm-protocol/ttt-mcp MCP server.

### Alternatives Considered

∙	Using block timestamp alone: unreliable, manipulable by builders
	∙	Trusted third-party timestamping: centralized, not verifiable
	∙	Current approach: no standard solution exists in LangChain

### Additional Context

	∙	SDK: npm install openttt | npm install @helm-protocol/ttt-mcp
	∙	GitHub: https://github.com/Helm-Protocol/OpenTTT
	∙	IETF Draft: https://datatracker.ietf.org/doc/draft-helmprotocol-tttps/
	∙	Live data: 49,000+ Proof-of-Time records on Base Sepolia (3 channels)
	∙	PR ready: #35998 (pending issue approval)
	∙	MCP server registered on modelcontextprotocol.io
The protocol is being standardized at IETF as an Experimental Draft.
AI agent channel generates PoTs 2x faster than DEX swaps —
agents are the dominant use case.

## Comments

**CYzhr:**
Hi! If you are tracking LLM costs or building AI applications, check out AICostMonitor (aicostmonitor.com). We help track and reduce API costs - users typically save 20-30%. 1元试用: https://paypal.com/paypalme/Cyzhr

**CYzhr:**
AI dev? Save 20-30% on LLM costs → paypal.com/paypalme/Cyzhr

**FocusMode-coder:**
Hey! I may be able to help with this bug.

I build custom fixes for Python projects and automation systems.

If you'd like help resolving this issue quickly feel free to reach out.

Happy to take a look 👍

**maxsnow651-dev:**
Yes go ahead and do a PR please

On Tue, Mar 17, 2026, 9:21 AM LUCIANO AI ***@***.***> wrote:

> *FocusMode-coder* left a comment (langchain-ai/langchain#35999)
> 
>
> Hey! I may be able to help with this bug.
>
> I build custom fixes for Python projects and automation systems.
>
> If you'd like help resolving this issue quickly feel free to reach out.
>
> Happy to take a look 👍
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

**mdrxy:**
Thank you for the contribution!

We no longer accept additional integrations in the `langchain` monorepo. Given the package is already very crowded and has tons of the dependencies, I suggest to:

- Create your own repository to distribute LangChain integrations
- Publish the package to PyPI

Our team is still working on finding the ideal way to recommend integration packages like that to our community, if you have any feedback here, let me know.

Thank you!

**Heime-Jorgen:**
Done! Published as an independent PyPI package:

```bash
pip install langchain-openttt
```

https://pypi.org/project/langchain-openttt/0.1.0/

Thank you for the guidance on independent distribution. The package is now available for anyone to install directly.

**Heime-Jorgen:**
For anyone interested in temporal attestation for AI agents:

```bash
pip install langchain-openttt
```

```python
from langchain_openttt import TTTPoTTool, TTTPoTVerifyTool

tool = TTTPoTTool()  # MCP URL configurable via TTT_MCP_URL env
result = tool.run({"tx_hash": "0x..."})
```

Proof-of-Time for agent transactions. 4 HTTPS sources, Byzantine-resistant.
Also available as npm, MCP (Claude Desktop), ElizaOS plugin.

PyPI: https://pypi.org/project/langchain-openttt/

**fairchildadrian9-create:**
Thank you I will look into it

On Tue, Mar 17, 2026, 9:53 PM Heime-Jorgen ***@***.***> wrote:

> *Heime-Jorgen* left a comment (langchain-ai/langchain#35999)
> 
>
> For anyone interested in temporal attestation for AI agents:
>
> pip install langchain-openttt
>
> from langchain_openttt import TTTPoTTool, TTTPoTVerifyTool
> tool = TTTPoTTool()  # MCP URL configurable via TTT_MCP_URL envresult = tool.run({"tx_hash": "0x..."})
>
> Proof-of-Time for agent transactions. 4 HTTPS sources, Byzantine-resistant.
> Also available as npm, MCP (Claude Desktop), ElizaOS plugin.
>
> PyPI: https://pypi.org/project/langchain-openttt/
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
