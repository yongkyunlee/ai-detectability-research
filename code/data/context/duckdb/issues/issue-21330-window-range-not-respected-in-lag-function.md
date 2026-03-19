# Window range not respected in `lag` function

**Issue #21330** | State: closed | Created: 2026-03-12 | Updated: 2026-03-12
**Author:** jankramer
**Labels:** needs triage

### What happens?

Specifying a window with a range (e.g. `order by ts range between interval 15 minutes preceding...`) does not have any effect when using the `lag` window function.

### To Reproduce

In the following example, I expected `ts_lag` to be `NULL` for every row, since the window frame range is shorter than the delta between the rows, but this is not the case. The result of `array_agg` does seem to observe the window range as I expected.

Query:
```
select ts,
       lag(ts) over w as ts_lag,
       array_agg(ts) over w as window_values,
  from unnest(['2026-01-01T12:00:00Z', '2026-01-01T12:30:00Z', '2026-01-01T13:00:00Z']) t(ts)
window w as (order by ts::timestamp range between interval 15 minutes preceding and current row);
```

Output:
```
┌──────────────────────┬──────────────────────┬──────────────────────────┐
│          ts          │        ts_lag        │      window_values       │
│       varchar        │       varchar        │        varchar[]         │
├──────────────────────┼──────────────────────┼──────────────────────────┤
│ 2026-01-01T12:00:00Z │ NULL                 │ ['2026-01-01T12:00:00Z'] │
│ 2026-01-01T12:30:00Z │ 2026-01-01T12:00:00Z │ ['2026-01-01T12:30:00Z'] │
│ 2026-01-01T13:00:00Z │ 2026-01-01T12:30:00Z │ ['2026-01-01T13:00:00Z'] │
└──────────────────────┴──────────────────────┴──────────────────────────┘
```

### OS:

MacOS arm64

### DuckDB Version:

1.5.0

### DuckDB Client:

CLI (also reproducible on https://shell.duckdb.org/)

### Hardware:

_No response_

### Full Name:

Jan Kramer

### Affiliation:

n/a

### Did you include all relevant configuration (e.g., CPU architecture, Linux distribution) to reproduce the issue?

- [x] Yes, I have

### Did you include all code required to reproduce the issue?

- [x] Yes, I have

### Did you include all relevant data sets for reproducing the issue?

Yes

## Comments

**szarnyasg:**
Hi @jankramer, thanks for the report! I converted the reproducer to be Postgres-compatible and it returns the same result (rendered in my timezone, CET):

```sql
create table tbl (ts timestamptz);

insert into tbl values
  ('2026-01-01T12:00:00Z'),
  ('2026-01-01T12:30:00Z'),
  ('2026-01-01T13:00:00Z');

select ts,
       lag(ts) over w as ts_lag,
       array_agg(ts) over w as window_values
from tbl
window w as (order by ts::timestamp range between interval '15 minutes' preceding and current row);
```
```
           ts           |         ts_lag         |       window_values
------------------------+------------------------+----------------------------
 2026-01-01 13:00:00+01 |                        | {"2026-01-01 13:00:00+01"}
 2026-01-01 13:30:00+01 | 2026-01-01 13:00:00+01 | {"2026-01-01 13:30:00+01"}
 2026-01-01 14:00:00+01 | 2026-01-01 13:30:00+01 | {"2026-01-01 14:00:00+01"}
```

cc-ing @hawkfish who likely has further insight into this.

**jankramer:**
Just learned from @hawkfish in Discord that this is expected behavior: the `lag` function does not use window framing. A workaround is specifying a secondary ordering  (`lag( ts order by ts)`) which indeed yields the expected result.

Thanks for the quick triage and suggested workaround!
