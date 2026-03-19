# [1.5] Non-interactive usage of CLI does not work anymore

**Issue #21243** | State: closed | Created: 2026-03-09 | Updated: 2026-03-12
**Author:** ced75
**Labels:** reproduced

### What happens?

It seems that non-interactive usage of CLI is broken with DuckDB 1.5.
If I call a valid (working with DuckDB 1.4.4) SQL script, nothing seems to be executed and no error message is displayed.

### To Reproduce

Create a SQL script, named test.sql for example.

Launch it:
```duckdb < test.sql```
Nothing happens.

### OS:

Ubuntu 24.04

### DuckDB Version:

1.5

### DuckDB Client:

DuckDB CLI 1.5

### Hardware:

_No response_

### Full Name:

Cedric

### Affiliation:

IGN

### Did you include all relevant configuration (e.g., CPU architecture, Linux distribution) to reproduce the issue?

- [x] Yes, I have

### Did you include all code required to reproduce the issue?

- [x] Yes, I have

### Did you include all relevant data sets for reproducing the issue?

Not applicable - the reproduction does not require a data set

## Comments

**carlopi:**
I have the solution (https://github.com/duckdb/duckdb/pull/21247), and 2 workarounds for now:
```
DUCKDB_NO_HIGHLIGHT=1 ./build/release/duckdb < test.sql
```
or
```
./build/release/duckdb < test.sql | cat
```
I guess either of them could work as temporary workaround, this is to be fixed properly in v1.5.1.

**szarnyasg:**
Hi @ced75, thanks for reporting this!

**I wrote this up in our documentation and presented workarounds:** https://duckdb.org/docs/current/guides/troubleshooting/command_line

--

@carlopi the first proposed workaround does not work for me on Linux/macOS, so I omitted it from the guide.

```sql
DUCKDB_NO_HIGHLIGHT=1 ./build/release/duckdb < test.sql
```
