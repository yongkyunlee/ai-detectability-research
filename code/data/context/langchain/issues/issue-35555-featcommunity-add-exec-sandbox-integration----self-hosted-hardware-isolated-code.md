# feat(community): Add exec-sandbox integration -- self-hosted hardware-isolated code execution (QEMU microVMs)

**Issue #35555** | State: closed | Created: 2026-03-04 | Updated: 2026-03-04
**Author:** clemlesne
**Labels:** external

---

## Summary

LangChain's code execution story currently has a gap between local-but-limited (the now-archived `langchain-sandbox` / Pyodide) and cloud-managed sandboxes (E2B, Modal, Daytona, Runloop). There is no self-hosted option that provides hardware-level isolation, multi-language support, and production-grade security without requiring a cloud account or external API key.

[exec-sandbox](https://github.com/dualeai/exec-sandbox) fills this gap. It runs each Python, JavaScript, or shell execution in a dedicated QEMU microVM with hardware virtualization (KVM on Linux, HVF on macOS). The VM boots, runs code, and is destroyed -- no state leaks between executions. Apache-2.0 licensed.

This issue proposes adding `exec-sandbox` as a LangChain community integration, covering three surfaces:

1. **`ExecSandboxTool`** -- a `BaseTool` subclass for ReAct agents
2. **`ExecSandboxBackend`** -- a `SandboxBackendProtocol` implementation for Deep Agents
3. **`exec_sandbox_eval`** -- an eval function for `langgraph-codeact`

## Motivation

### The current landscape

| Solution | Isolation | Self-hosted | Languages | Maintained |
|---|---|---|---|---|
| `langchain-sandbox` (Pyodide) | WASM + Deno | Yes | Python only | [Archived](https://github.com/langchain-ai/langchain-sandbox) (Jan 2026) |
| E2B | Firecracker VM | [Complex](https://github.com/e2b-dev/infra) (Terraform + Nomad) | Python, JS/TS, R, Java, Bash | Yes |
| Modal | gVisor (userspace kernel) | No (cloud only) | Python | Yes |
| Daytona | Docker / Kata / Sysbox | Yes ([self-hosted via K8s](https://github.com/daytonaio/daytona), AGPL-3.0) | Multi | Yes |
| Runloop | Cloud sandbox | No (cloud API) | Multi | Yes |
| **exec-sandbox** | **Hardware VM (KVM/HVF)** | **Yes (`pip install`)** | **Python, JS/TS, Shell** | **Yes** |

### Why exec-sandbox complements existing integrations

1. **Data sovereignty** -- Code and data never leave the machine. Required for regulated industries and enterprise security policies that prohibit sending code to external services.

2. **No cloud dependency** -- `pip install exec-sandbox` + `brew install qemu` is the entire setup. No API key, no cloud account.

3. **macOS development** -- Develop and test locally on Mac (HVF) with the same isolation model as production Linux (KVM). E2B, Modal, Daytona, and Runloop require Linux/cloud for execution.

4. **Hardware-level isolation** -- Each execution runs in a dedicated QEMU microVM with its own kernel. The security model includes hardware virtualization (KVM/HVF), a hardened kernel (~360 subsystems stripped), EROFS read-only rootfs, seccomp, cgroups v2, namespaces, and unprivileged QEMU. See the [security documentation](https://github.com/dualeai/exec-sandbox#security) for details.

5. **Full runtime support** -- Runs native CPython 3.14 / Bun 1.3 / Bash. Arbitrary `pip install` works (any package with a prebuilt `musllinux` wheel). Unlike Pyodide (~300+ compatible packages), the full ecosystem is available.

Both cloud-managed sandboxes (E2B, Modal, Daytona, Runloop) and exec-sandbox can coexist as LangChain integrations. Cloud sandboxes are ideal for teams that want managed infrastructure. exec-sandbox is for teams that need self-hosted execution with full control over the security boundary.

## Proposed Implementations

### 1. `ExecSandboxTool` -- BaseTool for ReAct Agents

Follows the same pattern as `E2BDataAnalysisTool` in `langchain_community.tools`. Key difference: native async support (`_arun`).

```python
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field
from exec_sandbox import ExecutionResult, Scheduler, SchedulerConfig

class ExecSandboxInput(BaseModel):
    code: str = Field(..., description="The code to execute.")
    language: str = Field(default="python", description="'python', 'javascript', or 'raw' (shell).")
    packages: list[str] = Field(default_factory=list, description="Packages to install (e.g., ['pandas==2.2.0']).")

class ExecSandboxTool(BaseTool):
    """Execute code in a hardware-isolated QEMU microVM."""

    name: str = "exec_sandbox"
    description: str = (
        "Execute code in a secure, hardware-isolated sandbox (QEMU microVM). "
        "Supports Python, JavaScript/TypeScript, and shell commands. "
        "Returns stdout, stderr, and exit code."
    )
    args_schema: type[BaseModel] = ExecSandboxInput

    async def _arun(self, code: str, language: str = "python", packages: list[str] | None = None, **kwargs) -> str:
        scheduler = await self._ensure_scheduler()
        result = await scheduler.run(code=code, language=language, packages=packages or [],
                                     allow_network=self.allow_network, timeout_seconds=self.timeout_seconds)
        return _format_result(result)
```

Full implementation with `_run`, `_arun`, lifecycle management, and error handling will be provided in the PR.

**Usage with LangGraph ReAct agent:**

```python
from langchain.chat_models import init_chat_model
from langgraph.prebuilt import create_react_agent

model = init_chat_model("claude-sonnet-4-20250514", model_provider="anthropic")
tool = ExecSandboxTool(timeout_seconds=60, memory_mb=512)
agent = create_react_agent(model, [tool])

result = await agent.ainvoke({
    "messages": [{"role": "user", "content": "Calculate the first 20 Fibonacci numbers"}]
})
```

### 2. `ExecSandboxBackend` -- SandboxBackendProtocol for Deep Agents

Integrates with the [Deep Agents sandbox system](https://docs.langchain.com/oss/python/deepagents/sandboxes). The only required method is `execute()` -- all filesystem operations are [built on top by `BaseSandbox`](https://github.com/langchain-ai/deepagents/blob/main/libs/deepagents/deepagents/backends/sandbox.py).

```python
from deepagents.backends.protocol import ExecuteResponse, SandboxBackendProtocol
from exec_sandbox import Scheduler, SchedulerConfig, Session

class ExecSandboxBackend(SandboxBackendProtocol):
    """Self-hosted QEMU microVM sandbox for Deep Agents."""

    @property
    def id(self) -> str:
        return "exec-sandbox"

    async def aexecute(self, command: str, *, timeout: int | None = None) -> ExecuteResponse:
        session = await self._ensure_session()
        result = await session.exec(code=command, timeout_seconds=timeout or self._timeout_seconds)
        return ExecuteResponse(output=result.stdout or "", exit_code=result.exit_code, truncated=False)
```

Full implementation with lifecycle management, truncation handling, and `execute()` sync wrapper will be provided in the PR.

**Usage with Deep Agents:**

```python
from deepagents import create_deep_agent
from langchain.chat_models import init_chat_model
from langchain_exec_sandbox import ExecSandboxBackend

model = init_chat_model("claude-sonnet-4-20250514", model_provider="anthropic")
backend = ExecSandboxBackend(memory_mb=512, allow_network=True, allowed_domains=["api.github.com"])

agent = create_deep_agent(
    model=model,
    backend=backend,
    system_prompt="You are a software engineer. Use the sandbox to write, test, and debug code.",
)
```

### 3. `exec_sandbox_eval` -- Eval Function for langgraph-codeact

The [CodeAct architecture](https://github.com/langchain-ai/langgraph-codeact) requires a sandbox function with signature `(code: str, _locals: dict) -> tuple[str, dict]`. The default `eval()` using Python's `exec()` is [explicitly documented as unsafe](https://github.com/langchain-ai/langgraph-codeact#readme) for production.

```python
from exec_sandbox import Scheduler

def create_exec_sandbox_eval(scheduler: Scheduler, timeout_seconds: int = 30) -> callable:
    """Create a CodeAct-compatible eval function backed by exec-sandbox."""
    def eval_fn(code: str, _locals: dict) -> tuple[str, dict]:
        result = asyncio.get_event_loop().run_until_complete(
            scheduler.run(code=code, language="python", timeout_seconds=timeout_seconds)
        )
        output = result.stdout or ""
        if result.stderr:
            output += f"\n[stderr] {result.stderr}"
        return output, {}
    return eval_fn
```

Full implementation with variable serialization across turns and a session-backed stateful variant will be provided in the PR.

**Usage with CodeAct:**

```python
from exec_sandbox import Scheduler
from langgraph_codeact import create_codeact

async with Scheduler() as scheduler:
    eval_fn = create_exec_sandbox_eval(scheduler, timeout_seconds=60)
    agent = create_codeact(model, tools=[], eval_fn=eval_fn)
```

## Performance

| Path | Latency |
|---|---|
| Warm pool hit | 1-2ms |
| L1 memory snapshot | ~100ms |
| Cold boot | ~400ms boot + interpreter startup |

See the [benchmarks documentation](https://github.com/dualeai/exec-sandbox#performance) for throughput numbers under load.

## Prior Art

- [langchain-sandbox](https://github.com/langchain-ai/langchain-sandbox) -- archived Jan 2026, Pyodide/Deno sandbox
- [E2BDataAnalysisTool](https://github.com/langchain-ai/langchain/blob/master/docs/docs/integrations/tools/e2b_data_analysis.ipynb) -- cloud-managed sandbox (BaseTool pattern)
- [Deep Agents sandboxes](https://docs.langchain.com/oss/python/deepagents/sandboxes) -- SandboxBackendProtocol with Modal, Daytona, Runloop
- [langgraph-codeact](https://github.com/langchain-ai/langgraph-codeact) -- CodeAct architecture
- [exec-sandbox](https://github.com/dualeai/exec-sandbox) -- Apache-2.0, [PyPI](https://pypi.org/project/exec-sandbox/)

## Environment

- exec-sandbox: latest (PyPI)
- langchain-core: >=0.3
- Python: 3.12+
- QEMU: 8.0+
- Platforms: macOS (HVF), Linux (KVM)

## Comments

**keenborder786:**
https://github.com/langchain-ai/deepagents/tree/main/libs/partners
@clemlesne Since all backend and sandbox environment partner integrations are located in the DeepAgent repository, wouldn't it be more appropriate to open this issue directly in the DeepAgent repo?

**eyurtsev:**
@clemlesne a tool is fine, but same guidelines as I've advised in the deepagents repo. Please open up an integration package and put the implementations there. If you're associated with an actual company, you'll be able to submit details about your integration into the integration docs.
