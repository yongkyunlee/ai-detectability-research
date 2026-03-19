# Transactions not working as expected with DELETE/TRUNCATE

**Issue #13819** | State: open | Created: 2024-09-09 | Updated: 2026-03-06
**Author:** gordonhart
**Labels:** reproduced, stale

### What happens?

Unable to delete from multiple tables with foreign key constraints in a transaction.

Expected behavior: changes are committed on `commit()` or can be rolled back as desired

Actual behavior: foreign key constraint failure

### To Reproduce

```py
import duckdb

conn = duckdb.connect()
conn.sql("CREATE TABLE a (id INTEGER PRIMARY KEY)")
conn.sql("CREATE TABLE b (a_id INTEGER NOT NULL, FOREIGN KEY (a_id) REFERENCES a (id))")
conn.sql("INSERT INTO a (id) VALUES (1), (2), (3)")
conn.sql("INSERT INTO b (a_id) VALUES (1), (2), (3)")
conn.begin()
conn.sql("TRUNCATE b")
conn.sql("TRUNCATE a")  # 
    conn.sql("TRUNCATE a")
duckdb.duckdb.ConstraintException: Constraint Error: Violates foreign key constraint because key "a_id: 1" is still referenced by a foreign key in a different table
```

Verified that this happens on 0.10.3 as well as 1.0.0.

### OS:

MacOS Sonoma 14.1

### DuckDB Version:

0.10.3

### DuckDB Client:

Python

### Hardware:

_No response_

### Full Name:

Gordon Hart

### Affiliation:

Kolena

### What is the latest build you tested with? If possible, we recommend testing with the latest nightly build.

I have tested with a stable release

### Did you include all relevant data sets for reproducing the issue?

Yes

### Did you include all code required to reproduce the issue?

- [X] Yes, I have

### Did you include all relevant configuration (e.g., CPU architecture, Python version, Linux distribution) to reproduce the issue?

- [X] Yes, I have

## Comments

**gordonhart:**
Looks like this might be covered under the [Over-Eager Unique Constraint Checking](https://duckdb.org/docs/sql/indexes#over-eager-unique-constraint-checking) known limitation in the documentation about indexes. Particularly this seems that it would also apply to deletions followed by deletions:

> As a result of this – transactions that perform deletions followed by insertions may trigger unexpected unique constraint violations, as the deleted tuple has not actually been removed from the index yet.

Would still appreciate a second look from somebody more familiar with DuckDB.

Love the project btw — way more joy than pain has come from using DuckDB so far.

**gordonhart:**
Reading a bit more on this, I'm pretty sure that the "fix" here is to include a similar warning when performing double deletes to the warning shown to the user when trying to update e.g. [`LIST` types](https://duckdb.org/docs/sql/data_types/list.html) which runs into the same issue as it is internally an insert and delete operation:

```
Constraint Error: Duplicate key "id: 1" violates primary key constraint.
If this is an unexpected constraint violation please double check with the known index limitations section in our documentation (https://duckdb.org/docs/sql/indexes).
```

Perhaps also the "known limitations" section linked above should be updated to also reference double deletes.

If a maintainer agrees on this solution, I can work on getting it up as a PR.

**rkennedy-argus:**
No idea if it's the same problem, but I just ran into something similar:

```
D create table numbers (num int primary key);
D insert into numbers (num) values (1);
D begin transaction;
D truncate numbers;
D select * from numbers;
┌────────┐
│  num   │
│ int32  │
├────────┤
│ 0 rows │
└────────┘
D insert into numbers (num) values (1);
Constraint Error: Duplicate key "num: 1" violates primary key constraint. If this is an unexpected constraint violation please double check with the known index limitations section in our documentation (https://duckdb.org/docs/sql/indexes).
```

I'm attempting to re-populate the table within a transaction (so if anything fails I can roll back to the previous table data). Unfortunately, this doesn't work because the index doesn't appear to be updated until the transaction is committed.

**github-actions[bot]:**
This issue is stale because it has been open 90 days with no activity. Remove stale label or comment or this will be closed in 30 days.

**curio77:**
I guess this hasn't gone anywhere?  Asking because I've just encountered related issues with current DuckDB v1.3.2.

**Cerebrado:**
This has been open for more than one year... and it is basic for database operations. We cannot delete children records and then parent records in a transaction... and since this is is not supporting cascade delete, we are supposed to live with the danger that the dabase could be in an inconsistent state.
I'm moving out of here and use sqlite.
