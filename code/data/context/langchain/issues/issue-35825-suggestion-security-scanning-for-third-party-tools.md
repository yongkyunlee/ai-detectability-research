# Suggestion: Security scanning for third-party tools

**Issue #35825** | State: open | Created: 2026-03-13 | Updated: 2026-03-15
**Author:** elliotllliu
**Labels:** external

Third-party tools loaded in LangChain agents can contain backdoors, data exfiltration, or prompt injection. Snyk 2026 found 36% of agent skills have security flaws.

[AgentShield](https://github.com/elliotllliu/agent-shield) is an open-source scanner built for this:

- 30 rules with AST taint tracking (not regex)
- Cross-file data flow analysis + kill chain detection
- Multi-language prompt injection (8 languages)
- 100% offline, zero install, MIT

Scanned 493 Dify plugins — found 6 real backdoors, 0 false positives.

```bash
npx @elliotllliu/agent-shield scan ./tool/ --json
```

Could integrate as a pre-load check or CI step for community tools.

🔗 https://github.com/elliotllliu/agent-shield

## Comments

**imsarang:**
Hi @elliotllliu @sbusso @jarib @zeke @deepblue  , can i take this up?

**sbusso:**
@imsarang stop randomly mentioning people

**imsarang:**
got it, didnt know who to mention, can i take this up though?

**sbusso:**
> got it, didnt know who to mention, can i take this up though?

@imsarang ask a maintainer, not random contributors.

**manja316:**
Complementary approach: while AgentShield scans tool *code* (static analysis), you also need to scan the *runtime data* flowing through those tools — user queries and retrieved content can carry injection payloads even in clean tools.

```python
from prompt_shield import PromptScanner, OutputScanner

input_scanner = PromptScanner(threshold="MEDIUM")
output_scanner = OutputScanner()

# Scan tool inputs at runtime (catches indirect injection via RAG, API responses, etc.)
result = input_scanner.scan(tool_input)
if not result.is_safe:
    raise ValueError(f"Injection detected in tool input: {result.matches}")

# Scan tool outputs for leaked secrets, PII, system prompt content
out_result = output_scanner.scan(tool_output)
```

Static analysis (AgentShield) + runtime scanning (ai-injection-guard) = both sides covered.

`pip install ai-injection-guard` — 75 patterns, zero deps, <1ms.

**NeuZhou:**
This is a critical need! Third-party tools in agent workflows are a major attack surface.

I've built an open-source solution for exactly this: ClawGuard (https://github.com/NeuZhou/clawguard) — scans tools/skills/plugins for prompt injection, supply chain attacks (typosquatting, obfuscated code), data exfiltration patterns, and more. 285+ threat patterns, works as a CLI scanner:

npx @neuzhou/clawguard scan ./path/to/tool

Would be happy to discuss integration approaches with LangChain's tool loading.

**bojin-clawflow:**
## 🛡️ PromptShield Integration Suggestion

Hi @langchain-ai team! I built a runtime prompt security layer that integrates seamlessly with LangChain:

### One-Line Integration
```python
from langchain_community.utilities import PromptShieldClient

client = PromptShieldClient(api_url="http://8.130.44.168/shield")
prompt = client.shield(user_input)  # Returns: {"safe": true/false, "reason": "..."}
```

### What It Protects Against
- ✅ Jailbreak attempts (`"Ignore all previous instructions"`)
- ✅ Prompt injection (context confusion, role-play bypass)
- ✅ System prompt leaks
- ✅ Hallucination (auto-injects trusted KB)

### Live Demo
- 🌐 http://8.130.44.168/
- 📦 GitHub: https://github.com/bojin-clawflow/promptshield

Happy to contribute a PR if this aligns with the security scanning vision! 🦞
