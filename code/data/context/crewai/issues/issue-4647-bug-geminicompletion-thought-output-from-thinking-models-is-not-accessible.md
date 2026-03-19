# [BUG] GeminiCompletion: thought output from thinking models is not accessible

**Issue #4647** | State: closed | Created: 2026-02-28 | Updated: 2026-03-03
**Author:** schuay
**Labels:** bug

### Description

When using a Gemini thinking model (e.g. gemini-2.5-pro, gemini-3.1-pro-preview) with stream=True, crewai emits a warning and silently discards all thought content. There is currently no supported path to access the model's reasoning output.

### Steps to Reproduce

  crewai[google-genai] >= 0.28.8
  google-genai (native provider path via GeminiCompletion)
  model: gemini/gemini-3.1-pro-preview (or any gemini-2.5+ thinking model)
  stream=True

  Every streaming response involving a tool call produces:

  WARNING:google_genai.types:Warning: there are non-text parts in the response:
  ['function_call', 'thought_signature'], returning concatenated text result from
  text parts. Check the full candidates.content.parts accessor to get the full
  model response.

  Thought content is never surfaced to the caller — not via events, not via callbacks, not via any public API.

### Expected behavior

Thoughts should be surfaced.

### Screenshots/Code snippets

None

### Operating System

Ubuntu 20.04

### Python Version

3.12

### crewAI Version

1.10.0

### crewAI Tools Version

1.10.0

### Virtual Environment

Venv

### Evidence

None

### Possible Solution

  Two issues in src/crewai/llms/providers/gemini/completion.py:

  1. _prepare_generation_config does not set thinking_config

  The method builds a types.GenerateContentConfig but never sets thinking_config. Without thinking_config=ThinkingConfig(include_thoughts=True), the Gemini API does not return thought text parts — only the opaque thought_signature metadata. This means
  thought content is never requested, let alone captured.

  2. _process_stream_chunk uses chunk.text and ignores thought parts

```
  # completion.py line ~934
  if chunk.text:                  # <-- calls .text property → triggers warning
      full_response += chunk.text
```

  The .text property on a GenerateContentResponse raises the warning whenever non-text parts (function_call, thought_signature) are present. The method then iterates candidate.content.parts but only handles part.function_call, skipping any parts where
  part.thought == True.

  Workaround (monkey-patch)

  Until this is fixed, both issues can be patched at runtime before any LLM() instantiation:

```
  from crewai.llms.providers.gemini.completion import GeminiCompletion

  _orig_config  = GeminiCompletion._prepare_generation_config
  _orig_chunk   = GeminiCompletion._process_stream_chunk

  def _patched_config(self, system_instruction=None, tools=None, response_model=None):
      config = _orig_config(self, system_instruction, tools, response_model)
      from google.genai import types
      config.thinking_config = types.ThinkingConfig(include_thoughts=True)
      return config

  def _patched_chunk(self, chunk, full_response, function_calls, usage_data,
                     from_task=None, from_agent=None):
      # Capture thought parts before _orig_chunk calls chunk.text
      if chunk.candidates:
          candidate = chunk.candidates[0]
          if candidate.content and candidate.content.parts:
              for part in candidate.content.parts:
                  if getattr(part, "thought", False) and part.text:
                      # Replace with your preferred sink: logger, event bus, callback, etc.
                      print(f"[thought] {part.text}", end="", flush=True)

      return _orig_chunk(self, chunk, full_response, function_calls,
                         usage_data, from_task, from_agent)

  GeminiCompletion._prepare_generation_config = _patched_config
  GeminiCompletion._process_stream_chunk      = _patched_chunk
```

### Additional context

None
