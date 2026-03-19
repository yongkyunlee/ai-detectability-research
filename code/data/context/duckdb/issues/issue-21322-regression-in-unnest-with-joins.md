# Regression in unnest with joins.

**Issue #21322** | State: closed | Created: 2026-03-12 | Updated: 2026-03-16
**Author:** coady
**Labels:** reproduced

### What happens?

```
SELECT * FROM (SELECT [1, 2] AS values) t, UNNEST(LIST_ZIP(t.values, [0, 1])) u(unnested);
```
errors as of 1.5.
```
INTERNAL Error:
Failed to cast expression to type - expression type mismatch

Stack Trace:

0        duckdb::Exception::ToJSON(duckdb::ExceptionType, std::__1::basic_string, std::__1::allocator> const&) + 48
1        duckdb::Exception::Exception(duckdb::ExceptionType, std::__1::basic_string, std::__1::allocator> const&) + 36
2        duckdb::InternalException::InternalException(std::__1::basic_string, std::__1::allocator> const&) + 20
3        duckdb::BoundColumnRefExpression const& duckdb::BaseExpression::Cast() const + 96
4        duckdb::UnnestRewriter::FindCandidates(duckdb::unique_ptr, true>&, duckdb::unique_ptr, true>&, duckdb::vector, true>>, true, std::__1::allocator, true>>>>&) + 868
...
```

### To Reproduce

```
SELECT * FROM (SELECT [1, 2] AS values) t, UNNEST(LIST_ZIP(t.values, [0, 1])) u(unnested);
```

### OS:

macOS arm64

### DuckDB Version:

1.5.0

### DuckDB Client:

CLI

### Hardware:

_No response_

### Full Name:

A. Coady

### Affiliation:

open source

### Did you include all relevant configuration (e.g., CPU architecture, Linux distribution) to reproduce the issue?

- [x] Yes, I have

### Did you include all code required to reproduce the issue?

- [x] Yes, I have

### Did you include all relevant data sets for reproducing the issue?

Not applicable - the reproduction does not require a data set

## Comments

**JeromeLefebvre:**
Hitting the same issue with this query:

```sql
FROM read_json('data.json') AS src
CROSS JOIN UNNEST(src.data.metrics) AS t(r);
```

With this data.json file
```json
{
  "data" : {
    "metrics" : []
  }
}
```

**Mytherin:**
Thanks for reporting - this issue has been fixed by https://github.com/duckdb/duckdb/pull/21209. The fix will land in v1.5.1
