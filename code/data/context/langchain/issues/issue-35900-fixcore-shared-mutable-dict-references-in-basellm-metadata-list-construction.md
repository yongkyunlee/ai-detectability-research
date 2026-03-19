# fix(core): shared mutable dict references in BaseLLM metadata_list construction

**Issue #35900** | State: open | Created: 2026-03-15 | Updated: 2026-03-17
**Author:** roli-lpci
**Labels:** external

## Checked other resources

- [x] This is a bug, not a usage question.
- [x] I searched existing issues and didn't find a duplicate.
- [x] I checked the documentation.

## Description

`BaseLLM.generate()` and `BaseLLM.agenerate()` construct default metadata lists using `[{}] * len(prompts)`:

```python
metadata_list = cast(
    "list[dict[str, Any] | None]", metadata or ([{}] * len(prompts))
)
```

**`[{}] * N` creates N references to the same dict object**, not N independent dicts. If any downstream code mutates one entry's metadata dict, all entries are silently corrupted.

The bug exists in both the sync path (`generate`, line ~948) and the async path (`agenerate`, line ~1212).

### Current impact

Currently latent — `CallbackManager.configure()` reads from these dicts but doesn't mutate them. However, any future code or custom callback handler that writes to per-prompt metadata (e.g., `meta["run_id"] = ...`) would silently affect all prompts in the batch.

### Prior art

This exact pattern has been confirmed and fixed in other frameworks:
- [agno-agi/agno#6811](https://github.com/agno-agi/agno/pull/6811) — streaming tool calls used `[{}] * N`, causing shared dict corruption

The same codebase already uses `copy.deepcopy()` to protect against this in `text-splitters/base.py:121`.

### Proposed fix

Replace `[{}] * len(prompts)` with `[{} for _ in range(len(prompts))]` to create independent dicts.

I have a fix ready with a regression test if this is approved.

## System Info

langchain-core latest (master branch)

## Comments

**gitbalaji:**
Hi, I'd like to work on this. Could a maintainer please assign it to me?

**fairchildadrian9-create:**
Could someone assign me to this I also want to work on it

On Mon, Mar 16, 2026, 7:52 AM Balaji Seshadri ***@***.***>
wrote:

> *gitbalaji* left a comment (langchain-ai/langchain#35900)
> 
>
> Hi, I'd like to work on this. Could a maintainer please assign it to me?
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

**roli-lpci:**
I opened this issue and already have a working fix ready in #35899.

The fix replaces `[{}] * len(prompts)` with `[{} for _ in range(len(prompts))]` in both the sync and async paths of `BaseLLM`. Includes a regression test with a negative control confirming the old pattern was broken.

PR was auto-closed for missing the issue link — now updated with `Fixes #35900` and should reopen. Happy for a maintainer to review.

**roli-lpci:**
Could a maintainer please assign this issue to me? I opened it and already have a working fix in #35899 — the PR was auto-closed due to the missing issue link, now updated with `Fixes #35900`. The fix is tested and ready for review.

**roli-lpci:**
@dosubot @baskaryan @eyurtsev Could a maintainer please assign this to me? I reported this bug, opened this issue, and the fix is already implemented in #35899 — just waiting on assignment to satisfy the bot requirement.

**maxsnow651-dev:**
Assign me please

On Mon, Mar 16, 2026, 4:03 PM Roli Bosch ***@***.***> wrote:

> *roli-lpci* left a comment (langchain-ai/langchain#35900)
> 
>
> @dosubot Bagatur ***@***.***)  Eugene
> Yurtsev ***@***.***)  Could a maintainer
> please assign this to me? I reported this bug, opened this issue, and the
> fix is already implemented in #35899
>  — just waiting on
> assignment to satisfy the bot requirement.
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
