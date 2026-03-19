# INTERNAL Error: row_number() with multi-column PARTITION BY causes incorrect column type binding

**Issue #21387** | State: open | Created: 2026-03-15 | Updated: 2026-03-15
**Author:** shauneccles
**Labels:** reproduced

## What happens?

After filtering on `row_number()` output, DuckDB binds a column's type to the `ORDER BY` column's type instead of the column's actual type, causing an `INTERNAL Error`.

## To Reproduce

```sql
create table t (a varchar, ts timestamp, k varchar);
insert into t values ('x', '2024-01-01', 'abc'), ('y', '2024-02-01', 'def');

-- Verify column types
select typeof(k) from t limit 1;  -- VARCHAR

-- BUG: fails with INTERNAL Error
with deduped as (
    select k,
           row_number() over (partition by a, k order by ts desc) as rn
    from t
)
select k from deduped where rn = 1;
```

**Error:**

```
INTERNAL Error: Failed to bind column reference "k" [N.1]: inequal types (VARCHAR != TIMESTAMP)
```

**Expected:** Returns 2 rows (`abc`, `def`). Column `k` is VARCHAR — no TIMESTAMP involvement.

## Analysis

All four conditions are required — removing **any one** prevents the error:

| # | Condition | Removing it fixes the error |
|---|-----------|----------------------------|
| 1 | `row_number()` | `rank()` and `dense_rank()` work fine |
| 2 | Multi-column `PARTITION BY` (e.g. `partition by a, k`) | Single-column partition works |
| 3 | `ORDER BY` on a non-VARCHAR column (e.g. TIMESTAMP) | `ORDER BY` on a VARCHAR column works; omitting `ORDER BY` works |
| 4 | `WHERE rn = ` filter on the window output | Removing the filter works |

Additional observations:
- The outer query doesn't matter: `SELECT *`, `SELECT k`, `GROUP BY k` all fail equally.
- Any non-VARCHAR `ORDER BY` type reproduces: TIMESTAMP, DATE, INTEGER.
- The issue occurs with plain tables (no views, no CTEs needed for the source).
- The binder appears to resolve `k`'s type from the `ORDER BY` column's type rather than the column's actual declared type.

## Verification queries (all pass when run individually)

```sql
-- rank() instead of row_number(): works
with d as (select k, rank() over (partition by a, k order by ts desc) as rn from t)
select k from d where rn = 1;

-- single-column partition: works
with d as (select k, row_number() over (partition by k order by ts desc) as rn from t)
select k from d where rn = 1;

-- ORDER BY varchar column: works
with d as (select k, row_number() over (partition by a, k order by a desc) as rn from t)
select k from d where rn = 1;

-- no filter: works
with d as (select k, row_number() over (partition by a, k order by ts desc) as rn from t)
select k from d;
```

## OS

Windows 11 (10.0.26200)

## DuckDB Version

v1.5.0

## DuckDB Client

Python (`import duckdb`)

## Hardware

x86_64
