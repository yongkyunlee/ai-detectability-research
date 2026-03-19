# 🐞 [langchain-openai] Bug: reasoning_content not extracted from DeepSeek streaming responses

**Issue #35516** | State: closed | Created: 2026-03-02 | Updated: 2026-03-02
**Author:** squallopen
**Labels:** external

## Checkboxes

- [x] This is a bug, not a usage question.
- [x] I added a clear and descriptive title that summarizes this issue.
- [x] I used the GitHub search to find a similar question and didn't find it.
- [x] I am sure that this is a bug in LangChain rather than my code.
- [x] The bug is not resolved by updating to the latest stable version of LangChain.
- [x] This is related to langchain-openai package.
- [x] I posted a self-contained, minimal, reproducible example.

## Package
- [x] langchain-openai

## Related Issues
- #35006
- #34938

## Reproduction Steps

```typescript
import { ChatOpenAI } from "@langchain/openai";

const llm = new ChatOpenAI({
  model: "deepseek-reasoner",
  apiKey: process.env.DEEPSEEK_API_KEY,
  baseURL: "https://api.deepseek.com"
});

const stream = await llm.stream("What is 2+2?");

for await (const chunk of stream) {
  // chunk.additional_kwargs.reasoning_content is always undefined
  console.log("reasoning:", chunk.additional_kwargs?.reasoning_content);
}
```

Expected: `reasoning_content` should contain the model's thinking process.
Actual: `reasoning_content` is always undefined.

## Description

LangChain's ChatOpenAI doesn't extract `reasoning_content` from DeepSeek's streaming responses. The `reasoning_content` field is used by DeepSeek models (like `deepseek-reasoner`) to stream their thinking process.

## Suggested Fix

In `libs/langchain-openai/src/chat_models/completions.ts`, function `convertCompletionsDeltaToBaseMessageChunk`, add:

```typescript
// Extract reasoning_content (DeepSeek specific)
if (delta.reasoning_content) {
  additional_kwargs.reasoning_content = delta.reasoning_content;
}
```

## System Info

- langchain-openai: ^0.1.0
- Node.js: 18+
- DeepSeek API

---

## PR

Fix submitted: #35520
