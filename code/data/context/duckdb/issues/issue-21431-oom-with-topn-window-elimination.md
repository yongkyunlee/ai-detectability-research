# OOM with TopN Window Elimination

**Issue #21431** | State: open | Created: 2026-03-17 | Updated: 2026-03-18
**Author:** JasonPunyon
**Labels:** reproduced

### What happens?

Queries like the one in the reproducer (derived from my production workload) cause OOMs after the TopN Window Elimination optimization was opened up in 5f9e4101c164d7731008344c7d7e422e2f4f7448. On this example it'll more than triple the memory used and blow out the limit.

### To Reproduce

```
-- TopN Window Elimination causes OOM
-- Commit: 5f9e4101c164d7731008344c7d7e422e2f4f7448
--
-- Expected: query fails with Out of Memory.
-- Uncomment the next line to see it succeed.
-- SET disabled_optimizers = 'top_n_window_elimination';

SET memory_limit = '1GB';

CREATE TABLE t (group_id INT, category INT, value INT);

INSERT INTO t
SELECT i / 2, i % 10, i % 1000
FROM range(0, 400000) r(i);

WITH counts AS (
    SELECT group_id, category, COUNT(*) AS cnt
    FROM t
    GROUP BY group_id, category
),
ranked AS (
    SELECT *,
        ROW_NUMBER() OVER (PARTITION BY group_id ORDER BY cnt DESC) AS rn
    FROM counts
    QUALIFY rn <= 50
)
SELECT group_id, category, cnt
FROM ranked;
```

### OS:

Bookworm

### DuckDB Version:

main

### DuckDB Client:

cli

### Hardware:

_No response_

### Full Name:

Jason Punyon

### Affiliation:

Sumble

### Did you include all relevant configuration (e.g., CPU architecture, Linux distribution) to reproduce the issue?

- [x] Yes, I have

### Did you include all code required to reproduce the issue?

- [x] Yes, I have

### Did you include all relevant data sets for reproducing the issue?

Yes

## Comments

**feichai0017:**
I wanna take this

**Mytherin:**
Thanks - I had a brief look and figured out the issue is specifically caused by `QUALIFY rn <= 50`. This gets rewritten to `arg_min_max_n(..., 50)`. `arg_min_max_n` pre-allocates all 50 slots up-front, but MAX(rn) is 3 in this case, so these slots are almost all empty.

The solution would be to either (1) limit the top-n window optimizer to only doing this optimization with smaller QUALIFY clauses, or (2) have the BinaryAggregateHeap do allocation in a different manner so that it doesn't pre-allocate all slots up front.

**Mytherin:**
I think (2) is the nicer solution since that reduces `arg_min_max_n` memory usage in general, not just for this specific instance of it.
