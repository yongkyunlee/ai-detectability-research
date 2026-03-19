# `INSERT OR IGNORE` crashes with `SIGTRAP` when inserting from `read_parquet()` into table

**Issue #21254** | State: closed | Created: 2026-03-09 | Updated: 2026-03-11
**Author:** patricktrainer

### What happens?

INSERT OR IGNORE INTO a table with a composite PRIMARY KEY (VARCHAR, TIMESTAMP) crashes the process with SIGTRAP (exit code 133) when the source data comes from read_parquet() over multiple Parquet files (~3M+ rows) and the TIMESTAMP column is produced by TRY_CAST from a string.

No Python exception is raised — the process is killed by the OS signal.

### To Reproduce

```python 
import os, tempfile
import duckdb
import pyarrow as pa
import pyarrow.parquet as pq

NUM_FILES = 7
ROWS_PER_FILE = 500_000
SCHEMA = pa.schema([("id", pa.string()), ("ts", pa.string()), ("value", pa.int32())])

with tempfile.TemporaryDirectory() as tmp:
    # Generate ~3.5M rows across 7 Parquet files
    data_dir = os.path.join(tmp, "data")
    os.makedirs(data_dir)
    for i in range(NUM_FILES):
        table = pa.table({
            "id": [f"k_{(i * ROWS_PER_FILE + j) % (ROWS_PER_FILE * 3)}" for j in range(ROWS_PER_FILE)],
            "ts": [f"2025-01-{(j % 28) + 1:02d}T{j % 24:02d}:{j % 60:02d}:00.{(i * ROWS_PER_FILE + j) % 1000000:06d}" for j in range(ROWS_PER_FILE)],
            "value": list(range(ROWS_PER_FILE)),
        }, schema=SCHEMA)
        pq.write_table(table, os.path.join(data_dir, f"{i}.parquet"))

    glob = os.path.join(data_dir, "*.parquet")
    con = duckdb.connect(os.path.join(tmp, "test.duckdb"))
    con.execute("CREATE TABLE t (id VARCHAR, ts TIMESTAMP, value INTEGER, PRIMARY KEY (id, ts))")

    # This crashes with SIGTRAP (exit code 133)
    con.execute(f"""
        INSERT OR IGNORE INTO t
        SELECT id, TRY_CAST(ts AS TIMESTAMP) AS ts, value
        FROM read_parquet('{glob}')
        WHERE TRY_CAST(ts AS TIMESTAMP) IS NOT NULL
    """)
```

#### What I expected

  The insert completes, skipping rows that conflict on `(id, ts)`.

#### What does NOT crash

  - Same data loaded via `CREATE TABLE AS SELECT DISTINCT ON (id, ts) ...` without a PRIMARY KEY
  - Same schema/query with smaller datasets (~1M rows)
  - Same query without PK on the target table

### OS:

macOS arm64 (Darwin 25.3.0)

### DuckDB Version:

1.5.0

### DuckDB Client:

Python

### Hardware:

_No response_

### Full Name:

Patrick Trainer

### Affiliation:

Big Cartel

### Did you include all relevant configuration (e.g., CPU architecture, Linux distribution) to reproduce the issue?

- [x] Yes, I have

### Did you include all code required to reproduce the issue?

- [x] Yes, I have

### Did you include all relevant data sets for reproducing the issue?

Yes

## Comments

**szarnyasg:**
@patricktrainer Thanks! And also congratulations, this is the first regression bug discovered in 1.5.

This reproduces in the CLI too:

```python
import os, tempfile
import duckdb
import pyarrow as pa
import pyarrow.parquet as pq

print(duckdb.__version__)

NUM_FILES = 7
ROWS_PER_FILE = 500_000
SCHEMA = pa.schema([("id", pa.string()), ("ts", pa.string()), ("value", pa.int32())])

# Generate ~3.5M rows across 7 Parquet files
data_dir = os.path.join("data")
os.makedirs(data_dir)
for i in range(NUM_FILES):
    table = pa.table({
        "id": [f"k_{(i * ROWS_PER_FILE + j) % (ROWS_PER_FILE * 3)}" for j in range(ROWS_PER_FILE)],
        "ts": [f"2025-01-{(j % 28) + 1:02d}T{j % 24:02d}:{j % 60:02d}:00.{(i * ROWS_PER_FILE + j) % 1000000:06d}" for j in range(ROWS_PER_FILE)],
        "value": list(range(ROWS_PER_FILE)),
    }, schema=SCHEMA)
    pq.write_table(table, os.path.join(data_dir, f"{i}.parquet"))

glob = os.path.join(data_dir, "*.parquet")
con = duckdb.connect(os.path.join("test.duckdb"))
con.execute("CREATE TABLE t (id VARCHAR, ts TIMESTAMP, value INTEGER, PRIMARY KEY (id, ts))")

print(f"""
INSERT OR IGNORE INTO t
SELECT id, TRY_CAST(ts AS TIMESTAMP) AS ts, value
FROM read_parquet('{glob}')
WHERE TRY_CAST(ts AS TIMESTAMP) IS NOT NULL
""")

# This crashes with SIGTRAP (exit code 133)
con.execute(f"""
    INSERT OR IGNORE INTO t
    SELECT id, TRY_CAST(ts AS TIMESTAMP) AS ts, value
    FROM read_parquet('{glob}')
    WHERE TRY_CAST(ts AS TIMESTAMP) IS NOT NULL
""")
```

```bash
duckdb test.duckdb
```
```sql
DuckDB v1.5.0 (Variegata)
Enter ".help" for usage hints.
test D     INSERT OR IGNORE INTO t
           SELECT id, TRY_CAST(ts AS TIMESTAMP) AS ts, value
           FROM read_parquet('data/*.parquet')
           WHERE TRY_CAST(ts AS TIMESTAMP) IS NOT NULL;
duckdb(44393,0x1fc14e240) malloc: Heap corruption detected, free list is damaged at 0x60000135fba0
*** Incorrect guard value: 0
duckdb(44393,0x1fc14e240) malloc: *** set a breakpoint in malloc_error_break to debug
[1]    44393 abort      duckdb test.duckdb
```

**taniabogatsch:**
Hi @patricktrainer - thanks for the excellent reproducer, [PR with a fix is up here](https://github.com/duckdb/duckdb/pull/21270).

**patricktrainer:**
Thanks @szarnyasg and @taniabogatsch - glad I could be helpful!

Nice work on the fix! 🦆
