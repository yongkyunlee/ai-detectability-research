# duckdb 1.5: Issue with struct and write ahead log

**Issue #21100** | State: closed | Created: 2026-02-26 | Updated: 2026-03-03
**Author:** gishor
**Labels:** reproduced

### What happens?

We found a bug that seems related to the write ahead log while testing duckdb 1.5. The output of the same query changes after executing `CHECKPOINT`.

### To Reproduce

This fails in your unittest framework.

```sql
load __TEST_DIR__/test_wal_struct_null.db

statement ok
PRAGMA disable_checkpoint_on_shutdown

statement ok
SET wal_autocheckpoint='1TB'

statement ok
CREATE TABLE t(
    data STRUCT(a INTEGER)
)

statement ok
INSERT INTO t VALUES (NULL)

statement ok
CHECKPOINT

statement ok
UPDATE t SET data = {'a': 7}

restart

# Uncommenting this fixes it.
#statement ok
#CHECKPOINT

# Bug, actually returns 0
query I
SELECT COUNT(*) FROM t WHERE data IS NOT NULL
----
1

statement ok
CHECKPOINT

# Correct
query I
SELECT COUNT(*) FROM t WHERE data IS NOT NULL
----
1
```

### OS:

Mac ARM

### DuckDB Version:

DuckDB v1.5.0-dev7500 (Development Version, 461ef9e350)

### DuckDB Client:

cli

### Hardware:

_No response_

### Full Name:

Gishor Sivanrupan

### Affiliation:

Exaforce

### Did you include all relevant configuration (e.g., CPU architecture, Linux distribution) to reproduce the issue?

- [x] Yes, I have

### Did you include all code required to reproduce the issue?

- [x] Yes, I have

### Did you include all relevant data sets for reproducing the issue?

Not applicable - the reproduction does not require a data set

## Comments

**arup-chauhan:**
@carlopi  @gishor I can take this on. I’ll reproduce on `v1.5` dev, add a regression test, and then work on the `WAL` replay/`CHECKPOINT` fix for updates from `NULL` to non-`NULL` in a `STRUCT` column.

**carlopi:**
I think this has now been solved in `v1.5-variegata`, relevant PR is https://github.com/duckdb/duckdb/pull/21112
