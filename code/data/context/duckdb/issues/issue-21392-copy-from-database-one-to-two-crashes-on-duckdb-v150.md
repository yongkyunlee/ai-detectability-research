# `COPY FROM DATABASE one TO two` crashes on DuckDB v1.5.0

**Issue #21392** | State: open | Created: 2026-03-15 | Updated: 2026-03-16
**Author:** its-felix
**Labels:** fixed on nightly

### What happens?

When copying my database using the `COPY FROM DATABASE ... TO ...` command in DuckDB v1.5.0, DuckDB crashes after a couple minutes.

What I have tried:
- Attach the source database with the `READ_ONLY` option
- `SET threads TO 1` before issueing the copy command
- `CALL enable_logging()` - no logs printed

This happens both locally on my MacBook Pro M1 (using DuckDB CLI + UI) and on ECS Fargate (ARM) (using duckdb-go). On my MacBook, DuckDB used up to 15 GB (of 32 GB total) after around 3 minutes. Total memory usage of the system at this point was at 25 GB.

The only message which appears on the CLI on Mac is: `zsh: trace trap`

On ECS Fargate (using duckdb-go) there is a go-stacktrace and the first message being `free(): chunks in smallbin corrupted`. The full stacktrace seems to contain some parts of memory (r0 - r29, lr, sp, pc) of which I'm not sure if they might contain senstive data.

### To Reproduce

I can not provide the Database File directly on GitHub (its roughly 5.5 GB in size). I can share it with contributors via e-mail / link if requested.

```sql
ATTACH 'flights.db' AS flights (READ_ONLY) ;
ATTACH 'dst.db' AS dst ;
SET threads TO 1 ;
COPY FROM DATABASE flights TO dst ;
```

### OS:

macOS, Linux

### DuckDB Version:

v1.5.0

### DuckDB Client:

CLI, duckdb-go

### Hardware:

MacBook Pro M1, ECS Fargate (ARM)

### Full Name:

Felix Wollschlaeger

### Affiliation:

N/A

### Did you include all relevant configuration (e.g., CPU architecture, Linux distribution) to reproduce the issue?

- [x] Yes, I have

### Did you include all code required to reproduce the issue?

- [x] Yes, I have

### Did you include all relevant data sets for reproducing the issue?

No - I cannot easily share my data sets due to their large size

## Comments

**its-felix:**
It works on nightly (`v1.5-dev`) downloaded from https://duckdb.org/install/preview

**Mytherin:**
Thanks for reporting - this might be related to an index bug that was already fixed in https://github.com/duckdb/duckdb/pull/20455 which is why I suspect it works in the nightly build. The fix will land as part of v1.5.1.
