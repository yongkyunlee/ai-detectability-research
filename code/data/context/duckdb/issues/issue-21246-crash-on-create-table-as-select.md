# Crash on CREATE TABLE AS SELECT

**Issue #21246** | State: closed | Created: 2026-03-09 | Updated: 2026-03-12
**Author:** johnniemorrow
**Labels:** under review

### What happens?

Hi DuckDB,

I'm seeing an issue with v1.5.0 where I run CREATE TABLE AS SELECT on a large table. Sometimes it works, other times I get an error with:

`free(): corrupted unsorted chunks`

[duckdb_1_5_0_crash_repro.py](https://github.com/user-attachments/files/25851255/duckdb_1_5_0_crash_repro.py)

### To Reproduce

```bash
# setup-start:

docker run -d --name duckdb-1-5-0-crash -p 5433:5432 \
  -e POSTGRES_USER=test -e POSTGRES_PASSWORD=test -e POSTGRES_DB=test \
  postgres:18

docker exec -i duckdb-1-5-0-crash psql -U test -d test <<'SQL'
    CREATE TABLE big_table AS
    SELECT
      i AS id,
      md5(i::text) AS col1,
      md5((i * 2)::text) AS col2,
      md5((i * 3)::text) AS col3,
      now() - (i || ' seconds')::interval AS created_at
    FROM generate_series(1, 100000) AS i;
SQL

# setup-end
```

```bash
# test:
uv run duckdb_1_5_0_crash_repro.py --db-url postgresql://test:test@localhost:5433/test
```

### OS:

Ubuntu Linux

### DuckDB Version:

1.5.0

### DuckDB Client:

Python

### Hardware:

name -a: Linux ubuntu 6.8.0-101-generic #101-Ubuntu SMP PREEMPT_DYNAMIC Fri Feb  6 20:07:40 UTC 2026 aarch64 aarch64 aarch64 GNU/Linux

### Full Name:

John Morrow

### Affiliation:

John Morrow

### Did you include all relevant configuration (e.g., CPU architecture, Linux distribution) to reproduce the issue?

- [x] Yes, I have

### Did you include all code required to reproduce the issue?

- [x] Yes, I have

### Did you include all relevant data sets for reproducing the issue?

Yes

## Comments

**szarnyasg:**
Hi @johnniemorrow, thanks for opening this issue and the reproducer. How commonly do you encounter the issue? I the Python script 100+ times on both macOS and Ubuntu 24.04 and it never crashed.

**johnniemorrow:**
Hi @szarnyasg - so I generated the reproducer with Claude and didn't test it locally which I should have. I can't get that to reproduce it locally either :/

My real setup is not a lot different - the tables are a bit bigger and I have views which the CREATE TABLE FROM SELECT is running on. There are a few different tables in different Postgres schemas. The core is happening consistently with 1.5.0, but not in the same place - sometimes it's on the first table, sometimes on a different table.

I've tried enabling gdb and run that same process 200 times and it's fine under gdb, so maybe it's timing dependent.

I'll see if I can strip my real one down to a smaller reproducible version.

**johnniemorrow:**
@szarnyasg - here's an updated version which crashes consistently, on my machine:

[duckdb_1_5_0_crash_repro.py](https://github.com/user-attachments/files/25855533/duckdb_1_5_0_crash_repro.py)

```bash
# 1. Start PostgreSQL
docker run -d --name duckdb-1-5-0-crash -p 5433:5432 \
  -e POSTGRES_USER=test -e POSTGRES_PASSWORD=test -e POSTGRES_DB=test \
  postgres:18

# 2. Wait for postgres to be ready
sleep 3

# 3. Run the repro
uv run duckdb_1_5_0_crash_repro.py --db-url postgresql://test:test@localhost:5433/test

# 4. Cleanup
docker rm -f duckdb-1-5-0-crash

```

It looks like it's happening at the create index step, not the create table as select:

```bash
$ uv run duckdb_1_5_0_crash_repro.py --db-url postgresql://test:test@localhost:5433/test
Populating test table (50k rows)...
SELECT 50000
Done populating.
CREATE TABLE AS SELECT * FROM pg.data (50k rows)...
  OK
CREATE INDEX on (col_a, col_b)...
free(): corrupted unsorted chunks
```

**taniabogatsch:**
Hi @johnniemorrow - I tried to extract a minimal reproducer from your Postgres + Python scripts for our SQLogicTest framework. It does crash like so: 

```sql
require parquet

statement ok
SET checkpoint_threshold = '10.0 GB';

statement ok
ATTACH '__TEST_DIR__/prefix_transform.db' AS db (STORAGE_VERSION 'v1.0.0');

statement ok
CREATE TABLE db.data AS
SELECT
    i AS id,
    md5(i::text) AS col_a,
    md5((i * 2)::text) AS col_b
FROM generate_series(1, 50000) AS t(i);

statement ok
CREATE INDEX idx_data ON db.data (col_a, col_b);

statement ok
CHECKPOINT db;
```

```
unittest(47167,0x201d22240) malloc: Heap corruption detected, free list is damaged at 0x6000014600a0
*** Incorrect guard value: 4366091360
unittest(47167,0x201d22240) malloc: *** set a breakpoint in malloc_error_break to debug
```

The error does not match `free(): corrupted unsorted chunks`, but I am guessing that we're still looking at the same issue, and you're just seeing the memory issue surface differently.

[If I apply the changes in this PR](https://github.com/duckdb/duckdb/pull/21270), then the test no longer crashes for me. Would you mind running your repro with that PR/patch applied to check if it indeed fixes the issue on your end? Cheers, Tania

**johnniemorrow:**
Hi @taniabogatsch - I don't have an easy way to build the Python package from this branch since tools/pythonpkg isn't present. Happy to test once a pre-built wheel or nightly is available with this fix, or if there's another way let me know.

**taniabogatsch:**
Waiting for the nightly sounds good! :)

**taniabogatsch:**
PR got merged so should be available in the next nightly.

**johnniemorrow:**
Thanks @taniabogatsch - I'll keep an eye out on https://pypi.org/project/duckdb/#history and re-test whenever a new release appears
