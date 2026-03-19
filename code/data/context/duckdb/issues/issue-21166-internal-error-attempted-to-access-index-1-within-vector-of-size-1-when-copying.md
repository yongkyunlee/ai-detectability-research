# INTERNAL Error: "Attempted to access index 1 within vector of size 1" when COPYing PLAIN_DICTIONARY STRUCT(LIST<STRUCT>) column with predicate pushdown

**Issue #21166** | State: open | Created: 2026-03-04 | Updated: 2026-03-04
**Author:** KumoSiunaus
**Labels:** reproduced

## Summary

DuckDB 1.2.1 (latest nightly may also be affected; confirmed on 1.2.1 ARM64) raises an `InternalException` when using `COPY ... TO` on a query that:

1. Reads a `STRUCT(result LIST>, ...)` column encoded with **PLAIN_DICTIONARY**
2. Applies a **predicate pushdown** (`WHERE id = X`) that selects the **first non-null row immediately after a large contiguous null block** (≥53,000 nulls) within a row group

## Minimal Reproduction

```python
"""
Minimal reproduction for DuckDB bug:
  INTERNAL Error: Attempted to access index 1 within vector of size 1
"""

import duckdb
import pyarrow.parquet as pq

REPRO_FILE = "repro_input.parquet"
OUTPUT_FILE = "repro_output.parquet"

# Step 1: Create trigger file
# Key conditions:
#   - Row group size >= ~120,000 rows
#   - Large contiguous null block (>=53,000 rows) in a STRUCT(LIST) column, mid-row-group
#   - Target row is the FIRST non-null row immediately after the null block
#   - Enough distinct non-null values to trigger PLAIN_DICTIONARY encoding
setup_conn = duckdb.connect()
setup_conn.execute(f"""
COPY (
    SELECT
        i AS id,
        CASE WHEN i >= 59392 AND i )` column, the Dremel decoder **misreads the definition level at the null→non-null page boundary**, incorrectly marking the row as `NULL` at the outer struct level.

Evidence:

```sql
-- Returns NULL  (wrong — predicate pushdown active)
SELECT col IS NULL FROM 'repro_input.parquet' WHERE id = 112640;

-- Returns false  (correct — full scan, no pushdown)
PRAGMA disable_optimizer;
SELECT col IS NULL FROM 'repro_input.parquet' WHERE id = 112640;
```

Conditions that must all be met:
| Condition | Value |
|-----------|-------|
| Column encoding | PLAIN_DICTIONARY (legacy dict encoding) |
| Null block size | ≥53,000 contiguous nulls |
| Null block position | Mid-row-group (not starting at row 0) |
| Target row | **First** non-null row immediately after the null block |
| Row group size | ≥~120,000 rows |

### Bug 2 — Writer: `ListColumnWriter` Doesn't Guard Against Outer-NULL + Non-Empty Child Vector

After the misread above, the in-memory vector state becomes inconsistent:

```
outer_struct_vector[0].valid = false     ← misread as NULL by the reader
result_list_vector[0] = {offset, length=5}  ← child list still has 5 entries
child_vector.size = 1                    ← only 1 row allocated
```

`ListColumnWriter::Write` sums up `list_entry.length` for all rows (getting 5) and calls the child writer for 5 elements — but the child vector only has 1 row. `PrimitiveColumnWriter` then asserts `index < size` → crash.

The writer should skip child-field writes when the outer struct validity is `false`.

## Workaround

Use DuckDB to read, Polars to write — Polars' parquet writer handles this edge case correctly:

```python
result = conn.execute("SELECT * FROM read_parquet(...) WHERE ...").pl()
result.write_parquet("output.parquet")
```

Alternatively, `PRAGMA disable_optimizer` before the query avoids the misread but disables all optimizations.

## Environment

- DuckDB version: 1.2.1 (confirmed, ARM64; also reported on 1.4.3)
- Python: 3.13
- OS: Linux ARM64
- Install: `pip install duckdb`

## Comments

**szarnyasg:**
Thanks @KumoSiunaus for reporting this. On macOS, v1.4.4 crashes:

```
Encoding: ('PLAIN_DICTIONARY',)
With optimizer (predicate pushdown): col IS NULL = True   ← wrong!
Without optimizer (full scan):       col IS NULL = False  ← correct
CRASH: INTERNAL Error: Attempted to access index 1 within vector of size 1

Stack Trace:

0        duckdb_adbc_init + 3496372
1        duckdb_adbc_init + 3414920
2        duckdb_adbc_init + 19129596
3        duckdb_adbc_init + 14693072
4        duckdb_adbc_init + 14693512
5        duckdb_adbc_init + 14698668
6        duckdb_adbc_init + 14687324
7        duckdb_adbc_init + 14698668
8        duckdb_adbc_init + 15201692
9        duckdb_adbc_init + 15012656
10       duckdb_adbc_init + 5975684
11       duckdb_adbc_init + 5882208
12       duckdb_adbc_init + 5876376
13       duckdb_adbc_init + 7759356
14       duckdb_adbc_init + 7693824
15       duckdb_adbc_init + 7747852
16       duckdb_adbc_init + 7767284
17       _pthread_start + 136
18       thread_start + 8

This error signals an assertion failure within DuckDB. This usually occurs due to unexpected conditions or errors in the program's logic.
For more information, see https://duckdb.org/docs/stable/dev/internal_errors
```

v1.5 shows an `OSError`:

```
Traceback (most recent call last):
  File "/Users/gabor/tmp/reprex/my.py", line 42, in 
    pf = pq.ParquetFile(REPRO_FILE)
  File "/opt/homebrew/lib/python3.14/site-packages/pyarrow/parquet/core.py", line 328, in __init__
    self.reader.open(
    ~~~~~~~~~~~~~~~~^
        source, use_memory_map=memory_map,
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    ......
        arrow_extensions_enabled=arrow_extensions_enabled,
        ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
    )
    ^
  File "pyarrow/_parquet.pyx", line 1656, in pyarrow._parquet.ParquetReader.open
  File "pyarrow/error.pxi", line 92, in pyarrow.lib.check_status
OSError: Malformed schema: not enough ColumnOrder values
```
