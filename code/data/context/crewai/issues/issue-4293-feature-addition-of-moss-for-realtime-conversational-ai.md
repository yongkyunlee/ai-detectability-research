# [FEATURE] Addition of Moss for realtime Conversational AI

**Issue #4293** | State: closed | Created: 2026-01-28 | Updated: 2026-03-06
**Author:** CoderOMaster
**Labels:** feature-request, no-issue-activity

### Feature Area

Integration with external tools

### Is your feature request related to a an existing bug? Please link it here.

NA

### Describe the solution you'd like

Add Moss as a Tool to Crewai to enable low-latency, local-first semantic search within agents and chains.

Moss is a real-time semantic search engine optimized for conversational and multimodal AI. It enables agents, voice assistants, and chatbots to retrieve, reason, and respond in sub-10ms by colocating the vector search index with the model in the browser, on-device, or on the server. It supports hybrid keyword + semantic retrieval and comes with JS/Python SDKs.

This feature would expose Moss as a Tool that agents can call (e.g., moss_search("query")) to:

1. retrieve top-k results using Moss’s low-latency semantic engine,
2. return rich text snippets or document metadata for downstream reasoning,
3. optionally blend keyword and vector search with parameter control.

Available at https://usemoss.dev/

I propose integrating Moss as a Tool to support fast, context-aware retrieval directly within agents.

This would include:

A MossTool that allows agents to call Moss via a simple moss_search(query) interface.
Support for creating and loading a Moss index (local or hosted).
Retrieval functions that return top-k documents, optionally filtered by metadata.
Adjustable parameters to tune semantic vs keyword weighting, allowing hybrid retrieval strategies.

### Describe alternatives you've considered

_No response_

### Additional context

_No response_

### Willingness to Contribute

Yes, I'd be happy to submit a pull request

## Comments

**CoderOMaster:**
Hi Team, lemme kniw if i can work on it?

**github-actions[bot]:**
This issue is stale because it has been open for 30 days with no activity. Remove stale label or comment or this will be closed in 5 days.

**github-actions[bot]:**
This issue was closed because it has been stalled for 5 days with no activity.
