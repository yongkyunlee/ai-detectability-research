# UNIQUE constraint doesn't consider column collation

**Issue #19675** | State: open | Created: 2025-11-06 | Updated: 2026-03-18
**Author:** fatalmind
**Labels:** reproduced

### What happens?

A unique (and primary key) constraint allows adding rows with the same value with respect to the relevant collation.

### To Reproduce

```
CREATE TABLE tbl (
    str VARCHAR(255) COLLATE NOCASE UNIQUE
);
INSERT INTO tbl (str) VALUES ('A');
INSERT INTO tbl (str) VALUES ('a'); -- should fail
```

To further verify:
```
D select * from tbl;
┌─────────┐
│   str   │
│ varchar │
├─────────┤
│ A       │
│ a       │
└─────────┘
D select distinct * from tbl;
┌─────────┐
│   str   │
│ varchar │
├─────────┤
│ A       │
└─────────┘
```

### OS:

macOS

### DuckDB Version:

1.4.1 (actually all, I guess)

### DuckDB Client:

cli (via Homebrew), JDBC

### Hardware:

_No response_

### Full Name:

Markus Winand

### Affiliation:

Markus Winand

### Did you include all relevant configuration (e.g., CPU architecture, Linux distribution) to reproduce the issue?

- [x] Yes, I have

### Did you include all code required to reproduce the issue?

- [x] Yes, I have

### Did you include all relevant data sets for reproducing the issue?

Yes

## Comments

**szarnyasg:**
Thanks, I could reproduce the issue. We'll take a look!

**kiran-4444:**
Hey👋, I'd like to take this if it's up for community contributions.

**artjomPlaunov:**
Thanks for the interest @kiran-4444 and @feichai0017, but this is currently being worked on.

**kiran-4444:**
Hey @artjomPlaunov are you still working on this or do you need some help? I'd be happy to take this over.

**artjomPlaunov:**
@kiran-4444 This is currently blocked since it depends on another feature that hasn't been implemented yet, namely lazy binding of constraint indexes, since there are considerations around WAL replay. But in general, that might also end up touching a lot of stuff related to constraints that possibly needs to be reworked. I can ping on this thread when we have lazy binding of constraint indexes implemented though, as I think the actual push collation fix would be pretty straightforward after that.

**kiran-4444:**
> I can ping on this thread when we have lazy binding of constraint indexes implemented

Sure, Thanks!

**artjomPlaunov:**
@kiran-4444 If you want to look into the lazy binding of constraint indexes I could send more more info later, however I should note that depending on the scope/if it ends up being much bigger, it may still end up being something we do on our end. (just let me know if you want me to send info).

**kiran-4444:**
> If you want to look into the lazy binding of constraint indexes I could send more more info later

@artjomPlaunov I'd love that! As someone who loves database internals, this could be something that'll teach me a lot more along the way.

**artjomPlaunov:**
@kiran-4444 cool! 

The basic gist is that we have "unbound" non-constraint indexes during WAL replay. This is because some indexes could depend on expressions that aren't defined until after binding, but during WAL replay we can't bind the indexes yet. So replayed index operations are actually buffered and we do lazy index binding, so whenever the index is bound we will replay the buffered WAL operations to get it into a proper state. 

This is different for constraint indexes which are eagerly bound. The reason this works out right now is because they don't support, for example, pushing an index collation which requires already bound expressions and a client context to do the push, i.e. all the operations can be replayed normally on startup (I think, double check this). Also I think it's strictly for constraints, for example a UNIQUE index created separately is unbound I think, vs a UNIQUE constraint on the table would be what I mention as a "constraint index".

But the bigger issue which I haven't looked into is that since they are constraint indexes, they are (of course) tied into the constraint infrastructure, so it may not be so simple to lazily bind them, i.e. there are probably a lot more considerations here (I think particularly with transaction local storage). This is also why I say there is a decent chance we take this over depending on how involved it actually is (and also probably wont give much direction aside from this), so take it up if you're okay with learning like you mentioned even if you don't get the PR in :-) 

Here is the PR that reworked the buffering/replay for unbound indexes: https://github.com/duckdb/duckdb/pull/19901/changes
Also I think some tests there give an idea of testing WAL replay by not checkpointing on shutdown, when you're running locally and your CI it can save time to run the test suite with various configurations related to WAL replay and the storage_restart configs in test/configurations (and if it's doable/you open up a PR open it on draft and just run CI locally during the review process).

**blakethornton651-art:**
A quick fix could be adjusting this parameter

On Tue, Mar 17, 2026, 6:52 PM artjom_plaunov ***@***.***>
wrote:

> *artjomPlaunov* left a comment (duckdb/duckdb#19675)
> 
>
> @kiran-4444  cool!
>
> The basic gist is that we have "unbound" non-constraint indexes during WAL
> replay. This is because some indexes could depend on expressions that
> aren't defined until after binding, but during WAL replay we can't bind the
> indexes yet. So replayed index operations are actually buffered and we do
> lazy index binding, so whenever the index is bound we will replay the
> buffered WAL operations to get it into a proper state.
>
> This is different for constraint indexes which are eagerly bound. The
> reason this works out right now is because they don't support, for example,
> pushing an index collation which requires already bound expressions and a
> client context to do the push, i.e. all the operations can be replayed
> normally on startup (I think, double check this). Also I think it's
> strictly for constraints, for example a UNIQUE index created separately is
> unbound I think, vs a UNIQUE constraint on the table would be what I
> mention as a "constraint index".
>
> But the bigger issue which I haven't looked into is that since they are
> constraint indexes, they are (of course) tied into the constraint
> infrastructure, so it may not be so simple to lazily bind them, i.e. there
> are probably a lot more considerations here (I think particularly with
> transaction local storage). This is also why I say there is a decent chance
> we take this over depending on how involved it actually is (and also
> probably wont give much direction aside from this), so take it up if you're
> okay with learning like you mentioned even if you don't get the PR in :-)
>
> Here is the PR that reworked the buffering/replay for unbound indexes:
> https://github.com/duckdb/duckdb/pull/19901/changes
> Also I think some tests there give an idea of testing WAL replay by not
> checkpointing on shutdown, when you're running locally and your CI it can
> save time to run the test suite with various configurations related to WAL
> replay and the storage_restart configs in test/configurations (and if it's
> doable/you open up a PR open it on draft and just run CI locally during the
> review process).
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
