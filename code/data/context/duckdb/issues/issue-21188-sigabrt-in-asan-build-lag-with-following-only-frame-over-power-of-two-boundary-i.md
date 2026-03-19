# SIGABRT in ASAN build: `lag()` with `FOLLOWING`-only frame over power-of-two boundary integers and double `ROLLUP`

**Issue #21188** | State: open | Created: 2026-03-05 | Updated: 2026-03-06
**Author:** AldonahZero
**Labels:** under review

### What happens?

DuckDB's ASAN-instrumented library terminates with **SIGABRT** (signal 6) when a query uses:

- **`lag(x,1) OVER (ORDER BY max(x) DESC ROWS BETWEEN 2 FOLLOWING AND 4 FOLLOWING)`** — `lag` (looks backward) with a `FOLLOWING`-only frame. This is semantically inverted; the frame-width computation may underflow to a large unsigned value when `start > end` in the physical row direction.
- **Power-of-two boundary integers** in the UNION input: `10239/10240` (2¹⁰ boundary), `10485247/10485248` (2²³-1/2²³), `2146959359/2146959360` (2³¹-1 boundary), `-536870913/-536870912` (-2²⁹ boundary). These trigger signed-integer overflow in ROLLUP offset or sort-key arithmetic.
- **`LEAD(1,70) OVER ()` inside the source UNION** — offset 70 over a 10-row input yields NULL for all rows; the NULL column fed to `CONCAT` may leave ROLLUP string buffers uninitialised.
- **`GROUP BY ROLLUP(x,x), ROLLUP(x,x)`** — double ROLLUP cross-product produces 97 output rows (confirmed in vanilla build).

**This is the most critical bug in the set:** the vanilla release build exits 0 and returns 97 rows silently, masking the underlying memory-safety violation. The results may be incorrect.

### To Reproduce

```sql
DROP TABLE IF EXISTS x ;

SELECT x = lag ( x , 1 ) OVER ( ORDER BY max ( x ) DESC ROWS BETWEEN 2 FOLLOWING AND 4 FOLLOWING ) FROM ( SELECT 'MEMORY' AS x , 2 AS x , 3 AS x UNION SELECT 4 AS x , NULL AS x , x UNION SELECT x , CONCAT ( 'B' ) , CONCAT ( ( -1 * x ) , ( x = 10 AND x = -1 ) OR ( x = 1 AND x = 3 ) ) FROM ( SELECT 10239 AS x UNION SELECT 10240 AS x UNION SELECT 10485247 AS x UNION SELECT 10485248 AS x UNION SELECT 2146959359 AS x UNION SELECT 2146959360 AS x UNION SELECT -536870913 AS x UNION SELECT -536870912 AS x UNION SELECT -1 AS x UNION SELECT LEAD ( 1 , 70 ) OVER ( ) AS x ) ) AS x GROUP BY ROLLUP ( x , x ) , ROLLUP ( x , x ) ORDER BY x , x , x ;
```

### OS:

Ubuntu 22.04

### DuckDB Version:

v1.4.4

### DuckDB Client:

Python

### Hardware:

_No response_

### Full Name:

research

### Affiliation:

research

### Did you include all relevant configuration (e.g., CPU architecture, Linux distribution) to reproduce the issue?

- [x] Yes, I have

### Did you include all code required to reproduce the issue?

- [x] Yes, I have

### Did you include all relevant data sets for reproducing the issue?

Yes

## Comments

**szarnyasg:**
@AldonahZero thanks for the report. On the `v1.5-variegata` branch, I am unable to reproduce the memory violation even with the `relassert` build. Can you please try this branch?
