# Feature: Add QEMU microVM execution strategy (exec-sandbox) as Docker alternative for CodeInterpreterTool

**Issue #4702** | State: open | Created: 2026-03-04 | Updated: 2026-03-04
**Author:** clemlesne

## Problem

CrewAI's CodeInterpreterTool exposes two execution modes, each with different code paths:

1. **Safe mode** (default) -- tries Docker container execution (recommended), automatically falls back to a restricted sandbox when Docker is unavailable. The sandbox is described as "very limited" with strict restrictions on many modules and built-in functions.
2. **Unsafe mode** -- executes directly on the host, explicitly not recommended for production

This leaves a real gap. Users who cannot or prefer not to run Docker (CI environments, macOS enterprise license constraints, Docker-in-Docker headaches per [#3028](https://github.com/crewAIInc/crewAI/issues/3028), or containerized deployments) are stuck choosing between a severely restricted sandbox and running untrusted LLM-generated code directly on their host machine. The [community forum thread](https://community.crewai.com/t/alternative-for-docker-while-doing-code-execution-by-agent/1623) and [issue #1983](https://github.com/crewAIInc/crewAI/issues/1983) show this is a recurring pain point.

## Proposal

Add [exec-sandbox](https://github.com/dualeai/exec-sandbox) (`pip install exec-sandbox`) as a 4th execution strategy -- hardware-isolated QEMU microVMs that provide stronger isolation than Docker containers without requiring a Docker daemon.

**What exec-sandbox provides:**

| | Docker (current) | exec-sandbox (proposed) |
|---|---|---|
| Isolation | Container (shared kernel) | Hardware VM (KVM/HVF, own kernel) |
| Daemon required | Yes (Docker Desktop) | No (just QEMU binary) |
| Docker Desktop license cost | Paid for orgs with 250+ employees or $10M+ revenue | Free (Apache-2.0 + QEMU GPL) |
| Warm start latency | Container startup (~1s) | 1-2ms (pre-booted VM pool) |
| Cold start latency | Image pull + boot | ~100ms (L1 memory snapshot) |
| Languages | Python (current impl) | Python, JavaScript, RAW |
| State leakage | Possible (shared layers) | None (fresh VM per execution, destroyed after) |
| Docker-in-Docker | Problematic ([#3028](https://github.com/crewAIInc/crewAI/issues/3028)) | N/A (no daemon) |
| Network control | Manual config | Disabled by default, domain allowlisting |
| File I/O | Mounts host CWD | Explicit upload/download (no host filesystem exposure) |

## How integration could work

### Option A: As a custom CrewAI Tool (works today, no core changes needed)

```python
from crewai import Agent, Task, Crew
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from exec_sandbox import Scheduler

class ExecSandboxInput(BaseModel):
    code: str = Field(..., description="Python 3 code to execute")
    packages: list[str] = Field(
        default_factory=list,
        description="pip packages to install before execution (e.g. ['pandas==2.2.0'])",
    )

class ExecSandboxTool(BaseTool):
    name: str = "Secure Code Interpreter"
    description: str = (
        "Executes Python 3 code in a hardware-isolated VM sandbox. "
        "Each execution gets a fresh VM that is destroyed after. "
        "Use for computations, data analysis, or any code that needs "
        "to run securely. Always end with a print() statement for output."
    )
    args_schema: type[BaseModel] = ExecSandboxInput

    def _run(self, code: str, packages: list[str] | None = None) -> str:
        import asyncio

        async def _execute():
            async with Scheduler() as scheduler:
                result = await scheduler.run(
                    code=code,
                    language="python",
                    packages=packages or [],
                    timeout_seconds=60,
                )
                if result.exit_code != 0:
                    return f"Error (exit code {result.exit_code}):\n{result.stderr}"
                return result.stdout

        return asyncio.run(_execute())

# Usage with a CrewAI agent
agent = Agent(
    role="Data Analyst",
    goal="Analyze data and produce insights",
    backstory="Expert data analyst with strong Python skills",
    tools=[ExecSandboxTool()],
)
```

### Option B: As a native CodeInterpreterTool strategy (requires core changes)

This would add `"microvm"` as a new `code_execution_mode` alongside `"safe"` and `"unsafe"`:

```python
agent = Agent(
    role="Data Analyst",
    goal="Analyze data and produce insights",
    backstory="Expert data analyst",
    allow_code_execution=True,
    code_execution_mode="microvm",  # New mode: QEMU microVM via exec-sandbox
)
```

Internally, `CodeInterpreterTool` would gain a `run_code_in_microvm()` method parallel to the existing `run_code_in_docker()` and `run_code_in_restricted_sandbox()`, dispatched from `_run()`.

## Why not just use Docker?

Docker works well for many users, and this proposal does not replace it. But there are legitimate cases where Docker is not viable:

- **Enterprise macOS teams**: Docker Desktop requires a [paid subscription](https://docs.docker.com/subscription/desktop-license/) for organizations with 250+ employees or $10M+ revenue. QEMU is free.
- **CI/CD and containerized deployments**: Running Docker-inside-Docker is fragile and requires privileged containers or socket mounting ([#3028](https://github.com/crewAIInc/crewAI/issues/3028)). QEMU microVMs need no daemon.
- **Stronger isolation needs**: Containers share the host kernel. A kernel exploit in a container can compromise the host. MicroVMs run their own kernel with hardware virtualization.
- **Restricted sandbox is too restricted**: The current fallback blocks many standard modules (`os`, `sys`, `subprocess`, `tempfile`, etc.), making it impractical for real data analysis or file processing tasks.

## About exec-sandbox

- **GitHub**: [dualeai/exec-sandbox](https://github.com/dualeai/exec-sandbox) -- Apache-2.0 license
- **PyPI**: [exec-sandbox](https://pypi.org/project/exec-sandbox/)
- **How it works**: Each execution boots a lightweight QEMU microVM (or grabs one from a warm pool in 1-2ms), runs code via a Rust guest-agent, streams stdout/stderr back, and destroys the VM. No state persists between executions.
- **Platforms**: macOS (HVF) + Linux (KVM)
- **Languages**: Python, JavaScript, RAW
- **Features**: Package installation with snapshot caching, file I/O, streaming output, network domain filtering, port forwarding, sessions for stateful multi-step workflows
