# `DISTINCT` and `DISTINCT ON` are applied before and after `ORDER BY` in a `SELECT` clause, respectively

**Issue #16991** | State: open | Created: 2025-04-04 | Updated: 2026-03-01
**Author:** soerenwolfers
**Labels:** reproduced

### What happens?

The `DISTINCT` clause currently is applied *before* the `ORDER BY` clause, whereas the `DISTINCT ON` clause comes after the `ORDER BY` clause.  

They should come in the same place, and the same logic should then be applied to aggregate functions in order to allow the currently disallowed

```sql
array_agg(DISTINCT x ORDER BY y)
```

(Follow up from https://github.com/duckdb/duckdb/discussions/16940)

### To Reproduce

Currently, 
```sql
SELECT
    DISTINCT 
    x
FROM 
    (VALUES (1, 1), (2, 0), (1, -1)) _(x, y)
ORDER BY
    y;
```
returns 
```
┌───────┐
│   x   │
│ int32 │
├───────┤
│     2 │
│     1 │
└───────┘
```

whereas simply adding `ON (x)` as in 

```sql
SELECT
    DISTINCT ON (x)
    x
FROM 
    (VALUES (1, 1), (2, 0), (1, -1)) _(x, y)
ORDER BY
    y;
```
returns 
```
┌───────┐
│   x   │
│ int32 │
├───────┤
│     1 │
│     2 │
└───────┘
```

This shows that `DISTINCT` is applied before `ORDER BY` and `DISTINCT ON` after `ORDER BY`. 
(In PostgreSQL, the queries throw `Query Error: for SELECT DISTINCT, ORDER BY expressions must appear in select list` and `SELECT DISTINCT ON expressions must match initial ORDER BY expressions`, respectively.)

The query below, which should be equivalent to the first query (up to the shape of the result), throws an error:

```sql
SELECT
    array_agg(DISTINCT x ORDER BY y)
FROM 
    (VALUES (1, 1), (2, 0), (1, -1)) _(x, y)
```
```
Binder Error: In a DISTINCT aggregate, ORDER BY expressions must appear in the argument list
```

 instead of returning the expected

```
┌───────────────────────┐
│ array_agg(x) │
│        int32[]        │
├───────────────────────┤
│ [2, 1]                │
└───────────────────────┘
```

### OS:

Linux

### DuckDB Version:

1.2.1-dev212

### DuckDB Client:

Python

### Hardware:

.

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
