# langchain-exa: update default search type from neural to auto

**Issue #36083** | State: open | Created: 2026-03-18 | Updated: 2026-03-18
**Author:** theishangoswami
**Labels:** external

The Exa retriever currently defaults to `neural` search type, but `auto` is now the recommended default. The `auto` type lets the Exa API pick the best search strategy for each query.

Changes:
- Update default `type` in `ExaSearchRetriever` from `neural` to `auto`
- Reorder the `type` Literal in `ExaSearchResults` tool to put `auto` first
- Small description update to mention Exa is a web search API built for AI

These are small changes and I can open a PR if this gets approved.
