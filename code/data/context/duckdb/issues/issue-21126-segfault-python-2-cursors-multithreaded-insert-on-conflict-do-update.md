# [segfault]: Python, 2 cursors, multithreaded, INSERT ... ON CONFLICT DO UPDATE

**Issue #21126** | State: closed | Created: 2026-02-28 | Updated: 2026-03-01
**Author:** txbm
**Labels:** needs triage

### What happens?

Running the minimal Python script below with two threads (each creating its own cursor from the same connection) consistently crashes DuckDB with a segfault/abort during `INSERT ... ON CONFLICT DO UPDATE`.

- The multiple threads guide says each thread should use `conn.cursor()` to create a thread-local connection. https://duckdb.org/docs/stable/guides/python/multiple_threads
- The concurrency guide says conflicting updates should produce a conflict error, not a crash. https://duckdb.org/docs/stable/connect/concurrency

Observed behavior: process crashes (SIGSEGV/SIGABRT/SIGBUS).

Expected behavior: a conflict error or successful retry, but not a crash.

### To Reproduce

```python
import threading
import time

import duckdb

THREAD_COUNT = 2
RUN_SECONDS = 4.0

conn = duckdb.connect()
conn.execute("create table t (id varchar)")
conn.execute("create unique index t_idx on t (id)")

sql_line = "insert into t values ('id_0'), ('id_1') on conflict(id) do update set id = excluded.id"

stop_at = time.monotonic() + RUN_SECONDS
threads: list[threading.Thread] = []

def insert_loop() -> None:
    while time.monotonic() < stop_at:
        db = conn.cursor()
        try:
            db.execute(sql_line)
        except (duckdb.TransactionException, duckdb.ConversionException, duckdb.ConstraintException):
            time.sleep(0.0005)
        finally:
            db.close()

for _ in range(THREAD_COUNT):
    thread = threading.Thread(target=insert_loop, daemon=True)
    thread.start()
    threads.append(thread)

for thread in threads:
    thread.join(timeout=RUN_SECONDS + 1.0)

conn.close()
```

**Run:**

```
PYTHONFAULTHANDLER=1 python duckdb-segfault-repro.py
```

**Output:**

```
Fatal Python error: Segmentation fault

Current thread 0x00000001722f7000 (most recent call first):
  File "duckdb-segfault-repro.py", line 23 in insert_loop
  ...
EXIT:139
```

### OS:

macOS-14.4.1-arm64-arm-64bit

### DuckDB Version:

1.3.0

### DuckDB Client:

Python

### Hardware:

Apple M3 Max, 128 GB RAM (Mac15,9)

### Additional context

LLDB trace shows crash inside `RowGroupCollection::~RowGroupCollection()` during rollback:

```
duckdb::RowGroupCollection::~RowGroupCollection
duckdb::LocalTableStorage::~LocalTableStorage
duckdb::LocalStorage::Rollback
duckdb::DuckTransaction::Rollback
duckdb::DuckTransactionManager::RollbackTransaction
```

- RollbackTransaction: https://github.com/duckdb/duckdb/blob/83ae79e5b7a60820d3fe163e8c60de300fd0c8d1/src/transaction/duck_transaction_manager.cpp#L469-L498
- DuckTransaction::Rollback: https://github.com/duckdb/duckdb/blob/83ae79e5b7a60820d3fe163e8c60de300fd0c8d1/src/transaction/duck_transaction.cpp#L284-L292
- LocalStorage::Rollback: https://github.com/duckdb/duckdb/blob/83ae79e5b7a60820d3fe163e8c60de300fd0c8d1/src/storage/local_storage.cpp#L618-L631
- LocalTableStorage::Rollback: https://github.com/duckdb/duckdb/blob/83ae79e5b7a60820d3fe163e8c60de300fd0c8d1/src/storage/local_storage.cpp#L285-L301
- RowGroupCollection::CommitDropTable: https://github.com/duckdb/duckdb/blob/83ae79e5b7a60820d3fe163e8c60de300fd0c8d1/src/storage/table/row_group_collection.cpp#L1778-L1783

### Full Name:

Peter Michael Elias

### Affiliation:

https://www.probably.dev

### Did you include all relevant configuration (e.g., CPU architecture, Linux distribution) to reproduce the issue?

- [x] Yes, I have

### Did you include all code required to reproduce the issue?

- [x] Yes, I have

### Did you include all relevant data sets for reproducing the issue?

Yes

## Comments

**szarnyasg:**
Hi @txbm, thanks for the report. I can indeed reproduce this on v1.3.0, but newer versions (e.g. v1.4.3 LTS, v1.5.0-dev) no longer reproduce the issue. Can you try updating to either of these?

```
pip install duckdb --upgrade # v1.4 LTS
pip install duckdb --pre --upgrade # v1.5-dev latest dev version
```

**txbm:**
Okay seems that is our best option. We ship a desktop application with DuckDB embedded within so it will require testing but hopefully that will go smoothly. Since presumably this bug was discovered and fixed are you able to point me to any record of its nature? I was unable to find anything when searching issues. Thank you for responding.

**szarnyasg:**
Not entirely sure. Because `ON CONFLICT` uses the index, it's quite possible that one of the pull requests targeting the ART (Adaptive Radix Tree) indexing that fixed it: https://github.com/duckdb/duckdb/pulls?q=is%3Apr+is%3Amerged+art+

**txbm:**
Haha ok, thank you very much. We'll get started on testing 1.4.0. Appreciate the help.

Also I have not rigorously verified this but at a glance I would not be surprised if [this PR](https://github.com/duckdb/duckdb/pull/20160) is specifically relevant here, just in case anyone else comes along and is curious.
