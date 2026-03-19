# Summarize gives Out of Range Error due to inf/-inf 

**Issue #14373** | State: open | Created: 2024-10-15 | Updated: 2026-03-12
**Author:** paultiq
**Labels:** reproduced

### What happens?

`SUMMARIZE ` results in `STDDEV_SAMP is out of range!` error if any column contains an inf value. 

This occurs for any stddev, variance, regr_r2, etc function. 

** Would prefer to see null values or inf values or something *else* other than an exception. 

### To Reproduce

```sql

CREATE OR REPLACE TABLE abc as 
SELECT 1/0 as someinfvalue, -1/0 as otherinfvalue, 'foo' as anotherval
UNION ALL SELECT 2 as someinfvalue, 3 as otherinfvalue, 'foo' as anotherval
;

SUMMARIZE abc;
```

Similarly, this would occur with: 
```sql
SELECT stddev(someinfvalue) 
FROM abc
```

This, of course, also happens with variance, regr_r2, etc. 


### OS:

Windows

### DuckDB Version:

1.1.2

### DuckDB Client:

Python

### Hardware:

_No response_

### Full Name:

Paul T

### Affiliation:

Iqmo

### What is the latest build you tested with? If possible, we recommend testing with the latest nightly build.

I have tested with a nightly build

### Did you include all relevant data sets for reproducing the issue?

Yes

### Did you include all code required to reproduce the issue?

- [X] Yes, I have

### Did you include all relevant configuration (e.g., CPU architecture, Python version, Linux distribution) to reproduce the issue?

- [X] Yes, I have

## Comments

**soerenwolfers:**
I think it should return `NaN`, like many other operations listed at https://github.com/duckdb/duckdb/discussions/10956

**szarnyasg:**
Thanks, this was easy to reproduce. We'll take a look.

**yiyinghu97:**
Is it possible to return NaN if some columns contain NaN?

**soobrosa:**
:+1: kills the chance to use `SUMMARIZE` in production.

**paultiq:**
I had hoped that try() would help in 1.3, but it didn't. Same error: 
```py
CREATE OR REPLACE TABLE abc as 
SELECT 1/0 as someinfvalue, -1/0 as otherinfvalue, 'foo' as anotherval
UNION ALL SELECT 2 as someinfvalue, 3 as otherinfvalue, 'foo' as anotherval
;

SELECT try(stddev(someinfvalue)) 
FROM abc
```

- OutOfRangeException

**reory:**
Still reproducible in v1.5.0 (Windows)

I've been using DuckDB for several of my backend projects (including clinical data dashboards and text analysis suites), and I wanted to confirm that this issue persists in the latest version (v1.5.0).

I have verified that this issue still happens in the latest version. Basic functions like SUM and AVG handle infinity correctly, stat functions still trigger the Outofrangeexception.

Also try() is still blocked. (Binder Error) Not sure how to solve this part. Maybe a deeper look at SQL workaround?

Repo script:

```python
import duckdb
import pandas as pd

# Using ':memory:' allows for a clean, isolated environment for testing
con = duckdb.connect(':memory:')

print("--- Data Initialization ---")
# We include both positive and negative infinity to test mathematical edge cases
try:
    con.execute("""
        CREATE TABLE test_inf AS 
        SELECT 1.0/0.0 as inf_col, 2.0 as normal_col
        UNION ALL 
        SELECT 2.0, 3.0
    """)
    print("✅ Table created successfully with infinity values.")
except Exception as e:
    print(f"❌ Failed to create table: {e}")

print("\n--- Testing Mathematical Aggregates ---")

# We compare simple functions (sum/avg) against statistical ones (stddev/variance)
test_queries = {
    "SUM": "SELECT sum(inf_col) FROM test_inf",
    "AVG": "SELECT avg(inf_col) FROM test_inf",
    "STDDEV": "SELECT stddev(inf_col) FROM test_inf",
    "VARIANCE": "SELECT variance(inf_col) FROM test_inf"
}

for name, query in test_queries.items():
    try:
        result = con.execute(query).fetchone()[0]
        print(f"✅ {name}: {result}")
    except Exception as e:
        # Expect STDDEV and VARIANCE to fail here based on Issue #14373
        print(f"❌ {name} Failed: {str(e).strip()}")

print("\n--- Testing 'TRY' Wrapper Workaround ---")
# Verify if the 'TRY()' function can bypass the OutOfRangeException
# This checks the report that try() 
# is currently blocked by the Binder for aggregates
try:
    res = con.execute("SELECT try(stddev(inf_col)) FROM test_inf").fetchone()
    print(f"✅ TRY(STDDEV) workaround worked: {res}")
except Exception as e:
    print(f"❌ TRY() workaround failed: {e}")
```
Terminal output:

```text
e c:/Users/Admin/Desktop/code/github_duckdb_test/duck_db_test.py
--- Data Initialization ---
✅ Table created successfully with infinity values.

--- Testing Mathematical Aggregates ---
✅ SUM: inf
✅ AVG: inf
❌ STDDEV Failed: Out of Range Error: STDDEV_SAMP is out of range!
❌ VARIANCE Failed: Out of Range Error: VARSAMP is out of range!

--- Testing 'TRY' Wrapper Workaround ---
❌ TRY() workaround failed: Binder Error: aggregates are not allowed inside the TRY expression
```

I hope this reproduction script helps the team narrow down the cause. Thanks for all the hard work on DuckDB.
