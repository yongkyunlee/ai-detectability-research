# `json_extract` vs. `::` cast operator precedence

**Issue #14889** | State: open | Created: 2024-11-19 | Updated: 2026-03-18
**Author:** manticore-projects
**Labels:** expected behavior

### What happens?

Casting a `JSON_EXTRACT` expression works only when put into explicit brackets although those brackets should not be necessary.

### To Reproduce

```sql
-- fails: No function matches the given name and argument types 'json_extract(JSON, DECIMAL(5,2))'
SELECT c1::JSON->'price'::decimal(5,2) j
    FROM VALUES('{ "price": 5 }') AS T(c1);    

-- works:
SELECT (c1::JSON->'price')::decimal(5,2) j
    FROM VALUES('{ "price": 5 }') AS T(c1);   
```

```
/*
┌──────┐
│ j    │
├──────┤
│ 5.00 │
└──────┘
*/
```


### OS:

Linux

### DuckDB Version:

1.1.3

### DuckDB Client:

Java

### Hardware:

_No response_

### Full Name:

Andreas Reichel

### Affiliation:

manticore-projects.com

### What is the latest build you tested with? If possible, we recommend testing with the latest nightly build.

I have tested with a stable release

### Did you include all relevant data sets for reproducing the issue?

Yes

### Did you include all code required to reproduce the issue?

- [X] Yes, I have

### Did you include all relevant configuration (e.g., CPU architecture, Python version, Linux distribution) to reproduce the issue?

- [X] Yes, I have

## Comments

**szarnyasg:**
Hi, the problem here is that the `->` operator is also used for lambdas where it has to have a low precedence to allow expressions such as `x -> x::INT`. So in JSON, the extraction operation necessitates extra parens. I have a WIP PR that will explain this: https://github.com/duckdb/duckdb-web/pull/3922

**sirfz:**
The same issue happens with conditions as well, for example:

```
data->'field' is null
```

would evaluate `'field' is null` first and then try to evaluate `data->false` and fail

**Mytherin:**
While this is currently expected behavior, we have deprecated the conflicting lambda syntax and are planning to address this in a future release (after we have removed the conflicting lambda syntax).
