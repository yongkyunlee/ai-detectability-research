# union_by_name + hive_partitioning cannot filter on partition columns

**Issue #7491** | State: closed | Created: 2023-05-12 | Updated: 2026-03-18
**Author:** DanCardin

### What happens?

when using `hive_partitioning=1, union_by_name=1` together, queries seem to not apply filters to columns in the partition scheme.

From the code example below, the same query with/without `union_by_name=1` exhibits different behavior, which I wouldn't expect it to, from this sort of query.

For whatever it's worth, I am enabling `union_by_name` exclusively to allow the addition of columns to the parquet files over time, such that queries are still able to function when historically written files are missing said columns.

### To Reproduce

```python
import duckdb
import pyarrow
import pyarrow.dataset
import pyarrow.fs


def write_file(fs, data):
    partition_schema = pyarrow.schema([("a", pyarrow.string())])
    partitioning = pyarrow.dataset.partitioning(partition_schema, flavor="hive")

    table = pyarrow.Table.from_pydict(data)
    pyarrow.dataset.write_dataset(
        table,
        "foo",
        schema=table.schema,
        filesystem=fs,
        format="parquet",
        partitioning=partitioning,
        existing_data_behavior="overwrite_or_ignore",
    )


fs = pyarrow.fs.LocalFileSystem()
write_file(fs, {"a": [1, 1], "b": [2, 3]})
write_file(fs, {"a": [2, 2], "b": [3, 4]})

expected_result = [("1", 2), ("1", 3)]

query = "SELECT a, b FROM read_parquet('foo/**/*.parquet', hive_partitioning=1) WHERE a = '1'"
conn = duckdb.connect()
result = conn.execute(query).fetchall()
assert expected_result == result, result


query = "SELECT a, b FROM read_parquet('foo/**/*.parquet', hive_partitioning=1, union_by_name=1) WHERE a = '1'"
conn = duckdb.connect()
result = conn.execute(query).fetchall()
assert expected_result == result, result
```

### OS:

aarch64

### DuckDB Version:

0.7.1

### DuckDB Client:

python

### Full Name:

Dan Cardin

### Affiliation:

Known

### Have you tried this on the latest `master` branch?

- [x] I agree

### Have you tried the steps to reproduce? Do they include all relevant data and configuration? Does the issue you report still appear there?

- [X] I agree

## Comments

**DanCardin:**
This must have been fixed(?) somewhere since i installed the pre release and developed my minimal example. I just tried this on the most recent pre builds and it's at least now passing the assert. I had looked at issue reports and merged prs and didn't see anything that matched.

I suppose maybe this could be useful if turned into a testcase, if this hadn't originally been reported as a bug and was fixed incidentally?

Otherwise feel free to close, I suppose.

**Mytherin:**
Thanks for checking again - this was likely fixed as part of https://github.com/duckdb/duckdb/pull/6912

**psanker:**
I believe this issue still persists in some cases. I've found a situation where if you have an inequality filter on the partition key (e.g. `data_month` >= 202501), predicate pushdown does _not_  occur. Instead, there is an assumption that the filter column is in the data, which fails.

**szarnyasg:**
Hi @psanker can you please share the code that triggers the error?

**psanker:**
I have created a minimal viable repro:

```sql
-- Create partitioned data
create temp table sch_a as 
    select
	a.i as p_key,
        uuid() as id
    from generate_series(1, 4) a(i)
    cross join generate_series(1, 200) b(j);

-- Simulate schema evolution
create temp table sch_b as 
    select
	a.i as p_key,
        uuid() as id,
        floor(5 * random() + 1)::integer as scale
    from generate_series(5, 9) a(i)
    cross join generate_series(1, 200) b(j);

copy sch_a to 'testdat' (FORMAT CSV, PARTITION_BY (p_key), OVERWRITE_OR_IGNORE);
copy sch_b to 'testdat' (FORMAT CSV, PARTITION_BY (p_key), OVERWRITE_OR_IGNORE);

-- Create view on partitioned data with union_by_name
-- Specifying column names negates this behavior.

create or replace view v_testdat as
    select * from read_csv('testdat/*/*.csv', hive_partitioning=TRUE, union_by_name=TRUE);

-- Error here!
select * from v_testdat where p_key > 5;
```

The schema evolution aspect seems key. If you don't have that new column created, the error does not appear. Using 1.1.2 btw.

**Mytherin:**
This seems to have been resolved in the latest version of DuckDB
