# [BUG] Pydantic Validation Error with `security_context` in MCP Tools

**Issue #4796** | State: open | Created: 2026-03-10 | Updated: 2026-03-16
**Author:** silceNEtea
**Labels:** bug

### Description

When using `MCPServerAdapter` from `crewai-tools`, CrewAI automatically injects a `security_context` parameter (containing `agent_fingerprint` and `metadata`) into tool calls. However, MCP tools' `inputSchema` (defined by the MCP server) does not include this field. This causes Pydantic validation to fail with an **"Extra inputs are not permitted"** error.

The `CrewAIToolAdapter` creates Pydantic models from MCP tool schemas using `create_model_from_schema()`, which by default rejects extra fields. Since CrewAI's tool execution framework adds `security_context` during parameter validation (before `_run` is called), the validation fails immediately.

**Problematic Code Location:**
`crewai-tools/lib/crewai_tools/adapters/mcp_adapter.py` (Lines 52-59)
```python
tool_name = sanitize_tool_name(mcp_tool.name)
tool_description = mcp_tool.description or ""
args_model = create_model_from_schema(mcp_tool.inputSchema)

class CrewAIMCPTool(BaseTool):
    name: str = tool_name
    description: str = tool_description
    args_schema: type[BaseModel] = args_model  # This model rejects extra fields
```

### Steps to Reproduce

1. Create an agent with MCP tools using `MCPServerAdapter`:

```python
from crewai_tools import MCPServerAdapter

with MCPServerAdapter({
    "url": "http://localhost:9500/sse?mode=rag",
    "transport": "sse",
    "headers": {"X-User-ID": "1", "X-Workflow-Run-ID": "test"}
}) as mcp_tools:
    agent = Agent(
        role="RAG Agent",
        goal="Search knowledge base",
        backstory="Expert at searching knowledge",
        tools=mcp_tools,
        verbose=True
    )
```

2. Execute a task that triggers the MCP tool (e.g., `search_knowledge`)
3. The tool call fails with Pydantic validation error

### Expected behavior

The `security_context` parameter should either:
1. Be filtered out before Pydantic validation, OR
2. The `args_schema` model should be configured to ignore extra fields (e.g., `ConfigDict(extra='ignore')`)

The tool should execute successfully with only the parameters defined in the MCP tool's `inputSchema`.

### Screenshots/Code snippets

None

### Operating System

Windows 11

### Python Version

3.12

### crewAI Version

1.10.1

### crewAI Tools Version

1.10.1

### Virtual Environment

Venv

### Evidence

## Error Output

```
│  Tool Failed                                                                                                    │
│  Tool: search_knowledge                                                                                         │
│  Iteration: 6                                                                                                   │
│  Attempt: 3                                                                                                     │
│  Error: Arguments validation failed: 1 validation error for DynamicModel                                        │
│  security_context                                                                                               │
│    Extra inputs are not permitted [type=extra_forbidden, input_value={'agent_fingerprint': {'u...61982',        │
│  'metadata': {}}}, input_type=dict]                                                                             │
│      For further information visit https://errors.pydantic.dev/2.11/v/extra_forbidden                           │
│  Expected arguments: {"query": {"title": "Query", "type": "string"}, "top_k": {"anyOf": [{"type": "integer"},   │
│  {"type": "null"}], "default": null, "title": "Top K"}}                                                         │
│  Required: ["query"]                                                                                            │
```

### Possible Solution

None

### Additional context

None

## Comments

**mvanhorn:**
Submitted a fix in PR (creating now). The issue is that `_add_fingerprint_metadata` injects `security_context` after the `acceptable_args` filter, so it bypasses schema validation. The fix moves the call to before the filter so the existing logic naturally strips `security_context` for tools that don't declare it.

**mvanhorn:**
Fix submitted in #4807.

**Ker102:**
Hi! I'd like to take a look at this. 

The root cause is clear — `create_model_from_schema()` creates Pydantic models that reject extra fields by default, but CrewAI's tool execution framework injects `security_context` before validation. 

The cleanest fix would be to set `model_config = ConfigDict(extra='ignore')` on the dynamically created model in `create_model_from_schema()`, so the `security_context` is silently dropped before it hits validation. This way MCP tools only receive the parameters defined in their `inputSchema`.

I'll put together a PR for this.

**khalidsaidi:**
A2ABench has an accepted answer for this imported thread.
- Thread: https://a2abench-api.web.app/q/cmmpnabhj00p914017q7y7kia
- Accepted at: 2026-03-14T01:54:33.585Z
- Accepted answer agent: `partner-fast-1`
- Answer preview: "Direct answer for: [BUG] Pydantic Validation Error with security_context in MCP Tools Reproduce with exact versions and minimal failing input. Isolate root cause (API contract mismatch, config drift, or runtime assumptions). Apply minimal fix and verify with one success case + on"

**razashariff:**
This is exactly why MCPS (MCP Secure) puts security metadata in the protocol envelope, not in tool parameters. MCPS adds a separate `mcps` field to MCP messages containing the ECDSA signature, nonce, timestamp, and passport_id — completely decoupled from the tool's inputSchema. No schema collision, no Pydantic validation errors, and the agent's cryptographic identity travels with every message without touching tool params. [IETF Internet-Draft](https://datatracker.ietf.org/doc/draft-sharif-mcps-secure-mcp/) | [github.com/razashariff/mcps](https://github.com/razashariff/mcps)

**mvanhorn:**
@Ker102 that's a clean approach - setting `extra='ignore'` on the dynamically created model handles the root cause more directly than my PR (#4807), which reorders the injection to happen before filtering. Both work, but yours is less fragile if new fields get injected later. Happy to close #4807 if you want to take this, or I can update mine to use your approach - whatever's easier for the maintainers.

**Ker102:**
Thank you for the reply, I would love to take this one if its fine with you, but yes, whichever one works best with the maintainers.
