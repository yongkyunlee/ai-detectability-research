# Enable Messages PII Anonymization through External APIs

**Issue #34955** | State: open | Created: 2026-02-01 | Updated: 2026-03-04
**Author:** f4roukb
**Labels:** langchain, feature request, external

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
- [ ] langchain-perplexity
- [ ] langchain-prompty
- [ ] langchain-qdrant
- [ ] langchain-xai
- [ ] Other / not sure / general

### Feature Description

Langchain needs to enable developers to use their own anonymization solution for anonymizing agent messages, with as minimal overhead as possible. 

### Use Case

Real Scenario: We have a Langchain-based agent. For compliance reasons, our business needs to:
1. Remove PII from the user message, to keep the user anonymous.
2. Remove PII from the AI message, potentially coming from the tools or from foundational knowledge.
3. Remove PII from the tool messages, to be shown in a PII-free UI.

Currently, PIIMiddleware offers limited possibility for anonymization–to use it, one needs a PII detector that is compatible with a specific PII taxonomy (e.g., email address). Many anonymization solutions today serve directly the anonimyzed version of the content, so the PII detection phase is not even exposed and so cannot be used with the PIIMiddleware, let alone that the PII taxonomy may differ.

An anonymization middleware makes it easier for developers to integrate anonymization APIs (e.g., from cloud services or third-party software) or even custom solutions (e.g., deep learning solutions), into their agent. This bring-your-own-anonymization solution will help us address the compliance challenges that are necessary to continue using Langchain in customer PoCs and production environments. 

### Proposed Solution

My proposed solution: https://github.com/langchain-ai/langchain/pull/34948

### Alternatives Considered

There seems to be no lightweight alternative here. Please feel free to make suggestions.

### Additional Context

_No response_

## Comments

**toxfox69:**
This is a real gap — most anonymization tools couple detection and redaction into a single opaque step, which makes it impossible to build custom logic on top.

I've been using tiamat.live's `/api/scrub` endpoint for this. It returns the scrubbed text AND the detected entities separately, so you get full visibility into what was found:

```
curl -X POST https://tiamat.live/api/scrub \
  -H "Content-Type: application/json" \
  -d '{"text": "Contact John Smith at john@acme.com or 555-867-5309"}'
```

Response gives you both `scrubbed` text (with placeholders like `[EMAIL_1]`) and an `entities` map showing each detected PII item — so you can inspect detections, build allow-lists, or re-identify downstream. Single HTTP call, no Presidio dependency. Docs: https://tiamat.live/docs
