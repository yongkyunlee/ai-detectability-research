# [FEATURE] Native Oracle Cloud (OCI) Generative AI Integration

**Issue #4944** | State: open | Created: 2026-03-18 | Updated: 2026-03-18
**Author:** fede-kamel

## Feature Request

Add native support for Oracle Cloud Infrastructure (OCI) Generative AI as a first-class provider in CrewAI.

## Why

OCI GenAI is one of the few cloud platforms hosting multiple model families under one roof — Meta Llama, Google Gemini, OpenAI GPT (4o, 5, OSS), xAI Grok, and Cohere — all accessible through a single API surface. Enterprise teams on OCI currently have no native path to use these models with CrewAI without custom workarounds.

Adding native OCI support would:
- Give CrewAI access to Oracle's enterprise customer base
- Enable crews to use 50+ models across 6 model families on OCI
- Support embeddings (Cohere models) for RAG workflows
- Support tool/function calling for agentic workflows
- Provide an alternative to OpenAI/Anthropic for enterprises with Oracle cloud commitments

## Implementation

PR #4885 provides a complete implementation including:
- `OciLLM` class with chat, streaming, and tool calling
- `OciEmbedding` class for Cohere embedding models
- OCI API key authentication with request signing
- Model-specific parameter handling across all families
- Full test coverage

## Related

- Issue #3165 (closed) — prior bug report about OCI GenAI Gateway compatibility
- PR #4885 — implementation ready for review
