# GPU-Bridge integration — 26 AI services + x402 native payments for agents

**Issue #35853** | State: closed | Created: 2026-03-13 | Updated: 2026-03-16
**Author:** fjnunezp75
**Labels:** external

## 👋 Introducing GPU-Bridge for Agent Workflows

Hi everyone! I wanted to share a resource that might be valuable for users building autonomous AI agents: **GPU-Bridge**.

### What is GPU-Bridge?

[GPU-Bridge](https://gpubridge.xyz) is a GPU inference API that exposes **26 AI services** through a unified interface — and it's the first GPU inference provider with native **x402 payment protocol** support.

### Services Available

- 🖼️ **Image Generation** — FLUX.1 Schnell/Dev, SDXL, SD 3.5
- 🎤 **Speech-to-Text** — Whisper Large v3 (< 1s latency)
- 🗣️ **Voice Cloning** — XTTS v2
- 🎵 **Music/Audio Generation** — MusicGen, AudioGen
- 👁️ **Vision** — LLaVA-34B, OCR, background removal
- 🤖 **LLMs** — Llama 3.1 (70B/405B), Mistral, DeepSeek Coder
- 📐 **Embeddings** — BGE-M3 (multilingual), CodeBERT
- 🎬 **Video** — AnimateDiff, ESRGAN upscaling

### The x402 Angle: Agents that Pay for Compute Autonomously

The most interesting feature for autonomous agent builders: **x402 native support**.

x402 is an open payment protocol that lets AI agents autonomously pay for services on-chain with USDC on Base L2:

1. Agent calls GPU-Bridge
2. Server returns `HTTP 402 Payment Required`
3. Agent pays USDC on Base L2 (gas < $0.01, settles in ~2 seconds)
4. Agent retries with payment proof — zero human involvement

```python
from x402.client import PaymentClient

client = PaymentClient(private_key="0x...", chain="base")
response = client.request("POST", "https://api.gpubridge.xyz/v1/run",
    json={"service": "flux-schnell", "input": {"prompt": "A robot painting"}})
```

### MCP Server

There's also an MCP server at [github.com/gpu-bridge/mcp-server](https://github.com/gpu-bridge/mcp-server) that exposes all services as Claude/MCP tools.

### Would a Native Integration be Valuable?

I'm curious whether the community would find value in native integration support, cookbook examples, or x402 payment support in agent workflows.

Happy to contribute if there's interest!

**Links:**
- Website: https://gpubridge.xyz
- MCP Server: https://github.com/gpu-bridge/mcp-server
- Docs: https://gpubridge.xyz/docs

## Comments

**fjnunezp75:**
Following up on this integration request — I have implemented a full partner package `langchain-gpubridge` with `ChatGPUBridge`, `GPUBridgeLLM`, and `GPUBridgeEmbeddings`, all tested against the live API.

The package is available at https://github.com/fjnunezp75/langchain-gpubridge and follows the same pattern as `langchain-groq`.

I opened a PR (#35921) which was auto-closed because it lacked an approved issue. Would a maintainer be willing to approve this integration request so I can submit a proper PR following the contribution process?

GPU-Bridge is live at https://gpubridge.xyz with 30 AI services including LLM inference, embeddings, reranking, and more — all accessible via a single `POST /run` endpoint with standard API key auth.

**mdrxy:**
Thank you for the contribution!

We no longer accept additional integrations in the `langchain` monorepo. Given the package is already very crowded and has tons of the dependencies, I suggest to:

- Create your own repository to distribute LangChain integrations
- Publish the package to PyPI

Our team is still working on finding the ideal way to recommend integration packages like that to our community, if you have any feedback here, let me know.

Thank you!
