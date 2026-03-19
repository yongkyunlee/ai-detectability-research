# CTE materialisation prevents column pruning for simple pass-through CTEs (100x slowdown, regression between 1.3.2 and 1.4.0)

**Issue #20958** | State: closed | Created: 2026-02-14 | Updated: 2026-03-11
**Author:** RobinL
**Labels:** reproduced

### What happens?

Between DuckDB 1.3.2 and 1.4.0 we have observed a [huge slowdown in some queries in Splink](https://github.com/moj-analytical-services/splink/issues/2918)

I think I have a simple reprex that demonstrates the problem as follows:

```sql
CREATE TABLE result AS
WITH base AS (
    SELECT * FROM wide_table
)
SELECT id, value FROM base
UNION ALL
SELECT id, value FROM base
```

I believe the root cause is the changes made in https://github.com/duckdb/duckdb/pull/17459 (Make CTE Materialization the Default Instead of Inlining)

### To Reproduce

Full reprex runnable in python

```python
"""
Minimal reprex: DuckDB 1.4.x materializes simple pass-through CTEs,
blocking column pruning and causing performance regressions.

Usage:
    uv run --with duckdb==1.3.2 simplest_reprex.py
    uv run --with duckdb==1.4.4 simplest_reprex.py
"""

import duckdb
import json
import time

print(f"DuckDB version: {duckdb.__version__}")
con = duckdb.connect()

# Create a wide table with 50 columns, but the query only needs 2.
N = 50_000_000
extra_cols = ", ".join(f"i AS c{i}" for i in range(1, 49))
con.execute(f"""
    CREATE TABLE wide_table AS
    SELECT
        i AS id,
        i % 1000 AS value,
        {extra_cols}
    FROM range({N}) t(i)
""")
print(f"Table created: {N:,} rows, 50 columns")

# The simplest possible case: a SELECT * CTE referenced twice.
# - In 1.3.2: CTE is inlined, column pruning works, only 2 cols scanned
# - In 1.4.x: CTE is materialized with ALL 50 columns, blocking pruning
query = """
CREATE TABLE result AS
WITH base AS (
    SELECT * FROM wide_table
)
SELECT id, value FROM base
UNION ALL
SELECT id, value FROM base
"""

# Time the query
start = time.perf_counter()
con.execute(query)
elapsed = time.perf_counter() - start
print(f"Query time: {elapsed:.2f}s")

count = con.execute("SELECT count(*) FROM result").fetchone()[0]
print(f"Result rows: {count:,}")

# Get the plan for analysis
con.execute("DROP TABLE result")
plan_json = con.execute(f"EXPLAIN (FORMAT JSON) {query}").fetchall()[0][1]
plan = json.loads(plan_json)

# Walk the plan tree
def walk(node, depth=0):
    results = []
    if isinstance(node, list):
        for item in node:
            results.extend(walk(item, depth))
        return results
    name = (node.get("operator_name") or node.get("name") or "").strip()
    extra = node.get("extra_info") or {}
    op_type = node.get("operator_type", "")

    if op_type == "CTE" or (
        name.upper().startswith("CTE") and "SCAN" not in name.upper()
    ):
        cte_name = extra.get("CTE Name", name)
        results.append(("CTE_BARRIER", cte_name, None, depth))

    projs = extra.get("Projections")
    if isinstance(projs, list) and "SCAN" in name.upper():
        results.append(("SCAN", name, projs, depth))

    for child in node.get("children") or []:
        results.extend(walk(child, depth + 1))
    return results

print(f"\n{'=' * 60}")
print("Plan analysis (scans and CTE barriers):")
print(f"{'=' * 60}")

nodes = walk(plan)
has_cte_barrier = False
has_wide_scan = False

for kind, name, projs, depth in nodes:
    indent = "  " * depth
    if kind == "CTE_BARRIER":
        has_cte_barrier = True
        print(f"{indent}CTE [{name}] -- materialization barrier")
    elif kind == "SCAN" and projs is not None:
        n = len(projs)
        if n > 5:
            has_wide_scan = True
            print(f"{indent}{name}: {n} columns projected  
 

```
uv run --with duckdb==1.3.2 simplest_reprex.py
uv run --with duckdb==1.4.4 simplest_reprex.py
```

This query takes 100x longer on `duckdb=1.4.4` (31 seconds vs 0.3 seconds on my macbook).

More detailed output

```
➜  ddb_blocking_reprex git:(main) ✗ uv run --with duckdb==1.4.4 simplest_reprex.py
DuckDB version: 1.4.4
Table created: 50,000,000 rows, 50 columns
Query time: 31.64s
Result rows: 100,000,000

============================================================
Plan analysis (scans and CTE barriers):
============================================================
  CTE [base] -- materialization barrier
    SEQ_SCAN: 50 columns projected  
 

### OS:

MacOS

### DuckDB Version:

1.3.2 vs 1.4.4

### DuckDB Client:

Python

### Hardware:

_No response_

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

**szarnyasg:**
@RobinL thanks for reporting this and special thanks for the nice reproducer 🙏
