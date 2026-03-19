# Hive Partitioning -> different behaviour based on nesting levels

**Issue #21370** | State: closed | Created: 2026-03-13 | Updated: 2026-03-17
**Author:** MPizzotti
**Labels:** under review

### What happens?

I have a table that has 2 main dimensions: store_idx and record_date.
currently i'm saving the result as a hive-partition like so:
```
COPY (
    SELECT
        store_idx,
        record_date,
        -- ...facts
        year: year(record_date),
        month: month(record_date)
) TO '/hive_partition' (
    FORMAT 'parquet',
    PARQUET_VERSION 'V2',
    COMPRESSION 'ZSTD',
    PARTITION_BY (year, month),
    WRITE_PARTITION_COLUMNS FALSE,
    OVERWRITE_OR_IGNORE
);
```
and i get a neat, clean partition:
```
year=2025
|__month=1
|   |__data_0.parquet
|__month=2
    |__data_0.parquet
```

But given the huge parquet files generated,  i also tried to partition by a bucket of store indexes:
```
COPY (
    SELECT
        store_idx,
        record_date,
        -- ...facts
        store_bucket: (store_idx/600)::INTEGER,
        year: year(record_date),
        month: month(record_date)
) TO '/hive_partition' (
    FORMAT 'parquet',
    PARQUET_VERSION 'V2',
    COMPRESSION 'ZSTD',
    PARTITION_BY (year, month, store_bucket),
    WRITE_PARTITION_COLUMNS FALSE,
    OVERWRITE_OR_IGNORE
);
```
now, instead of getting a clean result back, i get a random number of files back, some even empty:

also, for first "cold" queries on this hive, related to #21347, it's taking a good amount of time since is scanning 6418 files, instead of scanning 28 files,

another point regarding performance: even if by [documentation](https://duckdb.org/docs/current/core_extensions/azure#difference-between-adls-and-blob-storage) is specified that `abfss://` should be faster, i found out that the default `az://` is faster even when using Azure Data Lake Storage (ADLS)

### To Reproduce

dummy dataset generator:  18,000 store_idx × 1,095 days (2022–2024) = ~19.7M rows
```
SELECT
    s.store_idx,
    DATE '2022-01-01' + (random() * 1094)::INT AS record_date,
    round(random() * 10000, 2)                  AS fct__revenue,
    round(random() * 500,   2)                  AS fct__transactions,
    round(random() * 100,   2)                  AS fct__avg_basket,
    round(random() * 1000,  2)                  AS fct__units_sold
FROM range(1, 18001) s(store_idx)
CROSS JOIN range(1095) d(day_offset);
```

and then try to dump the result in a hive partition with 2 nesting level (year, month) and 3 levels (year,month, store_bucket)

### OS:

x86_64

### DuckDB Version:

1.4.4+

### DuckDB Client:

any

### Hardware:

_No response_

### Full Name:

Massimiliano

### Affiliation:

luxottica

### Did you include all relevant configuration (e.g., CPU architecture, Linux distribution) to reproduce the issue?

- [x] Yes, I have

### Did you include all code required to reproduce the issue?

- [x] Yes, I have

### Did you include all relevant data sets for reproducing the issue?

Yes

## Comments

**Mytherin:**
Thanks for the report! This is a known issue when partitioning by many keys, you can work-around the issue by ordering by the partition keys explicitly in the `SELECT` statement (`ORDER BY year, month, store_bucket`).

**taniabogatsch:**
Closing as known issue (duplicate).
