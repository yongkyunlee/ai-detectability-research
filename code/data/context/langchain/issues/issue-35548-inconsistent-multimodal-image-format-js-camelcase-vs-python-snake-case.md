# Inconsistent multimodal image format: JS camelCase vs Python snake_case

**Issue #35548** | State: open | Created: 2026-03-04 | Updated: 2026-03-09
**Author:** huge0612
**Labels:** external

Title: Inconsistent multimodal image format: JS camelCase vs Python snake_case

## Description
LangGraph JS SDK generates `mimeType` (camelCase), Python expects `mime_type` (snake_case).

## Reproduction
1. Agent Chat UI (JS) → Python agent
2. Image upload → 400 BadRequestError: "Invalid value: image"

## Messages from Agent Chat UI:
```json
{
  "type": "image",
  "mimeType": "image/jpeg",  // ❌ Python expects mime_type
  "data": "...",
  "sourceType": "base64"     // ❌ Python expects source_type，witch is missing
}

## Expected
Unified snake_case across Python/JS SDKs.
