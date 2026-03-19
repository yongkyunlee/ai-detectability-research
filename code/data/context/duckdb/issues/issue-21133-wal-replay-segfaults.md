# WAL replay segfaults

**Issue #21133** | State: closed | Created: 2026-03-02 | Updated: 2026-03-02
**Author:** dentiny
**Labels:** under review

### What happens?

Rough repro steps (see below repro SQL) 
- Disable / delay automatic checkpoint
- Create table A, populates a few rows and delete
- Create table B, populates a few rows and closes the database
- Restart the database leads to segfault, if table A and B have different schema

### To Reproduce

```sql
# name: test/sql/storage/wal/wal_block_reuse_after_drop.test
# description: Verify blocks freed by DROP TABLE are not reused before WAL truncation
# group: [wal]

load __TEST_DIR__/wal_block_reuse.db

statement ok
PRAGMA disable_checkpoint_on_shutdown

statement ok
PRAGMA wal_autocheckpoint='1TB'

# Force row groups to flush immediately so WAL stores block pointers
statement ok
SET write_buffer_row_group_count=1

# Create table with PRIMARY KEY (forces block reads during WAL replay)
statement ok
CREATE TABLE t (a BIGINT PRIMARY KEY, b VARCHAR, c VARCHAR, d VARCHAR)

# Insert data - allocates blocks, WAL records block pointers
statement ok
INSERT INTO t SELECT i, 
  'row_' || i || repeat('x', 20), 
  'data_' || i || repeat('y', 30), 
  'col_' || i || repeat('z', 25) 
FROM generate_series(0, 99999) t(i)

# Drop table - frees blocks
statement ok
DROP TABLE t

# Create new table with different schema (DOUBLE vs VARCHAR)
statement ok
CREATE TABLE t2 (a DOUBLE, b DOUBLE, c DOUBLE, d DOUBLE)

# Insert into new table - would reuse freed blocks if bug exists
statement ok
INSERT INTO t2 SELECT 
  i * 3.14159, i * 2.71828, i * 1.41421, i * 1.73205 
FROM generate_series(0, 499999) t(i)

# Restart triggers WAL replay
# WAL contains: CREATE t, INSERT t, DROP t, CREATE t2, INSERT t2
# If blocks were prematurely reused, replaying INSERT t reads corrupted data
restart

query I
SELECT COUNT(*) FROM t2
----
500000

query R
SELECT a FROM t2 WHERE rowid = 0
----
0.000000
```

### OS:

ubuntu

### DuckDB Version:

0ae55359dd269c354022fb9902be34aa491d797b

### DuckDB Client:

C++

### Hardware:

_No response_

### Full Name:

dentiny

### Affiliation:

N/A

### Did you include all relevant configuration (e.g., CPU architecture, Linux distribution) to reproduce the issue?

- [x] Yes, I have

### Did you include all code required to reproduce the issue?

- [x] Yes, I have

### Did you include all relevant data sets for reproducing the issue?

Yes

## Comments

**dentiny:**
Tania mentioned a concurrent C++ test to repro, single threaded SQL should suffice.
Working on it https://github.com/dentiny/duckdb/pull/57
