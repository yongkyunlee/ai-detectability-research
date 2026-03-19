# ASOF JOIN with LIMIT hangs indefinitely when input has ≥ 64 rows

**Issue #21244** | State: closed | Created: 2026-03-09 | Updated: 2026-03-12
**Author:** zhura
**Labels:** reproduced

### What happens?

ASOF JOIN combined with a LIMIT clause causes the query to hang forever (never returns) when the input CTEs/tables contain 64 or more rows. With fewer than 64 rows it produces correct results. Removing LIMIT works correctly for any number of rows.

### To Reproduce

```python
import duckdb

con = duckdb.connect()

sql = """
WITH trades AS (
    SELECT
        'AAPL' AS symbol,
        TIMESTAMP '2024-01-01 10:00:00' + idx * INTERVAL 10 SECONDS AS trade_time,
        100 AS quantity
    FROM range(64) AS trade_rows(idx)   -- hangs; change to 63 to succeed
),
quotes AS (
    SELECT
        'AAPL' AS symbol,
        TIMESTAMP '2024-01-01 09:59:50' + idx * INTERVAL 10 SECONDS AS quote_time,
        150.0 AS price
    FROM range(64) AS quote_rows(idx)
)
SELECT
    t.symbol,
    t.trade_time,
    t.quantity,
    q.quote_time,
    q.price,
    t.quantity * q.price AS notional
FROM trades AS t
ASOF LEFT JOIN quotes AS q
    ON t.symbol = q.symbol
   AND t.trade_time >= q.quote_time
LIMIT 5
"""

df = con.execute(sql).df()   # <-- hangs here forever
print(df)
```

### OS:

OSX, Windows

### DuckDB Version:

1.5.0

### DuckDB Client:

Python 3.10-3.14

### Hardware:

_No response_

### Full Name:

Aliaksandr Zhura

### Affiliation:

Infio

### Did you include all relevant configuration (e.g., CPU architecture, Linux distribution) to reproduce the issue?

- [ ] Yes, I have

### Did you include all code required to reproduce the issue?

- [x] Yes, I have

### Did you include all relevant data sets for reproducing the issue?

No - Other reason (please specify in the issue body)

## Comments

**hawkfish:**
Hi @zhura - thanks for the report. This seems to be a threading issue of some kind. It succeeds when the thread count is 1.

**hawkfish:**
Missing break - PR up.

**Mytherin:**
Should be fixed by https://github.com/duckdb/duckdb/pull/21250
