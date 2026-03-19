---
source_url: https://duckdb.org/2021/05/14/sql-on-pandas.html
author: "Mark Raasveldt, Hannes Muhleisen"
platform: duckdb.org (official blog)
scope_notes: "Trimmed from a 17-min read on running SQL on Pandas DataFrames. Focused on core integration, automatic variable binding, and key benchmark results. Original ~4000 words; trimmed to ~500 words."
---

DuckDB, a free and open source analytical data management system, can efficiently run SQL queries directly on Pandas DataFrames.

One of the core goals of DuckDB is that accessing data in common formats should be easy. DuckDB is fully capable of running queries in parallel directly on top of a Pandas DataFrame (or on a Parquet/CSV file, or on an Arrow table). A separate, time-consuming import step is not necessary.

When you run a query in SQL, DuckDB will look for Python variables whose name matches the table names in your query and automatically start reading your Pandas DataFrames:

```python
import pandas as pd
import duckdb

mydf = pd.DataFrame({'a' : [1, 2, 3]})
print(duckdb.query("SELECT sum(a) FROM mydf").to_df())
```

The SQL table name `mydf` is interpreted as the local Python variable that happens to be a Pandas DataFrame, which DuckDB can read and query directly. The column names and types are also extracted automatically from the DataFrame.

Not only is this process painless, it is highly efficient. For many queries, you can use DuckDB to process data faster than Pandas, and with a much lower total memory usage, without ever leaving the Pandas DataFrame binary format ("Pandas-in, Pandas-out").

## Performance Benchmarks

Using TPC-H scale factor 1 data (~1 GB uncompressed CSV), the benchmarks operated purely on Pandas DataFrames in a "Pandas-in, Pandas-out" basis.

### Grouped Aggregate with Filter

```sql
SELECT
    l_returnflag, l_linestatus,
    sum(l_extendedprice), min(l_extendedprice),
    max(l_extendedprice), avg(l_extendedprice)
FROM lineitem
WHERE l_shipdate <= DATE '1998-09-02'
GROUP BY l_returnflag, l_linestatus;
```

| Name                     | Time (s) |
|--------------------------|----------|
| DuckDB (1 Thread)        | 0.60     |
| DuckDB (2 Threads)       | 0.42     |
| Pandas                   | 3.57     |
| Pandas (manual pushdown) | 2.23     |

DuckDB's query optimizer automatically applies projection pushdown. In Pandas, the filter creates a copy of the entire DataFrame (minus filtered rows), which is time consuming when the filter is not very selective.

### Joins

```sql
SELECT
    l_returnflag, l_linestatus,
    sum(l_extendedprice), avg(l_extendedprice)
FROM lineitem
JOIN orders ON (l_orderkey = o_orderkey)
WHERE l_shipdate <= DATE '1998-09-02'
  AND o_orderstatus = 'O'
GROUP BY l_returnflag, l_linestatus;
```

| Name                     | Time (s) |
|--------------------------|----------|
| DuckDB (1 Thread)        | 1.05     |
| DuckDB (2 Threads)       | 0.53     |
| Pandas                   | 15.2     |
| Pandas (manual pushdown) | 3.78     |

The basic Pandas approach is extremely time consuming compared to the optimized version. This demonstrates the usefulness of the automatic query optimizer. Even after optimizing, the Pandas code is still significantly slower because it stores intermediate results in memory after individual filters and joins.

## Data Transfer Overhead

Unlike external database systems like Postgres, DuckDB's data transfer time is negligible. Copying a Pandas DataFrame of 10M integers:

| Name                                   | Time (s) |
|----------------------------------------|----------|
| Pandas to Postgres using to_sql        | 111.25   |
| Pandas to SQLite using to_sql          | 6.80     |
| Pandas to DuckDB                       | 0.03     |

DuckDB directly reads the underlying array from Pandas, making this operation almost instant. DuckDB uses the Postgres SQL parser and offers many of the same SQL features, including window functions, correlated subqueries, recursive common table expressions, nested types, and sampling.
