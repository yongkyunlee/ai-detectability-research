# INTERNAL Error: Failed to bind column reference (inequal types)

**Issue #21340** | State: closed | Created: 2026-03-12 | Updated: 2026-03-18
**Author:** tlinhart
**Labels:** reproduced

### What happens?

When a subquery (or CTE) contains a window function whose `PARTITION BY` clause references columns of different types, and the outer query applies `GROUP BY` on one of those columns, DuckDB 1.5.0 throws an internal assertion error:

```
INTERNAL Error: Failed to bind column reference "c" [18.1]: inequal types (VARCHAR != INTEGER)
```

The same query works correctly on DuckDB 1.4.4.

### To Reproduce

```sql
CREATE TABLE t(a INT, b INT, c VARCHAR);
INSERT INTO t VALUES (1, 100, 'x'), (2, 200, 'y');

-- Example 1
SELECT c, avg(b)
FROM (
    SELECT * FROM t
    QUALIFY row_number() OVER (PARTITION BY a, c ORDER BY b DESC) = 1
) sub
GROUP BY c;

-- Example 2
SELECT c, avg(b)
FROM (
    SELECT *, row_number() OVER (PARTITION BY a, c ORDER BY b DESC) AS rn
    FROM t
) sub
WHERE rn = 1
GROUP BY c;

-- Example 3
WITH sub AS (
    SELECT * FROM t
    QUALIFY row_number() OVER (PARTITION BY a, c ORDER BY b DESC) = 1
)
SELECT c, avg(b) FROM sub GROUP BY c;
```

Running this results in this kind of error:

```
INTERNAL Error:
Failed to bind column reference "c" [18.1]: inequal types (VARCHAR != INTEGER)

Stack Trace:

duckdb() [0xa7c10b]
duckdb() [0xa7c1c4]
duckdb() [0xa7f231]
duckdb() [0xca7d59]
duckdb() [0x4b11fa]
duckdb() [0x1245a7f]
duckdb() [0x12477e1]
duckdb() [0x1247e92]
duckdb() [0xc92f96]
duckdb() [0x125347d]
duckdb() [0xc92f8b]
duckdb() [0x125347d]
duckdb() [0xc92f8b]
duckdb() [0x125347d]
duckdb() [0xc92f8b]
duckdb() [0x125347d]
duckdb() [0xc92f8b]
duckdb() [0xc9397b]
duckdb() [0xc93b3a]
duckdb() [0xd64104]
duckdb() [0xd64ba3]
duckdb() [0xd67b36]
duckdb() [0xd67f60]
duckdb() [0xd68185]
duckdb() [0xd68d89]
duckdb() [0xd6b307]
duckdb() [0xd6b3f2]
duckdb() [0xd6b4de]
duckdb() [0xd6c19d]
duckdb() [0x85a4e3]
duckdb() [0x85a7f9]
duckdb() [0x85aacb]
duckdb() [0x86566f]
duckdb() [0x8379e1]
/lib/x86_64-linux-gnu/libc.so.6(+0x2a1ca) [0x74748e42a1ca]
/lib/x86_64-linux-gnu/libc.so.6(__libc_start_main+0x8b) [0x74748e42a28b]
duckdb() [0x83d8be]

This error signals an assertion failure within DuckDB. This usually occurs due to unexpected conditions or errors in the program's logic.
For more information, see https://duckdb.org/docs/stable/dev/internal_errors
```

### OS:

Linux (Ubuntu 24.04.4 LTS), x86_64

### DuckDB Version:

v1.5.0 (Variegata) 3a3967aa81

### DuckDB Client:

CLI

### Hardware:

_No response_

### Full Name:

Tomáš Linhart

### Affiliation:

–

### Did you include all relevant configuration (e.g., CPU architecture, Linux distribution) to reproduce the issue?

- [x] Yes, I have

### Did you include all code required to reproduce the issue?

- [x] Yes, I have

### Did you include all relevant data sets for reproducing the issue?

Yes

## Comments

**Mytherin:**
Thanks - should be fixed in https://github.com/duckdb/duckdb/pull/21428
