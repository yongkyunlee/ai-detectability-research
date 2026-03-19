# INTERNAL Error: TransactionContext::ActiveTransaction in recursive CTE with APPROX_QUANTILE OVER window

**Issue #21354** | State: closed | Created: 2026-03-13 | Updated: 2026-03-13
**Author:** yharby

## What happens
Running a recursive CTE that uses `APPROX_QUANTILE(...) OVER (PARTITION BY ...)` inside the recursive member triggers an internal assertion failure:

```
INTERNAL Error: TransactionContext::ActiveTransaction called without active transaction
```

## To reproduce

```sql
INSTALL spatial; LOAD spatial;
SET geometry_always_xy = true;

-- Create test data
CREATE TABLE test_points AS 
SELECT ST_Point(random() * 360 - 180, random() * 180 - 90) AS geometry
FROM range(1000);

-- Recursive CTE with APPROX_QUANTILE window (KDTree partitioning pattern)
WITH RECURSIVE kdtree_sample AS (
    SELECT
        0 AS iteration,
        ST_X(ST_Centroid(geometry)) AS x,
        ST_Y(ST_Centroid(geometry)) AS y,
        '0' AS partition_id
    FROM test_points USING SAMPLE 500 ROWS
    
    UNION ALL
    
    SELECT
        iteration + 1,
        x,
        y,
        IF(
            IF(MOD(iteration, 2) = 0, x, y)  0
ORDER BY iteration, partition_id;
```

## Expected behavior
Query should execute successfully, returning KDTree partition assignments.

## Environment
- DuckDB v1.5.0 ("Variegata")
- macOS arm64 (also reproduced on Ubuntu x86_64 in CI)
- Python API (`duckdb` pip package)

## Notes
This worked in DuckDB v1.4.x. The pattern is used in [geoparquet-io](https://github.com/geoparquet/geoparquet-io) for KDTree spatial partitioning.

## Stack trace
```
0        duckdb_adbc_init + 3548796
1        duckdb_adbc_init + 3444796
2        PyInit__duckdb + 16858592
3        duckdb_adbc_init + 9895212
...
```

## Comments

**yharby:**
Closing — this was filed on the wrong repo. Tracking on duckdb/duckdb-spatial instead: https://github.com/duckdb/duckdb-spatial/issues/768
