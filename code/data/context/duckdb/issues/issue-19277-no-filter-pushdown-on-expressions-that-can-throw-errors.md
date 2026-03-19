# No filter pushdown on expressions that can throw errors

**Issue #19277** | State: closed | Created: 2025-10-06 | Updated: 2026-03-11
**Author:** soerenwolfers
**Labels:** reproduced

### What happens?

I have very wide parquet data.

Queries that filter aggressively on a single column are very slow, scaling with O(nColumns x nRows) when they should run in O(nColumns + nRows) because the filter only requires a single column and the result can then be found reading all columns for only a handful of rows.

In comparison, polars computes my query 17x faster than duckdb.

Alternatively, I can use a ridiculous workaround that's about as fast as polars: Store 800_000 different files with the filter column in the name; filter the filenames; read only the filtered files. Admittedly, this does have the unfair advantage of using row major storage though.

A related observation that I also think could be faster in duckdb: Even if I figure out the filtered row numbers in different ways and then try to specifically just read the corresponding rows, reading just a single row of 780 columns still takes 3 seconds.

PS: I'm using single threaded code in all my snippets below, because in times of kubernetes you have to pay for every single core you use. In any case, the speed up of polars and duckdb is the same when I use multiple threads.

### To Reproduce

```python
import duckdb
import polars as pl
import numpy as np
import math
rng = np.random.RandomState(1)
values = rng.rand(800000, 780)
pl.DataFrame(values).write_parquet('/tmp/polars.parquet')
```

then 

```sql
SET THREADS = 1;
EXPLAIN ANALYZE
SELECT * FROM '/tmp/polars.parquet' WHERE sqrt(column_0) < 0.001
```

takes 8.5s and prints

```text
┌─────────────────────────────────────┐
│┌───────────────────────────────────┐│
││    Query Profiling Information    ││
│└───────────────────────────────────┘│
└─────────────────────────────────────┘
 EXPLAIN ANALYZE SELECT * FROM '/tmp/polars.parquet' WHERE sqrt(column_0) < 0.001 
┌────────────────────────────────────────────────┐
│┌──────────────────────────────────────────────┐│
││               Total Time: 8.55s              ││
│└──────────────────────────────────────────────┘│
└────────────────────────────────────────────────┘
┌───────────────────────────┐
│           QUERY           │
└─────────────┬─────────────┘
┌─────────────┴─────────────┐
│      EXPLAIN_ANALYZE      │
│    ────────────────────   │
│           0 rows          │
│          (0.00s)          │
└─────────────┬─────────────┘
┌─────────────┴─────────────┐
│           FILTER          │
│    ────────────────────   │
│  (sqrt(column_0) < 0.001) │
│                           │
│           1 row           │
│          (0.11s)          │
└─────────────┬─────────────┘
┌─────────────┴─────────────┐
│         TABLE_SCAN        │
│    ────────────────────   │
│         Function:         │
│        PARQUET_SCAN       │
│                           │
│        Projections:       │
│          column_0         │
│          column_1         │
│            ...            │
│         column_779        │
│                           │
│    Total Files Read: 1    │
│                           │
│        800,000 rows       │
│          (8.35s)          │
└───────────────────────────┘
```

which indicates that all rows of all columns are read. Note that executing the same filter on a parquet with only one column only takes 50ms. Since columns in parquet are stored independently, I believe the query here should not take much longer than that. In fact, polars 

```python
import os
os.environ["POLARS_MAX_THREADS"] = "1"
import polars as pl
print(pl.thread_pool_size())
pl.scan_parquet('/tmp/polars.parquet').filter(pl.col('column_0').sqrt() < 0.001).collect()
```

takes only 500ms.

I can improve duckdb's performance slightly via

```sql
SET THREADS = 1;
EXPLAIN ANALYZE
SELECT * FROM '/tmp/polars.parquet' WHERE file_row_number IN (SELECT file_row_number FROM '/tmp/polars.parquet' WHERE sqrt(column_0) < 0.001)
```

which takes 3s (which I'm independently surprised by: there is only one row number that matches the filter here), but it feels awkward to have to do pushdowns by hand, since whether this is actually faster will depend on implementation details.

When I turn the parquet into a duckdb table first, the original query finishes in only 0.4s but the query plan is the same.

Just to provide more evidence that something must be broken or at least deserves serious attention, I can alternatively write 800_000 files(!) and use globbing and filename filtering: 

```python
# write "database"
os.makedirs('/tmp/ddb', exist_ok=True)

for i in range(values.shape[0]):
    with open(f"/tmp/ddb/myfile_{values[i, 0]}", 'wb') as f:
        f.write(values[i, :].tobytes())

# query "database"
all_files = os.listdir('/tmp/ddb')
filtered_files = [x for x in all_files if math.sqrt(float(x.split('_')[1])) < 0.001]

for file in filtered_files:
    with open(f'/tmp/ddb/{file}', 'rb') as f:
        print(np.frombuffer(f.read()))
```

The "query database" step here takes only 0.5s!

### OS:

Linux

### DuckDB Version:

'1.5.0.dev44'; polars1.32.3; numpy1.26.4

### DuckDB Client:

Python

### Hardware:

amd64, 16GB

### Full Name:

Soeren Wolfers

### Affiliation:

G-Research

### What is the latest build you tested with? If possible, we recommend testing with the latest nightly build.

I have tested with a nightly build

### Did you include all relevant data sets for reproducing the issue?

Not applicable - the reproduction does not require a data set

### Did you include all code required to reproduce the issue?

- [x] Yes, I have

### Did you include all relevant configuration (e.g., CPU architecture, Python version, Linux distribution) to reproduce the issue?

- [x] Yes, I have

## Comments

**Mytherin:**
Thanks for the report!

This is because DuckDB cannot currently push functions that can return errors into scans, and `sqrt` can return an error, e.g.:

```sql
select sqrt(-1);
-- Out of Range Error:
-- cannot take square root of a negative number
```

This is an expected limitation currently. Using functions that do not return errors in filters should be pushed down correctly.

**soerenwolfers:**
Ah, should have noticed that. That might be another reason to have duckdb return NaN instead of throwing errors on standard IEEE-functions then? (which would make sense anyway now that duckdb stopped throwing on basic arithmetic) https://github.com/duckdb/duckdb/discussions/10956

**MPizzotti:**
Continuing on the thread, is this the same reason why i cannot get a filter pushdown on a join?
here's a dummy query:
```
WITH store as (
select * from store_lookup as store_md where store_code='xxx'
),
brands as (
select * from brand_lookup where commodity_brand='xxx'
)
select sum(fct__net_sales__commercial__local)
from read_parquet("hive_path"
            hive_partitioning = true,
            hive_types = {'year': INT, 'month': INT},
            hive_types_autocast = false
    )
JOIN store on (dim__store_code=store_code)
JOIN brands using (hash_brand)
where
1=1
AND year=2025
AND month=12 
AND dim__record_date between  DATE '2025-12-08' and  DATE '2025-12-14' --ONE WEEK
```

looking at the profiled query using explain analyze i get this filter pushdown:
```
┌─────────────────────────────────────┐
│┌───────────────────────────────────┐│
││    Query Profiling Information    ││
│└───────────────────────────────────┘│
└─────────────────────────────────────┘

┌────────────────────────────────────────────────┐
│┌──────────────────────────────────────────────┐│
││               Total Time: 1.39s              ││
│└──────────────────────────────────────────────┘│
└────────────────────────────────────────────────┘
┌───────────────────────────┐
│           QUERY           │
└─────────────┬─────────────┘
┌─────────────┴─────────────┐
│      EXPLAIN_ANALYZE      │
│    ────────────────────   │
│           0 rows          │
│          (0.00s)          │
└─────────────┬─────────────┘
┌─────────────┴─────────────┐
│    UNGROUPED_AGGREGATE    │
│    ────────────────────   │
│    Aggregates: sum(#0)    │
│                           │
│           1 row           │
│          (0.00s)          │
└─────────────┬─────────────┘
┌─────────────┴─────────────┐
│         PROJECTION        │
│    ────────────────────   │
│fct__net_sales__commercial_│
│           _local          │
│                           │
│           0 rows          │
│          (0.00s)          │
└─────────────┬─────────────┘
┌─────────────┴─────────────┐
│         HASH_JOIN         │
│    ────────────────────   │
│      Join Type: INNER     │
│                           │
│        Conditions:        │
│     dim__store_code =     ├───────────────────────────────────────────┐
│         store_code        │                                           │
│                           │                                           │
│           0 rows          │                                           │
│          (0.00s)          │                                           │
└─────────────┬─────────────┘                                           │
┌─────────────┴─────────────┐                             ┌─────────────┴─────────────┐
│         HASH_JOIN         │                             │         TABLE_SCAN        │
│    ────────────────────   │                             │    ────────────────────   │
│      Join Type: INNER     │                             │         Function:         │
│                           │                             │        READ_PARQUET       │
│        Conditions:        │                             │                           │
│  hash_brand = hash_brand  │                             │        Projections:       │
│                           │                             │         store_code        │
│                           ├──────────────┐              │                           │
│                           │              │              │          Filters:         │
│                           │              │              │    store_code='xxxxxx'    │
│                           │              │              │                           │
│                           │              │              │    Total Files Read: 1    │
│                           │              │              │                           │
│           0 rows          │              │              │           1 row           │
│          (0.00s)          │              │              │          (0.00s)          │
└─────────────┬─────────────┘              │              └───────────────────────────┘
┌─────────────┴─────────────┐┌─────────────┴─────────────┐
│         TABLE_SCAN        ││         TABLE_SCAN        │
│    ────────────────────   ││    ────────────────────   │
│         Function:         ││         Function:         │
│        READ_PARQUET       ││        READ_PARQUET       │
│                           ││                           │
│        Projections:       ││        Projections:       │
│      dim__store_code      ││         hash_brand        │
│         hash_brand        ││                           │
│fct__net_sales__commercial_││          Filters:         │
│           _local          ││  commodity_brand='xxxxx'  │
│                           ││                           │
│          Filters:         ││    Total Files Read: 1    │
│  dim__store_code='xxxxxx' ││                           │
│ dim__record_date>='2025-12││                           │
│       -08'::DATE AND      ││                           │
│   dim__record_date<='2025 ││                           │
│       -12-14'::DATE       ││                           │
│                           ││                           │
│       File Filters:       ││                           │
│ (year = 2025)(month = 12) ││                           │
│                           ││                           │
│    Scanning Files: 1/26   ││                           │
│    Total Files Read: 1    ││                           │
│                           ││                           │
│          367 rows         ││          17 rows          │
│          (0.14s)          ││          (0.00s)          │
└───────────────────────────┘└───────────────────────────┘
```

looking at the profiled query, the store_code is correctly pushed down, since i'm pretty much filtering for the same column,
but it's not filtering by hash_brand, even if i try to declare the subquery as `brands as materialized(`.

is there a way to push down also a intermediate result?

in this example it's not really necessary, but this problem is quite tedius when working on date ranges coming from a lookup table.

**DinosL:**
This issue is resolved by https://github.com/duckdb/duckdb/pull/20744
