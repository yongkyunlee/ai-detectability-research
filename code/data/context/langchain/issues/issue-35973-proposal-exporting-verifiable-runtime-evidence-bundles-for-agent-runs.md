# Proposal: Exporting verifiable runtime evidence bundles for agent runs

**Issue #35973** | State: open | Created: 2026-03-16 | Updated: 2026-03-18
**Author:** joy7758
**Labels:** external

Hi LangChain team,

We recently implemented an experimental runtime evidence layer called AEP (Agent Evidence Profile).

The goal is to package autonomous agent runs into integrity-verifiable evidence bundles rather than plain logs.

Pipeline:

real runtime execution → evidence bundle export → offline verification → deterministic tamper detection

Repository:
https://github.com/joy7758/agent-evidence

Artifact DOI:
https://doi.org/10.5281/zenodo.19055948

A LangChain integration already exists via callback hooks.

Question:

Would it make sense for agent frameworks to expose a standardized runtime evidence export hook, similar to tracing callbacks but producing verifiable evidence artifacts?

Curious whether the LangChain team sees value in bridging observability traces with verifiable runtime evidence objects.

## Comments

**joy7758:**
Hi maintainers — thanks for the issue workflow guidance.

I opened a minimal example-only PR here:
https://github.com/langchain-ai/langchain/pull/35974

Could someone assign this issue to me if the direction looks reasonable? The PR just demonstrates a callback-based runtime evidence export path and does not propose any LangChain internal API changes.

**maxsnow651-dev:**
Yes u can do that

On Mon, Mar 16, 2026, 8:59 PM Bin Zhang ***@***.***> wrote:

> *joy7758* left a comment (langchain-ai/langchain#35973)
> 
>
> Hi maintainers — thanks for the issue workflow guidance.
>
> I opened a minimal example-only PR here:
> #35974 
>
> Could someone assign this issue to me if the direction looks reasonable?
> The PR just demonstrates a callback-based runtime evidence export path and
> does not propose any LangChain internal API changes.
>
> —
> Reply to this email directly, view it on GitHub
> ,
> or unsubscribe
> 
> .
> You are receiving this because you are subscribed to this thread.Message
> ID: ***@***.***>
>

**joy7758:**
Great — thanks for confirming.

I’ll proceed by iterating on the callback-based export path and turning it into a minimal, stable “runtime evidence bundle” pattern.

Next steps from my side:
- refine the example into a clearer export contract (steps / hashes / bundle structure)
- align it with existing tracing concepts where possible
- document a minimal validation/verification flow

I’ll keep updates in this issue as I converge on a more concrete shape.

If there are any constraints or directions you’d prefer (e.g. staying fully external vs. potential future hooks), happy to align early.

**joy7758:**
Thanks — I’ve now written up a minimal external-first, callback-based runtime evidence bundle shape to make the export path more reviewable.

The focus is deliberately narrow:
- steps
- hashes
- bundle structure

Useful mainly as a small discussion artifact for export shape, not as a formal or adopted interface.

Links:
- Contract: https://github.com/joy7758/agent-evidence/blob/feat/openai-agents-exporter/docs/contracts/runtime-evidence-export-contract.md
- Minimal example: https://github.com/joy7758/agent-evidence/blob/feat/openai-agents-exporter/examples/runtime-evidence/runtime-evidence-bundle.minimal.json

**maxsnow651-dev:**
Appreciate the detailed report

On Tue, Mar 17, 2026, 10:09 AM Bin Zhang ***@***.***> wrote:

> *joy7758* left a comment (langchain-ai/langchain#35973)
> 
>
> Thanks — I’ve now written up a minimal external-first, callback-based
> runtime evidence bundle shape to make the export path more reviewable.
>
> The focus is deliberately narrow:
>
>    - steps
>    - hashes
>    - bundle structure
>
> Useful mainly as a small discussion artifact for export shape, not as a
> formal or adopted interface.
>
> Links:
>
>    - Contract:
>    https://github.com/joy7758/agent-evidence/blob/feat/openai-agents-exporter/docs/contracts/runtime-evidence-export-contract.md
>    - Minimal example:
>    https://github.com/joy7758/agent-evidence/blob/feat/openai-agents-exporter/examples/runtime-evidence/runtime-evidence-bundle.minimal.json
>
> —
> Reply to this email directly, view it on GitHub
> ,
> or unsubscribe
> 
> .
> You are receiving this because you commented.Message ID:
> ***@***.***>
>
