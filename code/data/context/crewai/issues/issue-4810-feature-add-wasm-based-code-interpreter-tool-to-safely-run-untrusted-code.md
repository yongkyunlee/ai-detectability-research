# [FEATURE] Add Wasm-based code interpreter tool to safely run untrusted code.

**Issue #4810** | State: open | Created: 2026-03-11 | Updated: 2026-03-11
**Author:** mavdol
**Labels:** feature-request

### Feature Area

Integration with external tools

### Is your feature request related to a an existing bug? Please link it here.

It's related to the security vulnerabilities identified in the current CodeInterpreterTool (#4516). The discussion suggests more robust isolation like containers or other non Python-level sandboxing, which is what this integration provides with Wasm.

### Describe the solution you'd like

I'm proposing an integration called `crewai-capsule`. It's a pre-configured version of `Capsule`, a runtime I built to sandbox AI agent tasks using WebAssembly.

Here's an example of how it would work:
 
```python
from crewai_capsule import CapsulePythonREPLTool

python_tool = CapsulePythonREPLTool()

code = """
def factorial(n):
    if n <= 1:
        return 1
    return n * factorial(n - 1)

factorial(6)
"""

result = python_tool.run(code)
print(result) # "720"
```

Only the first run takes about a second (cold start), then every next run starts in ~10ms.

### Describe alternatives you've considered

_No response_

### Additional context

PyPI package: `crewai-capsule`
Integration repository: [github.com/mavdol/crewAI-capsule](https://github.com/mavdol/crewAI-capsule)
Main Capsule repository: [github.com/mavdol/capsule](https://github.com/mavdol/capsule)

I've also built a separate MCP server that provides the same sandboxing capabilities, if that's of interest: [github.com/mavdol/capsule/integrations/mcp-server](https://github.com/mavdol/capsule/tree/main/integrations/mcp-server)

I'd be happy to submit a PR to integrate this solution into CrewAI (whether through documentation, a direct integration, or any other convenient way).

### Willingness to Contribute

Yes, I'd be happy to submit a pull request
