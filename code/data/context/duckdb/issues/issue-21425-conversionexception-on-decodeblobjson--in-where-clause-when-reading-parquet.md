# ConversionException on decode(BLOB)::JSON->> in WHERE clause when reading Parquet

**Issue #21425** | State: closed | Created: 2026-03-17 | Updated: 2026-03-18
**Author:** Shawyeok
**Labels:** reproduced

### What happens?

When querying a Parquet file that contains a `BLOB` column storing JSON, using `decode(col)::JSON->>'$.key' = ?` as a `WHERE` condition **after any `BIGINT` range predicate** (`col >= ? AND col = ?` range filter **precedes** the JSON condition — even with a dummy `1=1` in between.
- Moving the JSON condition **before** the BIGINT range filter avoids the bug.
- Using `json_extract_string()` instead of `::JSON->>` avoids the bug regardless of clause order.

This appears to be a type inference / predicate pushdown issue during Parquet scan optimization.

### To Reproduce

```python
import duckdb, tempfile, os

tmp = tempfile.mktemp(suffix='.parquet')
conn = duckdb.connect()

# Create a Parquet file with a BIGINT column and a BLOB column containing JSON
conn.execute("""
CREATE TABLE fake AS
SELECT
    (1773525600000 + i * 1000)::BIGINT AS publish_time,
    printf('{"topic":"user","key":"%d","send_time":%d}', 1000000 + i, 1773525600000 + i * 1000)::BLOB AS data
FROM range(1000) t(i)
""")
conn.execute(f"COPY fake TO '{tmp}' (FORMAT parquet)")

# ❌ FAILS: JSON filter after BIGINT range filter
conn.execute(
    "SELECT count(*) FROM read_parquet(?) WHERE publish_time >= ? AND publish_time >'$.key' = ?",
    [[tmp], 0, 9999999999999, '1000001']
).fetchone()

os.unlink(tmp)
```

### Error

```
duckdb.duckdb.ConversionException: Conversion Error: Failed to cast value to numerical: {"topic":"user","key":"1000999","send_time":1773525999000}

LINE 1: ... WHERE publish_time >= ? AND publish_time >'$.key' = ?
                                                                          ^
```

### Behaviour Matrix

| Query | Result |
|---|---|
| `WHERE decode(data)::JSON->>'$.key' = ?` (alone) | ✅ OK |
| `WHERE decode(data)::JSON->>'$.key' = ? AND publish_time >= ? AND publish_time = ? AND publish_time >'$.key' = ?` | ❌ FAIL |
| `WHERE 1=1 AND decode(data)::JSON->>'$.key' = ?` | ❌ FAIL |
| `WHERE 1=1 AND publish_time >= ? AND publish_time >'$.key' = ?` | ❌ FAIL |
| `WHERE publish_time >= ? AND publish_time >'$.key' = ?` | ❌ FAIL |
| `WHERE publish_time >= ? AND publish_time >` expression.

### Workaround

Use `json_extract_string()` instead of `::JSON->>`:

```python
# ✅ WORKS regardless of clause order
conn.execute(
    "SELECT count(*) FROM read_parquet(?) WHERE publish_time >= ? AND publish_time >'$.path'` and `json_extract_string(decode(col), '$.path')` should produce identical results regardless of WHERE clause predicate order.

### OS:

macOS, aarch64

### DuckDB Version:

1.5.0

### DuckDB Client:

1.5.0

### Hardware:

_No response_

### Full Name:

N/A

### Affiliation:

N/A

### Did you include all relevant configuration (e.g., CPU architecture, Linux distribution) to reproduce the issue?

- [x] Yes, I have

### Did you include all code required to reproduce the issue?

- [x] Yes, I have

### Did you include all relevant data sets for reproducing the issue?

Yes

## Comments

**Mytherin:**
Thanks for reporting!

This is an odd issue - but it has to do with operator precedence of `->>`. Effectively `->>` has higher precedence than `AND` in the current parser, so your predicate parses like this:

```sql
SELECT count(*) FROM read_parquet('json_blob.parquet')
WHERE (publish_time >= 0 AND publish_time >'$.key' = 1000001;
```

The system then tries to convert `decode(data)::JSON` to a boolean, which fails.

See also https://github.com/duckdb/duckdb/issues/14889

This is a long-standing pitfall that was caused by interaction between the JSON operators and the lambda function syntax. We have since deprecated the lambda function syntax involving arrows and are moving towards fixing this issue, but due to backwards compatibility issues this will take 1-2 more releases.

For now you can add explicit brackets to fix the issue:

```sql
SELECT count(*) FROM read_parquet('json_blob.parquet')
WHERE publish_time >= 0 AND publish_time >'$.key') = 1000001;

```
