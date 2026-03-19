# duckdb 1.5: Issues around LIMIT

**Issue #21160** | State: closed | Created: 2026-03-03 | Updated: 2026-03-06
**Author:** gishor
**Labels:** reproduced

### What happens?

In this example, we expect one row as a result. However, if we add `LIMIT 10`, we get no row at all. The query plan mentions `TOP_N`. So it might be related to the other Top N window elimination issues in the past weeks? Even though those were fixed.

While trying to minimize the example, I got a `Invalid unicode` error with a similar query. I put it in this issue as it seems like it's the same bug.

### To Reproduce

#### First case:

```sql
statement ok
PRAGMA enable_verification

statement ok
CREATE OR REPLACE TABLE t (id INTEGER, x VARCHAR, y DOUBLE);

statement ok
INSERT INTO t VALUES (1, NULL, NULL);

query I
SELECT id FROM t WHERE x IS NULL ORDER BY y;
----
1

query I
SELECT id FROM t WHERE x IS NULL ORDER BY y LIMIT 10;
----
1
```

returns:
```
================================================================================
Query unexpectedly failed (test/sql/window/foo.test:15)
 (test/sql/window/foo.test:15)!
================================================================================
SELECT id FROM t WHERE x IS NULL ORDER BY y LIMIT 10;
================================================================================
Actual result:
================================================================================
Invalid Error: Unoptimized statement differs from original result!
Original Result:
id
INTEGER
[ Rows: 0]

Unoptimized:
id
INTEGER
[ Rows: 1]
1

---------------------------------
Row count mismatch (0 vs 1)

~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
unittest is a Catch v2.13.7 host application.
Run with -? for options

-------------------------------------------------------------------------------
test/sql/window/foo.test
-------------------------------------------------------------------------------
/Users/gishor/Developer/duckdb/duckdb/test/sqlite/test_sqllogictest.cpp:212
...............................................................................

test/sql/window/foo.test:15: FAILED:
explicitly with message:
  0

[1/1] (100%): test/sql/window/foo.test
===============================================================================
test cases: 1 | 1 failed
assertions: 5 | 4 passed | 1 failed
```

#### Second case:
Everything same except the ORDER BY is by x.
```sql
statement ok
PRAGMA enable_verification

statement ok
CREATE OR REPLACE TABLE t (id INTEGER, x VARCHAR, y DOUBLE);

statement ok
INSERT INTO t VALUES (1, NULL, NULL);

query I
SELECT id FROM t WHERE x IS NULL ORDER BY x;
----
1

query I
SELECT id FROM t WHERE x IS NULL ORDER BY x LIMIT 10;
----
1
```

returns:
```
================================================================================
Query unexpectedly failed (test/sql/window/foo.test:15)
 (test/sql/window/foo.test:15)!
================================================================================
SELECT id FROM t WHERE x IS NULL ORDER BY x LIMIT 10;
================================================================================
Actual result:
================================================================================
Invalid Error: Unoptimized statement differs from original result!
Original Result:
Invalid Input Error: Invalid unicode (byte sequence mismatch) detected in value construction
Unoptimized:
id
INTEGER
[ Rows: 1]
1

~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
unittest is a Catch v2.13.7 host application.
Run with -? for options

-------------------------------------------------------------------------------
test/sql/window/foo.test
-------------------------------------------------------------------------------
/Users/gishor/Developer/duckdb/duckdb/test/sqlite/test_sqllogictest.cpp:212
...............................................................................

test/sql/window/foo.test:15: FAILED:
explicitly with message:
  0

[1/1] (100%): test/sql/window/foo.test
===============================================================================
test cases: 1 | 1 failed
assertions: 5 | 4 passed | 1 failed

```

### OS:

Mac ARM

### DuckDB Version:

DuckDB v1.5.0-dev7565 (Development Version, 6f3da6f556)

### DuckDB Client:

CLI/unittest

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

No - Other reason (please specify in the issue body)

## Comments

**szarnyasg:**
Thanks @gishor, for submitting this issue. This indeed looks incorrect, I'll check with the engineering team.
