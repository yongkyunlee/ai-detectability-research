# DuckDB 1.5.x regression: min(match_key_int) after UNION ALL over a temp view on read_parquet(...) is much slower than plain GROUP BY

**Issue #21302** | State: open | Created: 2026-03-11 | Updated: 2026-03-16
**Author:** RobinL
**Labels:** reproduced

### What happens?

I have found a performance regression in DuckDB 1.5.x for a query shape used in blocking/record linkage as used in [Splink](http://github.com/moj-analytical-services/splink)

The shape is:

```sql
CREATE TABLE result AS
WITH blocked AS (
    SELECT 0 AS match_key_int, l_id, r_id FROM ...
    UNION ALL
    SELECT 1 AS match_key_int, l_id, r_id FROM ...
)
SELECT
    min(match_key_int) AS match_key,
    l_id,
    r_id
FROM blocked
GROUP BY l_id, r_id;
```

The same query becomes fast again if `min(match_key_int)` is removed:

```sql
CREATE TABLE result AS
WITH blocked AS (
    SELECT 0 AS match_key_int, l_id, r_id FROM ...
    UNION ALL
    SELECT 1 AS match_key_int, l_id, r_id FROM ...
)
SELECT
    l_id,
    r_id
FROM blocked
GROUP BY l_id, r_id;
```

The repro needs:

- a small in-memory left table
- a large Parquet-backed right table
- a right side that is  wider than the join columns actually used
- a temp view over the Parquet scan

In the repro:

- using `read_parquet(...)` directly in the join branches instead of a temp view also does not reproduce it
- when the Parquet-backed right side is made wider, the slowdown gets much worse

### To Reproduce

Full reprex runnable in python

```python
#!/usr/bin/env -S uv run
# /// script
# dependencies = ["duckdb"]
# ///

from __future__ import annotations

import os
import tempfile
import time
from pathlib import Path

import duckdb

N_RIGHT = int(os.environ.get("N_RIGHT", "2000000"))
MATCHING_LEFT_ROWS = int(os.environ.get("MATCHING_LEFT_ROWS", "50"))
EXTRA_COLS = int(os.environ.get("EXTRA_COLS", "5"))
THREADS = int(os.environ.get("THREADS", "4"))

def parquet_path() -> Path:
    suffix = os.environ.get("PARQUET_TAG", "")
    suffix_part = f"_{suffix}" if suffix else ""
    name = f"duckdb_even_simpler_{N_RIGHT}_{EXTRA_COLS}{suffix_part}.parquet"
    return Path(tempfile.gettempdir()) / name

def filler_columns_sql() -> str:
    return ",\n                ".join(
        [f"((i * {idx + 3}) + {idx}) % 1000003 AS filler_{idx}" for idx in range(EXTRA_COLS)]
    )

def create_parquet_if_needed(con: duckdb.DuckDBPyConnection, path: Path) -> None:
    if path.exists():
        return

    con.execute(
        f"""
        COPY (
            SELECT
                i AS ukam_address_id,
                i % 3000000 AS numeric_token_1,
                printf('%05d %03d', i % 60000, (i * 7) % 1000) AS postcode,
                {filler_columns_sql()}
            FROM range({N_RIGHT}) t(i)
        ) TO '{path}' (FORMAT PARQUET, ROW_GROUP_SIZE 50000)
        """
    )

def create_left_table(con: duckdb.DuckDBPyConnection, path: Path) -> None:
    con.execute(
        f"""
        CREATE OR REPLACE TEMP TABLE left_probe AS
        SELECT
            row_number() OVER () AS ukam_address_id,
            numeric_token_1,
            postcode
        FROM read_parquet('{path}')
        USING SAMPLE {MATCHING_LEFT_ROWS} ROWS
        """
    )

def create_right_view(con: duckdb.DuckDBPyConnection, path: Path) -> None:
    con.execute(
        f"""
        CREATE OR REPLACE TEMP VIEW right_data AS
        SELECT * FROM read_parquet('{path}')
        """
    )

def final_query(with_min: bool) -> str:
    match_key_sql = "    min(match_key_int) AS match_key,\n" if with_min else ""

    return f"""
WITH blocked AS (
    SELECT
        0 AS match_key_int,
        l.ukam_address_id AS ukam_address_id_l,
        r.ukam_address_id AS ukam_address_id_r
    FROM left_probe l
    INNER JOIN right_data r
      ON (
        l.numeric_token_1 = r.numeric_token_1
        AND l.postcode = r.postcode
      )

    UNION ALL

    SELECT
        1 AS match_key_int,
        l.ukam_address_id AS ukam_address_id_l,
        r.ukam_address_id AS ukam_address_id_r
    FROM left_probe l
    INNER JOIN right_data r
      ON (
        l.numeric_token_1 = r.numeric_token_1
        AND l.postcode = r.postcode
      )
)
SELECT
{match_key_sql}    ukam_address_id_l,
    ukam_address_id_r
FROM blocked
GROUP BY ukam_address_id_l, ukam_address_id_r
"""

def materialize(con: duckdb.DuckDBPyConnection, sql: str, table_name: str) -> tuple[float, int]:
    con.execute(f"DROP TABLE IF EXISTS {table_name}")
    start = time.perf_counter()
    con.execute(f"CREATE TABLE {table_name} AS {sql}")
    elapsed = time.perf_counter() - start
    rows = con.execute(f"SELECT count(*) FROM {table_name}").fetchone()[0]
    return elapsed, rows

def main() -> None:
    con = duckdb.connect()
    con.execute(f"PRAGMA threads={THREADS}")
    con.execute("PRAGMA enable_object_cache=false")

    path = parquet_path()
    create_parquet_if_needed(con, path)
    create_left_table(con, path)
    create_right_view(con, path)

    print(f"DuckDB version: {duckdb.__version__}")
    print(f"Parquet path: {path}")
    print(f"Rows in right parquet: {N_RIGHT:,}")
    print(f"Left probe rows: {MATCHING_LEFT_ROWS:,}")
    print(f"Extra filler columns: {EXTRA_COLS}")

    slow_sql = final_query(with_min=True)
    fast_sql = final_query(with_min=False)

    slow_time, slow_rows = materialize(con, slow_sql, "attempt_even_simpler_slow")
    fast_time, fast_rows = materialize(con, fast_sql, "attempt_even_simpler_fast")

    print(f"with min(match_key_int): {slow_time:.2f}s, rows={slow_rows:,}")
    print(f"without min(match_key_int): {fast_time:.2f}s, rows={fast_rows:,}")
    print(f"Slow/Fast ratio: {slow_time / fast_time:.2f}x")

    if slow_rows != fast_rows:
        print("WARNING: row counts differ between variants")

    if slow_time > fast_time * 1.75:
        print("REPRODUCED: grouped min(match_key_int) is much slower than plain grouping.")
    else:
        print("No large min-vs-group regression reproduced for this DuckDB version/configuration.")

if __name__ == "__main__":
    main()
```

```text
uv run --with duckdb==1.3.2 attempt_at_even_simpler_preproducer.py
uv run --with duckdb==1.4.4 attempt_at_even_simpler_preproducer.py
uv run --with duckdb==1.5.0 attempt_at_even_simpler_preproducer.py
uv run --with duckdb==1.5.0.dev336 attempt_at_even_simpler_preproducer.py
```

### Observed results

Verified on macOS with the current script above:

- DuckDB 1.3.2: `with min(match_key_int)` 0.02s, `without min(match_key_int)` 0.02s, ratio 1.16x
- DuckDB 1.4.4: `with min(match_key_int)` 0.02s, `without min(match_key_int)` 0.02s, ratio 1.04x
- DuckDB 1.5.0: `with min(match_key_int)` 0.04s, `without min(match_key_int)` 0.02s, ratio 1.97x
- DuckDB 1.5.0.dev336: `with min(match_key_int)` 0.04s, `without min(match_key_int)` 0.02s, ratio 1.97x

So this reduced repro does not reproduce on 1.3.2 or 1.4.4, but it does reproduce on 1.5.0 and 1.5.0.dev336.

### Additional observations

Two details seem to matter in this reduced repro:

1. If the right table is not wide at all, for example `EXTRA_COLS=0`, the slowdown disappears.
2. If `read_parquet(...)` is used directly in each join branch instead of going through the temp view

```sql
CREATE OR REPLACE TEMP VIEW right_data AS
SELECT * FROM read_parquet('...')
```

then the slowdown also disappears in this reduced example.

The width of the Parquet-backed right table also has a large effect on the size of the slowdown. In slightly larger variants of the same repro family on DuckDB 1.5.0:

- `EXTRA_COLS=5`: `0.23s` vs `0.10s`, ratio `2.23x`
- `EXTRA_COLS=20`: `0.55s` vs `0.11s`, ratio `5.21x`
- `EXTRA_COLS=80`: `3.23s` vs `0.14s`, ratio `22.37x`

### Possible cause

**⚠️Note: Possible slop⚠️:  The following is from asking an LLM to investigate the duckdb codebase for changes.**

> 
> This looks less like a Parquet-reader regression and more like a planner/binder regression around column pruning across a temp-view boundary.
> 
> The strongest evidence found is:
> 
> - in 1.3.2, both the temp-view version and the direct `read_parquet(...)` version preserve narrow Parquet projections in this repro
> - in 1.5.0, the direct `read_parquet(...)` version is still fast, but the temp-view + `min(match_key_int)` version slows down substantially
> - disabling `unused_columns` makes the fast form slow as well, which suggests the regression is specifically that the grouped-min temp-view shape loses column pruning
> 
> So the current best guess is: in 1.5.x, the temp view over `read_parquet(...)` has become a stronger optimization boundary for this shape, and required-column information no longer propagates as well through that boundary for the grouped `min(match_key_int)` variant.
> 
> The most plausible related changes I found are:
> 
> - Common Subplan Elimination: https://github.com/duckdb/duckdb/pull/19080
> - Make Binding CTEs lazy, and other CTE binding refactors: https://github.com/duckdb/duckdb/pull/19372
> - Allow lazy binding of views: https://github.com/duckdb/duckdb/pull/20696

### OS:

MacOS

### DuckDB Version:

1.3.2 vs 1.4.4 vs 1.5.0 vs 1.5.0.dev336

### DuckDB Client:

Python

### Hardware:

Mac M4 Max (36GB mem)

### Full Name:

Robin Linacre

### Affiliation:

UK Ministry of Justice

### Did you include all relevant configuration (e.g., CPU architecture, Linux distribution) to reproduce the issue?

- [x] Yes, I have

### Did you include all code required to reproduce the issue?

- [x] Yes, I have

### Did you include all relevant data sets for reproducing the issue?

Yes

## Comments

**Mytherin:**
Thanks for the report! This is down to missing projection pushdown in CTEs in the presence of `UNION ALL` - https://github.com/duckdb/duckdb/pull/21275 fixes the issue. As a work-around you can explicitly label the CTE as `AS MATERIALIZED`.
