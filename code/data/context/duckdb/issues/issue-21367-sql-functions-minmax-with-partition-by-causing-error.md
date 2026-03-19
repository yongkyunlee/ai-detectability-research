# SQL functions min/max with partition by causing error

**Issue #21367** | State: open | Created: 2026-03-13 | Updated: 2026-03-16
**Author:** ironhorse11-pro
**Labels:** reproduced

### What happens?

When running a min or max with a partition by function is returning the error NotImplementedException: Not implemented Error: Logical Operator Copy requires the logical operator and all of its children to be serializable: PandasScan function cannot be serialized.

This is only happening once I upgrade to version 1.5.0. Anything earlier works as expected.

 

### To Reproduce

```
import duckdb
import pandas as pd
from datetime import datetime, timedelta
import numpy as np

# Example: create base_data
now = datetime.now()
random_offset_days = np.random.randint(0, 30)
random_offset_seconds = np.random.randint(0, 24*60*60)
random_datetime = now - timedelta(days=random_offset_days, seconds=random_offset_seconds)

base_data = pd.DataFrame(
    {
        "id": [123],
        "lastupdatedtime": [random_datetime],
    }
)

sql = """
    SELECT DISTINCT
        id,
        min(lastupdatedtime) over (partition by id) as min
    FROM base_data
"""
test = duckdb.query(sql).df()
```

```
NotImplementedException: Not implemented Error: Logical Operator Copy requires the logical operator and all of its children to be serializable: PandasScan function cannot be serialized
```

### OS:

Debian GNU/Linux 12 (bookworm), x86_64

### DuckDB Version:

1.5.0

### DuckDB Client:

Python

### Hardware:

_No response_

### Full Name:

Jonah Cummings

### Affiliation:

Progressive Insurance

### Did you include all relevant configuration (e.g., CPU architecture, Linux distribution) to reproduce the issue?

- [x] Yes, I have

### Did you include all code required to reproduce the issue?

- [x] Yes, I have

### Did you include all relevant data sets for reproducing the issue?

Yes

## Comments

**ironhorse11-pro:**
My account may look brand new. This is because my corporation does not allow us to interact with repos outside our org, so I had to make a new account to post this.

**nsiicm0:**
This does not seem to be solely restricted to pandas and min/max aggregates. 
I can reproduce this issue on 1.5 with pretty much any partitioned window aggregate function (in my case "SUM") and also for reading CSV files (from S3 and local).

A workaround on my end is to "ORDER" the window function. A simple `ORDER BY NULL` works wonders.

```sql
COPY (
    SELECT 'a' AS x, 10 AS a, 20 AS b, 30 AS c
    UNION ALL BY NAME
    SELECT 'b' AS x, 11 AS a, 21 AS b, 31 AS c
    UNION ALL BY NAME
    SELECT 'c' AS x, 12 AS a, 22 AS b, 32 AS c
) TO 'test.csv'
```

Works:
```python
duckdb.sql("""
FROM 'test.csv'
SELECT 
    x, MAX(a) OVER (PARTITION BY x ORDER BY NULL)
""")
```

Fails:

```python
duckdb.sql("""
FROM 'test.csv'
SELECT 
    x, MAX(a) OVER (PARTITION BY x)
""")
```

This issue does not seem to appear with parquet files.
