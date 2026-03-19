# "* not similar to" is broken

**Issue #21096** | State: closed | Created: 2026-02-26 | Updated: 2026-03-06
**Author:** memeplex
**Labels:** reproduced

### What happens?

```
select * similar to '^([0-9]+)$' from 'embeddings.parquet'
```

Fine.

```
select * not similar to '^([0-9]+)$' from 'embeddings.parquet'
```

```
BinderException: Binder Error: STAR expression is only allowed as the root element of an expression. Use COLUMNS(*) instead.
```

According to https://duckdb.org/docs/stable/sql/expressions/star#column-filtering-via-pattern-matching-operators this syntax should be allowed.

### To Reproduce

```
CREATE TABLE datos AS SELECT 
    1 AS a1, 2 AS a2, 3 AS b1, 4 AS b2;

SELECT * NOT SIMILAR TO '^a[0-9]$' FROM datos;
```

### OS:

x86_64

### DuckDB Version:

1.4.4

### DuckDB Client:

Pythin

### Hardware:

_No response_

### Full Name:

Carlos

### Affiliation:

Mutt

### Did you include all relevant configuration (e.g., CPU architecture, Linux distribution) to reproduce the issue?

- [x] Yes, I have

### Did you include all code required to reproduce the issue?

- [x] Yes, I have

### Did you include all relevant data sets for reproducing the issue?

Not applicable - the reproduction does not require a data set

## Comments

**szarnyasg:**
Hi @memeplex, thanks for reporting this. I could reproduce this for v1.4 but also found that it works on the nightly build of 1.5:

```
DuckDB v1.5.0-dev8128 (Development Version, c43d12535f)
Enter ".help" for usage hints.
memory D CREATE TABLE datos AS SELECT
             1 AS a1, 2 AS a2, 3 AS b1, 4 AS b2;
memory D
memory D SELECT * NOT SIMILAR TO '^a[0-9]$' FROM datos;
┌───────┬───────┐
│  b1   │  b2   │
│ int32 │ int32 │
├───────┼───────┤
│     3 │     4 │
└───────┴───────┘
memory D
```

**taniabogatsch:**
https://github.com/duckdb/duckdb/pull/21177
