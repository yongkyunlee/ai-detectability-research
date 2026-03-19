# Add Capsule to safely run untrusted code using WebAssembly sandboxes

**Issue #35518** | State: open | Created: 2026-03-02 | Updated: 2026-03-10
**Author:** mavdol
**Labels:** core, langchain, feature request, external

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
- [x] langchain-core
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
- [ ] langchain-openrouter
- [ ] langchain-perplexity
- [ ] langchain-qdrant
- [ ] langchain-xai
- [ ] Other / not sure / general

### Feature Description

I would like LangChain to support Capsule as a lightweight, self-hosted sandbox for executing untrusted Python/JavaScript code. Capsule is a runtime that runs python/javascript code in WebAssembly sandboxes.

### Use Case

When AI agents generate code, executing it directly could be risky for the host system. Except for Docker containers or cloud-based tools, there are few lightweight alternatives. While `langchain-sandbox` (Pyodide/Wasm) seems to be a great solution, it executes Python code only and is now archived.

### Proposed Solution

Integrate `langchain-capsule` to documentation, a LangChain version of Capsule. Here's how the implementation works:
```python
import asyncio
from langchain_capsule import CapsulePythonTool, CapsuleJSTool

# Python Example
python_tool = CapsulePythonTool()
result = python_tool.run("1 + 1")
print(result) # "2"

# JavaScript / TypeScript Example
js_tool = CapsuleJSTool()
result = asyncio.run(js_tool.arun("1 + 2"))
print(result) # "3"
```

Only the first run takes a second (cold start), then every next run starts in ~10ms. This is because Capsule compiles and caches a native version of the Wasm module locally after the first execution.

### Alternatives Considered

_No response_

### Additional Context

- PyPI package: langchain-capsule
- Integration repo: [github.com/mavdol/langchain-capsule](https://github.com/mavdol/langchain-capsule)
- Capsule main repo: [github.com/mavdol/capsule](https://github.com/mavdol/capsule)

Happy to submit a PR in the LangChain docs if there's interest. Also open to other integration possibilities around Capsule!

## Comments

**DHANUSH1323:**
Hi @mavdol 

I've been independently testing langchain-capsule v0.1.0 as part of a security evaluation for LangChain agent deployments. Found a few things worth discussing before the official integration:

print() output is silently suppressed, result returns None
No memory limits, 1GB allocation succeeds without error
Infinite loops freeze the host process for 25+ seconds

Happy to share my full benchmark results. Would you like to collaborate with me for this?

**mavdol:**
Hi @DHANUSH1323, thank you so much for testing this!

These points are mainly design choices, but I'm totally open to evolving them based on feedback.

The sandbox currently returns only the last evaluated expression (not the full stdout), which is why `print()` doesn't show up. Capturing stdout/stderr would definitely be a great improvement, though.

For memory limits and timeouts, I intentionally kept them open in this first version to avoid being too restrictive, but the options are already there. There's also a compute system that stops the sandbox if an operation consumes too much resources, which is why it stopped at 25 seconds even without a timeout set.

Here's the uncompiled sandbox file if you want to check:
https://github.com/mavdol/langchain-capsule/blob/main/src/sandbox_py.py

And you can find the options in the documentation here:
https://github.com/mavdol/capsule?tab=readme-ov-file#documentation-v063

I'd love to collaborate on this, feel free to share your benchmark results! Happy to adjust anything based on what people think is best.

**DHANUSH1323:**
Thanks, I read the sandbox code and Capsule docs.

My benchmark results line up with the current defaults:

Stdout: sandbox returns only the last evaluated expression, and stdout/stderr is not captured, so print() output is not surfaced.
Memory: ram defaults to unlimited, and the sandbox tasks do not set a ram limit, so allocating ~1GB succeeds.
Time: timeout defaults to unlimited, and the sandbox tasks do not set a timeout, so infinite loops run until the compute or fuel system stops them (I observed ~25s).

So the main gap for agent safety is not “Capsule lacks limits”, it’s that langchain-capsule currently does not expose or set safe defaults for ram and timeout, and does not expose stdout/stderr capture.

I can send a PR that:
1) adds optional ram and timeout to the @task decorators in sandbox_py.py
2) exposes these as CapsulePythonTool parameters (with safe defaults)
3) optionally returns stdout/stderr alongside the result.

**DHANUSH1323:**
I implemented safe defaults and opened a PR: https://github.com/mavdol/langchain-capsule/pull/6

What changed
1. Default RAM cap: 256MB
2. Reduced compute fuel (CUSTOM) to stop runaway loops quickly
3. Rebuilt bundled sandbox_py.wasm used by CapsulePythonTool

Benchmarks (local)
1. 1GB allocation now fails (task_error)
2. infinite loops terminate quickly

This aligns langchain-capsule defaults with Capsule’s documented resource control model while keeping behavior configurable later.

Happy to adjust the approach if you think different defaults would make more sense.

**mavdol:**
That looks great, I'll check this out !

**mavdol:**
Hi there! Quick update about the stdout (`print` / `console.log`).
Previously, `langchain-capsule` was strictly using a Jupyter style, so only the last expression was returned. It now captures the stdout as well, so agents can use `print`.

If anyone has any suggestions or feedback about this integration, feel free to let me know!

**DHANUSH1323:**
That’s a great improvement. Capturing stdout makes the tool much more practical for agent workflows and debugging.

The remaining safety sensitive defaults on my side were mainly around resource control for untrusted execution, which I addressed in the PR.

I’ll keep testing as the integration evolves and share any additional findings.
