# Filter Pushdown with scalar macro not working

**Issue #21312** | State: open | Created: 2026-03-11 | Updated: 2026-03-12
**Author:** MPizzotti
**Labels:** under review

### What happens?

given this query:
```sql
FROM read_parquet(
    'hive_path/year=*/month=*/*.parquet',
    hive_partitioning = true,
    hive_types = {'year': 'INT', 'month': 'INT'}
)
WHERE [year, month] IN get_hives()
limit 100;
```
I expect duckdb to pushdown the filter and scan just the expected files.

here's the current implementation of get_hives():
```sql
CREATE OR REPLACE MACRO get_hives() as (
  select apply(
    generate_series(MIN(record_date), MAX(record_date), INTERVAL '1 month'),
    lambda d: [year(d), month(d)]
  )
  from lookup_dates
  WHERE gregorian_year='2025'
);
```
and returns this kind of values:
`[[2025, 1], [2025, 2], [2025, 3], [2025, 4], [2025, 5], [2025, 6], [2025, 7], [2025, 8], [2025, 9], [2025, 10], [2025, 11], [2025, 12]]`

but instead, duckdb is scanning the entire hive path and then filtering later:
```
┌─────────────┴─────────────┐
│     BLOCKWISE_NL_JOIN     │
│    ────────────────────   │
│      Join Type: INNER     │
│                           │
│         Condition:        │
│  contains(SUBQUERY, CAST  │
│  (list_value(year, month) ├──────────────┐
│        AS BIGINT[]))      │              │
│                           │              │
│                           │              │
│                           │              │
│        28,672 rows        │              │
│          356.30s          │              │
└─────────────┬─────────────┘              │
┌─────────────┴─────────────┐┌─────────────┴─────────────┐
│         TABLE_SCAN        ││         PROJECTION        │
│    ────────────────────   ││    ────────────────────   │
│         Function:         ││ CASE  WHEN ((#1 > 1)) THEN│
│        READ_PARQUET       ││   ("error"('More than one │
│                           ││      row returned by a    │
│        Projections:       ││     subquery used as an   │
│            year           ││     expression - scalar   │
│           month           ││     subqueries can only   │
|            ...            ||                           |
│                           ││                           │
│      309,170,896 rows     ││           1 row           │
│          409.23s          ││          (0.00s)          │
└───────────────────────────┘└─────────────┬─────────────┘
```

BUT, if i create a temporary variable like so:
```sql
set variable hives = get_hives();
FROM read_parquet(
    'hive_path/year=*/month=*/*.parquet',
    hive_partitioning = true,
    hive_types = {'year': 'INT', 'month': 'INT'}
)
WHERE [year, month] IN getvariable('hives')
limit 100;
```
The scan works fine, providing a massive boost:
```
┌─────────────┴─────────────┐
│         HASH_JOIN         │
│    ────────────────────   │
│      Join Type: SEMI      │
│                           │
│        Conditions:        │
│  file_index = file_index  │
│     file_row_number =     ├──────────────┐
│       file_row_number     │              │
│                           │              │
│                           │              │
│                           │              │
│          100 rows         │              │
│           0.00s           │              │
└─────────────┬─────────────┘              │
┌─────────────┴─────────────┐┌─────────────┴─────────────┐
│         TABLE_SCAN        ││      STREAMING_LIMIT      │
│    ────────────────────   ││    ────────────────────   │
│         Function:         ││                           │
│        READ_PARQUET       ││                           │
│                           ││           0.00s           │
│        Projections:       ││                           │
│            year           ││                           │
│           month           ││                           │
|            ...            ||                           |
│                           ││                           │
│    Total Files Read: 12   ││                           │
│                           ││                           │
│        Filename(s):       ││                           │
│    :                      ││                           │
│  /test_hive/year          ││                           │
│    =2025/month=1/data_0   ││                           │
│ .parquet, :               ││                           │
│   /test_hive              ││                           │
│ /year=2025/month=10/data_0││                           │
│ .parquet, :               ││                           │
│   /test_hive              ││                           │
│ /year=2025/month=11/data_0││                           │
│ .parquet, :               ││                           │
│   /test_hive              ││                           │
│ /year=2025/month=12/data_0││                           │
│ .parquet, :               ││                           │
│   /test_hive              ││                           │
│ /year=2025/month=2/data_0 ││                           │
│       .parquet, ...       ││                           │
│                           ││                           │
│                           ││                           │
│                           ││                           │
│          100 rows         ││          100 rows         │
│           4.33s           ││          (0.00s)          │
└───────────────────────────┘└─────────────┬─────────────┘
                             ┌─────────────┴─────────────┐
                             │         TABLE_SCAN        │
                             │    ────────────────────   │
                             │         Function:         │
                             │        READ_PARQUET       │
                             │                           │
                             │       File Filters:       │
                             │ contains([[2025, 1], [2025│
                             │ , 2], [2025, 3], [2025, 4]│
                             │  , [2025, 5], [2025, 6],  │
                             │   [2025, 7], [2025, 8],   │
                             │  [2025, 9], [2025, 10],   │
                             │  [2025, 11], [2025, 12]], │
                             │    CAST(list_value(year,  │
                             │    month) AS BIGINT[]))   │
                             │                           │
                             │   Scanning Files: 12/28   │
                             │                           │
                             │                           │
                             │                           │
                             │         2,048 rows        │
                             │           0.00s           │
                             └───────────────────────────┘
```

Since it's a subquery result, is there a way to force the materialization of an intermediate result and store it as a constant?

### To Reproduce

can be reproduced using a range query on 2 dates

### OS:

Windows

### DuckDB Version:

1.4.2+

### DuckDB Client:

CLI

### Hardware:

_No response_

### Full Name:

Massimiliano

### Affiliation:

Luxottica

### Did you include all relevant configuration (e.g., CPU architecture, Linux distribution) to reproduce the issue?

- [x] Yes, I have

### Did you include all code required to reproduce the issue?

- [x] Yes, I have

### Did you include all relevant data sets for reproducing the issue?

Not applicable - the reproduction does not require a data set

## Comments

**szarnyasg:**
Hi @MPizzotti, thanks for opening this issue.

> Since it's a subquery result, is there a way to force the materialization of an intermediate result and store it as a constant?

You can use the trick described in the [Force Join Order](https://duckdb.org/docs/stable/guides/performance/join_operations#how-to-force-a-join-order) section of the performance guide:

```sql
CREATE TEMP TABLE my_temp_table AS
   SELECT ...;
```

And then put the subquery in the table. This will for the subquery evaluated at this point.

Regarding the pushdown, I see your point. However, this is not a bug and more of a feature request. I'll pass it to the team but cannot guarantee any completion date. If your company would be interested in expediting its implementation, please [get in touch with us](https://duckdblabs.com/contact/).

**MPizzotti:**
thanks for the clarification, i will try to implement as you suggested, @szarnyasg.
My concern is that they are 2 different statements, similarly to using a variable.
The idea is to use a single statement (procedure-like??) i'm not an expert on the matter.

Since i'm using duckdb with node-neo Client, running 2 statement at the same time won't return data correctly.
