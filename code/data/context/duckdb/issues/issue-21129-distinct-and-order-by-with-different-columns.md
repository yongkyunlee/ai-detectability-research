# Distinct and order by with different columns

**Issue #21129** | State: open | Created: 2026-03-01 | Updated: 2026-03-08
**Author:** minouminou
**Labels:** reproduced, Needs Documentation

### What happens?

When selecting a distinct rows and ordering by another column DuckDB returns strange result. Most of RDBMS return error on queries like this, except MySQL (behavior is documented). Behavior should be documented or database should throw an exception.

### To Reproduce

```sql
create table t1 (a integer, b integer);
INSERT INTO t1 VALUES (2,1),(1,2),(3,3),(2,4);
SELECT * FROM t1;
```
```
┌───┬───┐
│ a ┆ b │
╞═══╪═══╡
│ 2 ┆ 1 │
│ 1 ┆ 2 │
│ 3 ┆ 3 │
│ 2 ┆ 4 │
└───┴───┘
```
```sql
SELECT DISTINCT a FROM t1 ORDER BY b ASC;
```
```
┌───┐
│ a │
╞═══╡
│ 2 │
│ 1 │
│ 3 │
└───┘
```
```sql
SELECT DISTINCT a FROM t1 ORDER BY b DESC;
```
```
┌───┐
│ a │
╞═══╡
│ 3 │
│ 1 │
│ 2 │
└───┘
```

### OS:

Windows 11

### DuckDB Version:

v1.4.4

### DuckDB Client:

DuckDB Web Shell

### Hardware:

_No response_

### Full Name:

Andrey Petrov

### Affiliation:

no

### Did you include all relevant configuration (e.g., CPU architecture, Linux distribution) to reproduce the issue?

- [x] Yes, I have

### Did you include all code required to reproduce the issue?

- [x] Yes, I have

### Did you include all relevant data sets for reproducing the issue?

Not applicable - the reproduction does not require a data set

## Comments

**Tishj:**
Looks like DISTINCT is applied first, and then the result set gets sorted
Which explains the output you're seeing in the second select

**soerenwolfers:**
@Tishj Unfortunately, `DISTINCT ON` works the opposite way: https://github.com/duckdb/duckdb/issues/16991
