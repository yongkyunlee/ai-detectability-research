# Hive Partitioning Filter Pushdown not working on INNER JOIN or CTE against local table

**Issue #17352** | State: closed | Created: 2025-05-04 | Updated: 2026-03-12
**Author:** its-felix
**Labels:** under review

### What happens?

With the following Parquet Hive Partitioned Data in S3:
```sql
COPY (
  SELECT
    *,
    (number % 10) AS number_mod_10
  FROM flight_variant_history
  ORDER BY airline_id, number_mod_10
)
TO 's3://XXXXXX/history_v2' (
  FORMAT parquet,
  COMPRESSION gzip,
  PARTITION_BY (airline_id, number_mod_10)
)
```

And the following **LOCAL** tables:
```sql
CREATE TABLE airlines (
    id UUID NOT NULL,
    name TEXT,
    PRIMARY KEY (id)
) ;

CREATE TABLE airline_identifiers (
    issuer TEXT NOT NULL,
    identifier TEXT NOT NULL,
    airline_id UUID NOT NULL,
    PRIMARY KEY (issuer, identifier),
    FOREIGN KEY (airline_id) REFERENCES airlines (id)
) ;
```

I would assume a full filter pushdown to work in this query:
```sql
WITH aid AS (
-- select returning 0-1 rows guaranteed by primary key on this table
  SELECT *
  FROM airline_identifiers
  WHERE issuer = 'iata'
  AND identifier = 'LH'
)
SELECT *
FROM read_parquet(
  's3://XXXXXX/history_v2/**/*.parquet',
  hive_partitioning = true,
  hive_types = {'airline_id': UUID, 'number_mod_10': USMALLINT}
) fvh
INNER JOIN aid
ON fvh.airline_id = aid.airline_id -- join on hive partition
WHERE fvh.number = 454
AND fvh.number_mod_10 = (454 % 10)
AND fvh.suffix = ''
ORDER BY fvh.departure_date_local ASC, fvh.created_at DESC
```

Instead, a filter pushdown only works on the given literal filter `fvh.number_mod_10 = (454 % 10)`:
```
┌─────────────────────────────────────┐
│┌───────────────────────────────────┐│
││         HTTPFS HTTP Stats         ││
││                                   ││
││            in: 3.9 MiB            ││
││            out: 0 bytes           ││
││              #HEAD: 3             ││
││              #GET: 47             ││
││              #PUT: 0              ││
││              #POST: 0             ││
││             #DELETE: 0            ││
│└───────────────────────────────────┘│
└─────────────────────────────────────┘
┌────────────────────────────────────────────────┐
│┌──────────────────────────────────────────────┐│
││               Total Time: 2.14s              ││
│└──────────────────────────────────────────────┘│
└────────────────────────────────────────────────┘
┌───────────────────────────┐
│           QUERY           │
└─────────────┬─────────────┘
┌─────────────┴─────────────┐
│      EXPLAIN_ANALYZE      │
│    ────────────────────   │
│           0 Rows          │
│          (0.00s)          │
└─────────────┬─────────────┘
┌─────────────┴─────────────┐
│         PROJECTION        │
│    ────────────────────   │
│             #0            │
│             #1            │
│             #2            │
│             #3            │
│             #4            │
│             #5            │
│             #6            │
│             #7            │
│             #8            │
│             #9            │
│__internal_decompress_strin│
│           g(#10)          │
│__internal_decompress_strin│
│           g(#11)          │
│            #12            │
│                           │
│          766 Rows         │
│          (0.00s)          │
└─────────────┬─────────────┘
┌─────────────┴─────────────┐
│          ORDER_BY         │
│    ────────────────────   │
│  fvh.departure_date_local │
│             ASC           │
│    fvh.created_at DESC    │
│                           │
│          766 Rows         │
│          (0.00s)          │
└─────────────┬─────────────┘
┌─────────────┴─────────────┐
│         PROJECTION        │
│    ────────────────────   │
│             #0            │
│             #1            │
│             #2            │
│             #3            │
│             #4            │
│             #5            │
│             #6            │
│             #7            │
│             #8            │
│             #9            │
│__internal_compress_string_│
│        ubigint(#10)       │
│__internal_compress_string_│
│       uinteger(#11)       │
│            #12            │
│                           │
│          766 Rows         │
│          (0.00s)          │
└─────────────┬─────────────┘
┌─────────────┴─────────────┐
│         PROJECTION        │
│    ────────────────────   │
│           number          │
│           suffix          │
│    departure_airport_id   │
│    departure_date_local   │
│         created_at        │
│        replaced_at        │
│        query_dates        │
│     flight_variant_id     │
│         airline_id        │
│       number_mod_10       │
│           issuer          │
│         identifier        │
│         airline_id        │
│                           │
│          766 Rows         │
│          (0.00s)          │
└─────────────┬─────────────┘
┌─────────────┴─────────────┐
│         HASH_JOIN         │
│    ────────────────────   │
│      Join Type: INNER     │
│                           │
│        Conditions:        ├──────────────┐
│  airline_id = airline_id  │              │
│                           │              │
│          766 Rows         │              │
│          (0.00s)          │              │
└─────────────┬─────────────┘              │
┌─────────────┴─────────────┐┌─────────────┴─────────────┐
│         TABLE_SCAN        ││         TABLE_SCAN        │
│    ────────────────────   ││    ────────────────────   │
│         Function:         ││           Table:          │
│        READ_PARQUET       ││    airline_identifiers    │
│                           ││                           │
│        Projections:       ││   Type: Sequential Scan   │
│         airline_id        ││                           │
│           number          ││        Projections:       │
│       number_mod_10       ││           issuer          │
│           suffix          ││         identifier        │
│    departure_airport_id   ││         airline_id        │
│    departure_date_local   ││                           │
│         created_at        ││          Filters:         │
│        replaced_at        ││       issuer='iata'       │
│        query_dates        ││      identifier='LH'      │
│     flight_variant_id     ││                           │
│                           ││                           │
│          Filters:         ││                           │
│         number=454        ││                           │
│         suffix=''         ││                           │
│                           ││                           │
│       File Filters:       ││                           │
│    (number_mod_10 = 4)    ││                           │
│                           ││                           │
│      Scanning Files:      ││                           │
│           47/455          ││                           │
│                           ││                           │
│          766 Rows         ││           1 Rows          │
│          (4.04s)          ││          (0.00s)          │
└───────────────────────────┘└───────────────────────────┘
```

### To Reproduce

Create reference table (stays local) and export some partitioned parquet data:
```sql
CREATE TABLE reference (
  id INT NOT NULL,
  example_partition TEXT NOT NULL,
  PRIMARY KEY (id)
) ;

CREATE TABLE partitioned_data (
  example_partition TEXT NOT NULL,
  value TEXT NOT NULL
) ;

INSERT INTO reference
(id, example_partition)
VALUES
(1, 'PartitionValue'),
(2, 'DifferentPartitionValue'),
(3, 'YetAnotherPartitionValue') ;

INSERT INTO partitioned_data
(example_partition, value)
VALUES
('PartitionValue', 'Foo'),
('DifferentPartitionValue', 'Bar') ;

COPY partitioned_data
TO 'example' (
  FORMAT parquet,
  PARTITION_BY (example_partition)
) ;

DROP TABLE partitioned_data ;
```

The filter pushdown is not applied:
```sql
EXPLAIN ANALYZE 
WITH r AS (
  SELECT *
  FROM reference
  WHERE id = 1
)
SELECT *
FROM read_parquet(
  'example/**/*.parquet',
  hive_partitioning = true,
  hive_types = {'example_partition': TEXT}
) partitioned_data
INNER JOIN r
ON partitioned_data.example_partition = r.example_partition ;
```
```
┌─────────────────────────────────────┐
│┌───────────────────────────────────┐│
││         HTTPFS HTTP Stats         ││
││                                   ││
││            in: 0 bytes            ││
││            out: 0 bytes           ││
││              #HEAD: 0             ││
││              #GET: 0              ││
││              #PUT: 0              ││
││              #POST: 0             ││
││             #DELETE: 0            ││
│└───────────────────────────────────┘│
└─────────────────────────────────────┘
┌────────────────────────────────────────────────┐
│┌──────────────────────────────────────────────┐│
││              Total Time: 0.0031s             ││
│└──────────────────────────────────────────────┘│
└────────────────────────────────────────────────┘
┌───────────────────────────┐
│           QUERY           │
└─────────────┬─────────────┘
┌─────────────┴─────────────┐
│      EXPLAIN_ANALYZE      │
│    ────────────────────   │
│           0 Rows          │
│          (0.00s)          │
└─────────────┬─────────────┘
┌─────────────┴─────────────┐
│         PROJECTION        │
│    ────────────────────   │
│           value           │
│     example_partition     │
│             id            │
│     example_partition     │
│                           │
│           1 Rows          │
│          (0.00s)          │
└─────────────┬─────────────┘
┌─────────────┴─────────────┐
│         HASH_JOIN         │
│    ────────────────────   │
│      Join Type: INNER     │
│                           │
│        Conditions:        │
│    example_partition =    ├──────────────┐
│      example_partition    │              │
│                           │              │
│           1 Rows          │              │
│          (0.00s)          │              │
└─────────────┬─────────────┘              │
┌─────────────┴─────────────┐┌─────────────┴─────────────┐
│         TABLE_SCAN        ││         TABLE_SCAN        │
│    ────────────────────   ││    ────────────────────   │
│         Function:         ││      Table: reference     │
│        READ_PARQUET       ││   Type: Sequential Scan   │
│                           ││                           │
│        Projections:       ││        Projections:       │
│     example_partition     ││             id            │
│           value           ││     example_partition     │
│                           ││                           │
│           1 Rows          ││           1 Rows          │
│          (0.00s)          ││          (0.00s)          │
└───────────────────────────┘└───────────────────────────┘
```

### OS:

macOS

### DuckDB Version:

v1.2.2 7c039464e4

### DuckDB Client:

CLI

### Hardware:

Apple M1 Pro

### Full Name:

Felix Wollschläger

### Affiliation:

N/A

### What is the latest build you tested with? If possible, we recommend testing with the latest nightly build.

I have tested with a stable release

### Did you include all relevant data sets for reproducing the issue?

Yes

### Did you include all code required to reproduce the issue?

- [x] Yes, I have

### Did you include all relevant configuration (e.g., CPU architecture, Python version, Linux distribution) to reproduce the issue?

- [x] Yes, I have

## Comments

**its-felix:**
Reproduced in DuckDB v1.3.0 (Ossivalis) 71c5c07cdd

**its-felix:**
Reproduced in DuckDB v1.3.1 (Ossivalis) 2063dda3e6

**its-felix:**
Reproduced in DuckDB v1.4.0 (Andium) b8a06e4a22

**samansmink:**
Hey @its-felix! really sorry for the lack of response on our end, and thanks for checking in with updated repro's.

This does indeed seem like something we would be interested in implementing, but given our huge backlog I can't really promise we can pick this one up in the near future.

**its-felix:**
It looks like this was implemented in 1.5.0 - nice!

Given the reproducible example from above, I can now see that only the required number of files are being read:
```sql
EXPLAIN ANALYZE 
WITH r AS (
  SELECT *
  FROM reference
  WHERE id = 1
)
SELECT *
FROM read_parquet(
  'example/**/*.parquet',
  hive_partitioning = true,
  hive_types = {'example_partition': TEXT}
) partitioned_data
INNER JOIN r
ON partitioned_data.example_partition = r.example_partition ;
```
->
```
┌─────────────┴─────────────┐┌─────────────┴─────────────┐
│         TABLE_SCAN        ││         TABLE_SCAN        │
│    ────────────────────   ││    ────────────────────   │
│         Function:         ││           Table:          │
│        READ_PARQUET       ││   memory.main.reference   │
│                           ││                           │
│        Projections:       ││      Type: Index Scan     │
│     example_partition     ││                           │
│           value           ││        Projections:       │
│                           ││             id            │
│      Dynamic Filters:     ││     example_partition     │
│     example_partition=    ││                           │
│      'PartitionValue'     ││       Filters: id=1       │
│                           ││                           │
│    Total Files Read: 1    ││                           │
│                           ││                           │
│        Filename(s):       ││                           │
│ example/example_partition ││           0.00s           │
│   =PartitionValue/data_0  ││                           │
│          .parquet         ││                           │
│                           ││                           │
│                           ││                           │
│                           ││                           │
│           1 row           ││           1 row           │
│           0.00s           ││          (0.00s)          │
└───────────────────────────┘└───────────────────────────┘
```

```sql
EXPLAIN ANALYZE 
WITH r AS (
  SELECT *
  FROM reference
  WHERE id IN(1, 2)
)
SELECT *
FROM read_parquet(
  'example/**/*.parquet',
  hive_partitioning = true,
  hive_types = {'example_partition': TEXT}
) partitioned_data
INNER JOIN r
ON partitioned_data.example_partition = r.example_partition ;
```
-->
```
┌─────────────┴─────────────┐┌─────────────┴─────────────┐
│         TABLE_SCAN        ││         TABLE_SCAN        │
│    ────────────────────   ││    ────────────────────   │
│         Function:         ││           Table:          │
│        READ_PARQUET       ││   memory.main.reference   │
│                           ││                           │
│        Projections:       ││   Type: Sequential Scan   │
│     example_partition     ││                           │
│           value           ││        Projections:       │
│                           ││             id            │
│      Dynamic Filters:     ││     example_partition     │
│         optional:         ││                           │
│   example_partition IN (  ││          Filters:         │
│     'PartitionValue',     ││      id>=1 AND id=   ││                           │
│ 'DifferentPartitionValue' ││                           │
│        AND optional:      ││           0.00s           │
│     example_partition<=   ││                           │
│      'PartitionValue'     ││                           │
│                           ││                           │
│    Total Files Read: 2    ││                           │
│                           ││                           │
│        Filename(s):       ││                           │
│    example/**/*.parquet   ││                           │
│                           ││                           │
│                           ││                           │
│                           ││                           │
│           2 rows          ││           2 rows          │
│           0.00s           ││          (0.00s)          │
└───────────────────────────┘└───────────────────────────┘
```

FYI @samansmink

**its-felix:**
reference https://github.com/duckdb/duckdb/pull/19888
