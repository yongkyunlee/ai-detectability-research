# Show HN: Stratum – SQL that branches and beats DuckDB on 35/46 1T benchmarks

**HN** | Points: 12 | Comments: 3 | Date: 2026-03-12
**Author:** whilo
**HN URL:** https://news.ycombinator.com/item?id=47357141
**Link:** https://datahike.io/notes/stratum-analytics-engine/

## Top Comments

**whilo:**
Hi HN - I’m the author of Stratum.The headline benchmark result is that on 10M rows, Stratum is faster than DuckDB on 35 of 46 single-threaded analytical queries, despite running entirely on the JVM.But the main idea is actually branchable tables: you can fork a table in O(1), keep copy-on-write snapshots, and query different branches through SQL.It speaks the PostgreSQL wire protocol, so psql&#x2F;JDBC&#x2F;DBeaver work out of the box.Benchmarks, methodology, and repo are linked from the page. Happy to answer questions.

**iFire:**
https:&#x2F;&#x2F;github.com&#x2F;replikativ&#x2F;stratum is apache2.0 license FOSS!> Stratum is a columnar analytics engine that combines the performance of fused SIMD execution with the semantics of immutable dataWhat are your thoughts for investing in a columnar based database rather than a hybrid one?I'm in the game development space.
