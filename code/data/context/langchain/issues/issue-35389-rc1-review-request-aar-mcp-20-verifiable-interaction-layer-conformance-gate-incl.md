# RC1 Review Request: AAR-MCP-2.0 Verifiable Interaction Layer (Conformance Gate included)

**Issue #35389** | State: open | Created: 2026-02-21 | Updated: 2026-03-09
**Author:** joy7758
**Labels:** external

### Proposal: Integrate AAR-MCP-2.0 RC1 (Verifiable Agent Interaction Layer)

I’m publishing **AAR-MCP-2.0 Core Spec (RC1)**: a verifiable interaction layer for MCP/agent tool calls.
It provides **tamper-evident journals + checkpoint signatures + conformance vectors**, and exports an **audit bundle** reviewers can independently verify.

**Why this matters**
- Observability logs are not evidence. We need **non-repudiable action receipts** for high-risk tools (write config, transfer funds, etc.).
- This RC1 focuses on **fail-closed enforcement** and **format-stable verification**, not vendor lock-in.

**RC1 entry (spec bundle + sha256 + conformance gate)**
- Repo: joy7758/aro-audit
- RC1 Review入口已在 README 顶部（含 spec bundle + sha256）
- Conformance Gate: boundary vectors (base OK / attestations-only OK / predicate-tamper FAIL)

**Review workflow**
- Please review via GitHub Discussions:
  - Review Thread #3: https://github.com/joy7758/aro-audit/discussions/3
  - Review Thread #4: https://github.com/joy7758/aro-audit/discussions/4
- Or open an issue using our RC1 review template.

**Ask**
- I’d like feedback on:
  1) Record types + digest boundary definition
  2) Checkpoint semantics (range, merkle root, signature)
  3) Tool-level dependency policy (soft/strict/hard-gate)
  4) Conformance vectors coverage (what’s missing)

If your project exposes MCP tools, I can provide a minimal wrapper and a 30s demo bundle to validate integration.

## Comments

**joy7758:**
[ARO-RC1-FOLLOWUP]
感谢维护！为避免在多个仓库分散讨论，我把所有 RC1 反馈统一收口到这里：
- https://github.com/joy7758/aro-audit/discussions/3
- https://github.com/joy7758/aro-audit/discussions/4

最小验收（1 条命令）：
```bash
./tools/run_conformance.sh
```

如果你愿意进一步评审：
1 看到 `VERIFY_OK` / `VERIFY_FAIL(attack)` 即代表 conformance gate 正常
2) 任何疑问/改动建议请直接贴到 Discussion（或提 PR，我这边会跟进）
COMMENT
)
