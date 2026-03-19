# Security: Recursive tool calling without cycle guard

**Issue #35721** | State: open | Created: 2026-03-10 | Updated: 2026-03-12
**Author:** cloakmaster
**Labels:** external

## Security Findings Report

We scanned this repository using [Inkog](https://inkog.io), an AI security scanner, and identified **1 MEDIUM severity vulnerability** related to recursive tool calling.

### Summary

- **1 MEDIUM severity** recursive tool calling without cycle guard
- **Governance Score:** 100/100 (otherwise excellent security posture)

### Findings

| Severity | Issue | Location |
|----------|-------|----------|
| MEDIUM | Recursive Tool Calling Without Cycle Guard | `base.py:668` |

### Details

The code allows recursive tool calling without implementing a cycle detection or depth limit guard. While this might be intentional for certain use cases, it poses risks:
- **Stack overflow:** Deep recursion can exhaust memory
- **Infinite loops:** Malformed or adversarial inputs could cause the agent to recurse indefinitely
- **Resource exhaustion:** Can lead to DoS conditions

### How to Reproduce

You can verify these findings by running Inkog yourself:

```bash
npx -y @inkog-io/cli scan . -deep
```

### Recommendations

1. **Add recursion depth limit:** Implement a maximum recursion depth counter.
2. **Cycle detection:** Track call history to detect and prevent circular tool calling patterns.
3. **Timeout mechanisms:** Add configurable timeout limits for tool execution chains.
4. **Documentation:** If recursive behavior is intentional, document the risks and provide configuration options for users to set their own limits.

### Learn More

For detailed remediation guidance and best practices for securing AI applications, visit [inkog.io](https://inkog.io).

---

*This report was generated to help improve the security of your project. We hope you find it useful! Note: Your repository scored 100/100 on governance, which is excellent — this is just a minor improvement opportunity.*

## Comments

**saschabuehrle:**
Good catch. A simple guard that tends to stop runaway recursion without blocking valid chains is a two gate approach:

Gate one is a strict max depth per run and per tool family.
Gate two is a repeated state detector keyed by normalized tuple of tool name, args hash, and recent parent call ids.

When either gate trips, return a structured tool error that includes reason and a suggested next safe action. This lets the agent recover instead of hard failing.

Test matrix that helped us validate behavior:

Normal DAG flow
Intentional recursion with changing args
Accidental recursion with same args
Parallel branches that call same tool with different args

The key detail is normalization of args before hashing so semantically equal payloads map to one key.

**Financier-Nuri:**
## 安全分析

这是一个关于递归工具调用循环检测的重要安全问题。感谢使用Inkog进行安全扫描！

### 问题分析

在处缺乏递归深度限制确实会导致：
1. **栈溢出**：深层递归会耗尽内存
2. **无限循环**：畸形或恶意输入可能导致无限递归
3. **资源耗尽**：可能导致DoS条件

### 建议解决方案

**方案1：添加递归深度限制**

**方案2：循环检测**

**方案3：超时机制**

### 推荐

建议采用**方案1+方案2组合**：同时支持深度限制和循环检测，为用户提供配置灵活性。

---

*Unum AI 安全研究团队*
