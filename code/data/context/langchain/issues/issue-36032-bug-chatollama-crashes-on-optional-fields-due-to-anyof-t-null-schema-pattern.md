# [Bug]: ChatOllama crashes on Optional fields due to anyOf: [T, null] schema pattern

**Issue #36032** | State: open | Created: 2026-03-17 | Updated: 2026-03-17
**Author:** Rav-xyl
**Labels:** external

Ollama's model templates expect flat schemas and do not handle the anyOf: [T, null] pattern that Pydantic v2 generates for Optional fields. This causes crashes during tool binding in ChatOllama.

## Comments

**Rav-xyl:**
.take

**Jairooh:**
This is a known Pydantic v2 breaking change — `Optional[T]` now serializes as `anyOf: [{type: T}, {type: null}]` instead of just `{type: T, nullable: true}`. A quick workaround is to pre-process your schema before binding: strip the `anyOf` wrappers by replacing `{"anyOf": [T_schema, {"type": "null"}]}` patterns with just `T_schema` (plus `"nullable": true` if the backend supports it). Alternatively, using `model_rebuild()` with `json_schema_extra` overrides on your Pydantic model fields can flatten the output before it hits Ollama's template parser.
