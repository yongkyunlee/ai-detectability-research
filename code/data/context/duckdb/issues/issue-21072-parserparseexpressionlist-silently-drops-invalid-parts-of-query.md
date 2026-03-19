# `Parser::ParseExpressionList()` silently drops invalid parts of query

**Issue #21072** | State: closed | Created: 2026-02-25 | Updated: 2026-03-12
**Author:** jakkes
**Labels:** reproduced

### What happens?

I was asked to open an issue here, see https://github.com/duckdb/duckdb-python/issues/339.

This seems to compile, but the `order by i` at the end seems to be doing nothing?

```python
duckdb.query("select unnest([0, 0, 1, 1]) as i, unnest([1, 2, 3, 4]) as x").aggregate("i, first(x) as x order by i")
```
Given that the 'correct' statement is
```python
duckdb.query("select unnest([0, 0, 1, 1]) as i, unnest([1, 2, 3, 4]) as x").aggregate("i, first(x order by i) as x")
```
it seems that the former statement should raise an error. Other invalid things suffixes (e.g. `first(x) as x where x != 1`) are also dropped silently.

### To Reproduce

```python
import duckdb
duckdb.query("select unnest([0, 0, 1, 1]) as i, unnest([1, 2, 3, 4]) as x").aggregate("i, first(x) as x order by i")
```
expected behavior is some sort of exception raised.

### OS:

Ubuntu

### DuckDB Version:

1.4.3

### DuckDB Client:

Python

### Hardware:

_No response_

### Full Name:

Jakob Stigenberg

### Affiliation:

Qubos Systematic

### Did you include all relevant configuration (e.g., CPU architecture, Linux distribution) to reproduce the issue?

- [x] Yes, I have

### Did you include all code required to reproduce the issue?

- [x] Yes, I have

### Did you include all relevant data sets for reproducing the issue?

Not applicable - the reproduction does not require a data set

## Comments

**evertlammerts:**
`Parser::ParseExpressionList()` uses only the select list, and silently drops everything else. E.g. a filter will also be ignored, as long as it parses successfully:

```
import duckdb
duckdb.query("select unnest([0, 0, 1, 1]) as i, unnest([1, 2, 3, 4]) as x").aggregate("i, first(x) as x where things = 'bad'")
```

**Dtenwolde:**
Fixed with https://github.com/duckdb/duckdb/pull/21306
