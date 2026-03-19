# [Community] Add AgenticReasoningLoader

**Issue #36019** | State: closed | Created: 2026-03-17 | Updated: 2026-03-17
**Author:** SaschaDeforth
**Labels:** feature request, external

### Checked other resources

- [x] This is a feature request, not a bug report or usage question.
- [x] I added a clear and descriptive title that summarizes the feature request.
- [x] I used the GitHub search to find a similar feature request and didn't find it.
- [x] I checked the LangChain documentation and API reference to see if this feature already exists.
- [x] This is not related to the langchain-community package.

### Package (Required)

- [ ] langchain
- [ ] langchain-openai
- [ ] langchain-anthropic
- [ ] langchain-classic
- [ ] langchain-core
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
- [x] Other / not sure / general

### Feature Description

### New Community Document Loader

**Package:** `langchain-arp`  
**Repository:** https://github.com/975SDE/langchain-arp  
**License:** MIT  
**Python:** 3.9+

---

### What is reasoning.json?

The [Agentic Reasoning Protocol (ARP)](https://arp-protocol.org) is an open web standard that provides machine-readable reasoning directives, anti-hallucination guardrails, and counterfactual logic to autonomous AI agents.

A `reasoning.json` file is served at `/.well-known/reasoning.json` — similar to how `robots.txt` controls crawlers and `schema.org` describes entities, `reasoning.json` teaches AI agents *how to think* about an entity.

### Use Case

### Why this matters for LangChain

As AI agents increasingly reason about brands and entities, hallucination prevention becomes critical. This loader gives LangChain developers a standardized way to ingest entity-approved ground truth into their RAG pipelines — reducing hallucination rates for specific entities.

### Proposed Solution

_No response_

### Alternatives Considered

N/A - Standard implementation for a new protocol.

### Additional Context

### Installation

```bash
pip install git+https://github.com/975SDE/langchain-arp.git
```

### Specification

- Full spec: https://arp-protocol.org/SPEC.md
- JSON Schema: https://arp-protocol.org/schema/v1.json
- Live deployments: 6+ production sites already serve `reasoning.json`

---

**Author:** Sascha Deforth ([@975SDE](https://github.com/975SDE))  
**Website:** https://arp-protocol.org

## Comments

**SaschaDeforth:**
## Context: Why ARP aligns with LangChain's direction

In a [recent interview](https://www.youtube.com/watch?v=rSKh6bVuVZI) (March 2026, Daytona Compute Conference), Harrison Chase described three core concepts that directly map to what ARP provides:

### 1. Skills as the new agent primitive

> *"Skills are basically a bunch of files. There's usually one skill.md file, which is a big markdown file that contains instructions on how to do something. [...] Rather than being loaded into the system prompt, they are just referenced in the system prompt."*

**ARP connection:** `reasoning.json` functions exactly like a Skill file

**mdrxy:**
Thank you for the contribution!

We no longer accept additional integrations in the `langchain` monorepo. Given the package is already very crowded and has tons of the dependencies, I suggest to:

- Create your own repository to distribute LangChain integrations
- Publish the package to PyPI

Our team is still working on finding the ideal way to recommend integration packages like that to our community, if you have any feedback here, let me know.

Thank you!

**SaschaDeforth:**
Thanks @mdrxy -- that makes total sense, and it's actually the direction we were already heading.

The standalone package is ready:

- **Repo:** [975SDE/langchain-arp](https://github.com/975SDE/langchain-arp)
- **Install:** `pip install langchain-arp` (publishing to PyPI today)
- **License:** MIT, full test suite (19 tests), zero hard dependencies beyond `requests`

Regarding the community recommendation program -- I'd love to be considered once that's in place. A few data points:

- The [Agentic Reasoning Protocol](https://arp-protocol.org) has a published spec and JSON schema
- 6+ production sites already serve `reasoning.json`
- The loader supports both file and URL loading with priority-based document ordering

Happy to provide any additional info you need. And if there's a registry, directory, or "awesome list" for community integrations, I'd be glad to submit there as well.
