# Show HN: A Base44-style builder for data workflows (DuckDB-powered)

**HN** | Points: 2 | Comments: 1 | Date: 2026-01-10
**Author:** vibecoding101
**HN URL:** https://news.ycombinator.com/item?id=46562425
**Link:** https://www.gptbeyond.com/try

I kept rebuilding the same CSV workflows (reconciling exports, creating aging schedules, stitching months together), so I built a small browser-only experiment.This lets you build full, node-based data workflows powered by DuckDB — all running entirely in the browser.You can:
- Upload CSVs
- Create and connect nodes
- Reconcile datasets
- Build aging schedules
- Ask questions in plain English and see the DuckDB SQL generated live with full workflows
- Inspect and modify the SQL at every stepThink “Base44-style UX,” but for data workflows instead of apps.This is intentionally early:
- CSV-only
- No persistence
- Usage is cappedBut I’m curious whether this workflow-first approach is useful or a dead end.https:&#x2F;&#x2F;www.gptbeyond.comFeedback very welcome — especially missing primitives, UX issues, or workflows you wish this supported.

## Top Comments

**vibecoding101:**
Quick clarification based on a few DMs&#x2F;questions:This isn’t just “explore a CSV” — you can build full, interactive workflows (with AI) by connecting nodes (joins, transforms, reconciliations, agings, etc.), and inspect&#x2F;modify the DuckDB SQL at every step.Still very early and intentionally constrained (CSV-only, no persistence), but I’m especially interested in:
- workflows people repeat monthly
- primitives that feel missing
- points where the node model breaks downAppreciate the thoughtful feedback so far.
