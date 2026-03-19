# Relax tokenizers version constraint to support transformers >=4.51

**Issue #4268** | State: closed | Created: 2026-01-23 | Updated: 2026-03-11
**Author:** aksgibm
**Labels:** no-issue-activity

## Problem

The current `tokenizers~=0.20.3` constraint in crewAI prevents using recent versions of `transformers` (4.51+), which require `tokenizers>=0.21`.

```
transformers 4.53.3 requires tokenizers=0.21, but crewai requires tokenizers~=0.20.3
```

## Analysis

After investigating the crewAI codebase:

1. **crewAI does not directly import or use tokenizers** - no `import tokenizers` or `from tokenizers` found in the source
2. **tokenizers is listed as a direct dependency** but appears to be a transitive constraint
3. **chromadb 1.1.0** (which crewAI uses) only requires `tokenizers>=0.13.2` with no upper bound
4. **PR #2784** moved tokenizers to optional dependency for `docling` extra, but the core constraint remains

## Proposed Solution

Change in `lib/crewai/pyproject.toml`:

```diff
- tokenizers~=0.20.3
+ tokenizers>=0.20.3
```

This would allow crewAI to work with both older and newer versions of transformers.

## Impact

This change would enable users to use:
- transformers 4.51+ (which requires tokenizers >=0.21)
- Latest sentence-transformers
- Other ML libraries that depend on recent tokenizers

## Related

- Issue #2782 - Originally reported this conflict
- PR #2784 - Partially addressed by making tokenizers optional for docling

## Environment

- crewai: 1.7.1
- transformers: 4.53.3 (cannot install due to conflict)
- Python: 3.11

## Comments

**joaquinariasco-lab:**
Hi @aksgibm ,

I saw your analysis on the tokenizers vs transformers conflict in CrewAI. That kind of deep dive into transitive dependencies is exactly what’s missing in the current agentic stack to make it production-ready.

I’m building an automated global economy, not just another framework, but a layer where agents from any background (CrewAI, AutoGen, or custom) can interact without these versioning nightmares. We are focusing heavily on environment isolation and modularity so that the "dependency hell" you're solving doesn't stop the economy from scaling.

We have an MVP that handles agent-to-agent transactions and problem-solving. Given your skill in making complex ML ecosystems work together, I’d love for you to see how we’re structuring our orchestration layer.

Would you be open to a quick look at the repo? I think your approach to "unblocking" the stack aligns perfectly with our vision.

Best,

Joaquin

**github-actions[bot]:**
This issue is stale because it has been open for 30 days with no activity. Remove stale label or comment or this will be closed in 5 days.

**github-actions[bot]:**
This issue was closed because it has been stalled for 5 days with no activity.
