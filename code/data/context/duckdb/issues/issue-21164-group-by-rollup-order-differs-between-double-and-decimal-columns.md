# `GROUP BY ROLLUP` order differs between `DOUBLE` and `DECIMAL` columns

**Issue #21164** | State: closed | Created: 2026-03-04 | Updated: 2026-03-05
**Author:** Matt711
**Labels:** needs triage

### What happens?

When `GROUP BY ROLLUP` produces multiple rows with the same `ORDER BY` keys, the order of those tied rows differs depending on whether an aggregated column uses `DOUBLE` vs `DECIMAL`. Is this behavior expected or is this a bug?

### To Reproduce

MRE
```python
import duckdb

QUERY = """
WITH data(channel, id, sales) AS (
    VALUES
        ('catalog channel', NULL,  100.0),
        ('catalog channel', NULL,  200.0),
        ('catalog channel',    1,   50.0)
),
grouped AS (
    SELECT channel, id, sum(sales) AS sales
    FROM data
    GROUP BY ROLLUP (channel, id)
)
SELECT channel, id, sales
FROM grouped
ORDER BY channel, id
LIMIT 100;
"""

QUERY_DECIMAL = """
WITH data(channel, id, sales) AS (
    VALUES
        ('catalog channel', NULL,  100.0::DECIMAL(18,2)),
        ('catalog channel', NULL,  200.0::DECIMAL(18,2)),
        ('catalog channel',    1,   50.0::DECIMAL(18,2))
),
grouped AS (
    SELECT channel, id, sum(sales) AS sales
    FROM data
    GROUP BY ROLLUP (channel, id)
)
SELECT channel, id, sales
FROM grouped
ORDER BY channel, id
LIMIT 100;
"""

con = duckdb.connect()
print("float:")
print(con.execute(QUERY).df().to_string())
print()
print("decimal:")
print(con.execute(QUERY_DECIMAL).df().to_string())

```

### OS:

x86_64

### DuckDB Version:

1.4.4

### DuckDB Client:

Python

### Hardware:

_No response_

### Full Name:

Matt Murray

### Affiliation:

RAPIDS specifically https://github.com/rapidsai/cudf

### Did you include all relevant configuration (e.g., CPU architecture, Linux distribution) to reproduce the issue?

- [x] Yes, I have

### Did you include all code required to reproduce the issue?

- [x] Yes, I have

### Did you include all relevant data sets for reproducing the issue?

Yes

## Comments

**Matt711:**
Re:

> Is this behavior expected or is this a bug?

"bug" might be too strong, but it definitely surprised me 😄

**Mytherin:**
Thanks for reporting! This is likely expected behavior. `DECIMAL` performs exact arithmetic, and thus does not suffer from floating point errors. You can use `fsum` (or `kahan_sum`) to use a floating point summation algorithm that uses a different algorithm to minimize floating point errors.

**soerenwolfers:**
floating point addition is exact on small integers and the numerical column is not used for sorting here anyway .That being said, neither SQL standard nor duckdb guarantee order preservation for neither aggregations nor sorts (i.e. stable sorts), so unless I'm mistaken about something this does very much look like expected behavior.

**Mytherin:**
Ah indeed, this is not related to floating point accuracy, but rather to the sort itself being underspecified.

**Matt711:**
Thanks folks! closing...
