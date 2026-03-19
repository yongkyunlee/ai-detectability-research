# Due to UNIQUE or PRIMARY KEY constraint, the size of duckdb database file keeps growing

**Issue #19468** | State: open | Created: 2025-10-22 | Updated: 2026-03-03
**Author:** rayGoMoon
**Labels:** under review

### What happens?

I can confirm that the issue of the **duckdb database file growing unbounded is indeed caused by the ART index.**

I'm currently using a small, but frequently updated and deleted duckdb database. It contains only one table with approximately 1,500 rows.

After running the duckdb database for 24 hours, the duckdb database file grew wildly to **1.2GB**, with the total number of rows remaining virtually unchanged.

Running VACUUM or CHECKPOINT operations did nothing to reduce the database file size.

However, when I exported the database as a Parquet file, the Parquet file size was only **400kb**.

After seeing @p1p1bear mention that this issue was related to ART indexes, I consulted the official DuckDB documentation:

[https://duckdb.org/docs/stable/sql/indexes#adaptive-radix-tree-art](https://duckdb.org/docs/stable/sql/indexes#adaptive-radix-tree-art)

This section states:

> ART indexes ... are automatically created for columns with a UNIQUE or PRIMARY KEY constraint.

So I tried removing the only UNIQUE constraint in the original table.

And just like that, a miracle happened!

After 24 hours of operation, the DuckDB database file size remained at **2.3 MB**.

DuckDB is an excellent project. I am deeply grateful to all its developers and contributors.

Hopefully, DuckDB will resolve this issue in the near future.

I'm sharing my personal experience here in the hope that it will help any developer facing this headache.

### To Reproduce

In the deno runtime, use TypeScript to create a test database based on the @duckdb/node-api client. Create a table in this test database with a UNIQUE constraint. Perform frequent updates to this table, and you'll notice a continuous increase in the size of the DuckDB database file. Furthermore, performing VACUUM or CHECKPOINT operations fails to reclaim the occupied storage space.

### OS:

ubuntu 24.04.3

### DuckDB Version:

1.4.1

### DuckDB Client:

@duckdb/node-api

### Hardware:

_No response_

### Full Name:

Ray

### Affiliation:

Nobody

### Did you include all relevant configuration (e.g., CPU architecture, Linux distribution) to reproduce the issue?

- [x] Yes, I have

### Did you include all code required to reproduce the issue?

- [x] Yes, I have

### Did you include all relevant data sets for reproducing the issue?

Yes

## Comments

**p1p1bear:**
Hi @rayGoMoon 
The current 1.4 version has not solved this problem.

Before cleaning data, DuckDB checks whether all rows in a row group have been emptied. If the row group is empty, it directly releases the underlying block by marking it as modified (MarkBlockAsModified). The block’s state is then updated to "free" during the checkpoint phase, making it available for reuse.

However, there is one prerequisite for block cleanup: the table must not have any ART indexes. This restriction was introduced in commit [8ce6cc79](https://github.com/duckdb/duckdb/commit/8ce6cc7992486ac957faf3bd7c56aafa79d220eb), associated with PR [#7794](https://github.com/duckdb/duckdb/pull/7794), which also explains the reasoning: cleaning up blocks while ART indexes exist would require rewriting the row IDs stored in the index, which is currently not supported. Therefore, DuckDB skip the cleanup process in such cases.

As a result, row IDs are never reused when ART indexes are present. [My testing](https://github.com/duckdb/duckdb/issues/17778#issuecomment-3162240609) confirms this behavior: in tables with ART indexes, the blocks storing table data cannot be reused—only the blocks storing the ART index itself can be reclaimed and reused.

Looking forward to the improvement of Duckdb (I think perhaps introducing a logical row id to avoid ART directly associated with the physical row id may solve this problem)   :)

**rayGoMoon:**
Hi, @p1p1bear. 

Thank you again for your kind reply.

It really helped me solve this headache.

In the long run, an unbounded, rapidly growing DuckDB data file is almost unusable.

I really hope DuckDB resolves this issue soon.

Thank you very much!

**xubobbs:**
see 
https://github.com/duckdb/duckdb/issues/20683   
https://github.com/duckdb/duckdb/pull/18829

**xubobbs:**
void RowGroupCollection::SetAppendRequiresNewRowGroup() {
// requires_new_row_group = true;
// xubo marked
}
when I mark this code,my database work find . because open and rewrite small database file kept quickly is very important.

**andreamoro:**
I experienced this issue and have opened a new report with a concrete reproduction (1.26 GB → 256 MB via `COPY FROM DATABASE` workaround) and a feature request: #21154
