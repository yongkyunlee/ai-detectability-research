# `COPY FROM DATABASE x TO y` fails with `key ... does not exist in the referenced table`

**Issue #16785** | State: open | Created: 2025-03-22 | Updated: 2026-03-12
**Author:** bubnov
**Labels:** reproduced

### What happens?

I tried to reclaim space using approach described here: [Compacting a Database by Copying](https://duckdb.org/docs/stable/operations_manual/footprint_of_duckdb/reclaiming_space.html#compacting-a-database-by-copying).

The copying fails with the error:

```
» ATTACH 'reclaim_space_demo.db' AS old;
» ATTACH 'reclaim_space_demo_copy.db' AS new;
» COPY FROM DATABASE old TO new;
Constraint Error:
Violates foreign key constraint because key "id: 1" does not exist in the referenced table
```

Am I doing something wrong or this is a bug?

The same error occurs when I try to do the same using `duckdb-rs` crate (v1.2.1).

### To Reproduce

1. **Create tables and fill them with some data**:

```bash
duckdb reclaim_space_demo.db
```

```sql
CREATE SEQUENCE IF NOT EXISTS id_sequence START 1;

CREATE TABLE IF NOT EXISTS nodes (
   id    VARCHAR PRIMARY KEY,
   name  VARCHAR NOT NULL
);

CREATE TABLE IF NOT EXISTS nodes_watchlist (
   node_id   VARCHAR UNIQUE NOT NULL,
   FOREIGN KEY (node_id) REFERENCES nodes(id)
);

CREATE TABLE IF NOT EXISTS datasources (
   id    INTEGER PRIMARY KEY DEFAULT nextval('id_sequence'),
   name  VARCHAR NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS datasources_nodes (
   datasource_id   INTEGER NOT NULL,
   node_id         VARCHAR NOT NULL,
   last_sync_date  TIMESTAMP_MS,
   FOREIGN KEY (datasource_id) REFERENCES datasources(id),
   FOREIGN KEY (node_id) REFERENCES nodes(id),
   UNIQUE (datasource_id, node_id)
);

CREATE TABLE IF NOT EXISTS data (
   datasource_id   INTEGER NOT NULL,
   created         TIMESTAMP_MS NOT NULL,
   value           DOUBLE NOT NULL,
   FOREIGN KEY (datasource_id) REFERENCES datasources(id),
   UNIQUE (datasource_id, created)
);

CREATE VIEW IF NOT EXISTS v_nodes_info AS
WITH
   cte_last_sync_dates AS (
      SELECT
         n.id,
         dsn.last_sync_date
      FROM nodes n
      JOIN datasources_nodes dsn ON dsn.node_id = n.id
      GROUP BY ALL
   )
SELECT
   n.*,
   nw.node_id IS NOT NULL AS watched,
   lsd.last_sync_date
FROM nodes n
LEFT JOIN nodes_watchlist nw ON nw.node_id = n.id
LEFT JOIN cte_last_sync_dates lsd ON lsd.id = n.id
ORDER BY n.id;

INSERT INTO datasources (name) VALUES ('a'), ('b'), ('c'); 
INSERT INTO nodes (id, name) VALUES ('node_1', 'Node 1'), ('node_2', 'Node 2'), ('node_3', 'Node 3');
INSERT INTO nodes_watchlist (node_id) VALUES ('node_1');
INSERT INTO datasources_nodes (datasource_id, node_id) VALUES (1, 'node_1');
INSERT INTO data (datasource_id, created, value) 
VALUES 
   (1, '2025-01-01 00:00:00', 0.0),
   (1, '2025-01-02 00:00:00', 1.0),
   (1, '2025-01-03 00:00:00', 2.0),
   (1, '2025-01-04 00:00:00', 3.0),
   (1, '2025-01-05 00:00:00', 4.0),
   (1, '2025-01-06 00:00:00', 5.0),
   (1, '2025-01-07 00:00:00', 6.0),
   (1, '2025-01-08 00:00:00', 7.0),
   (1, '2025-01-09 00:00:00', 8.0);
```

2. **Now try to reclaim space by copying**:

```
% duckdb                      
-- Loading resources from /Users/slavik/.duckdbrc
v1.2.1 8e52ec4395
Enter ".help" for usage hints.
Connected to a transient in-memory database.
Use ".open FILENAME" to reopen on a persistent database.
```
```
ATTACH 'reclaim_space_demo.db' AS old;
ATTACH 'reclaim_space_demo_copy.db' AS new;
COPY FROM DATABASE old TO new;
```
```
Constraint Error:
Violates foreign key constraint because key "id: node_1" does not exist in the referenced table
```

### OS:

macos

### DuckDB Version:

v1.2.1

### DuckDB Client:

cli, duckdb_rs

### Hardware:

_No response_

### Full Name:

Slavik Bubnov

### Affiliation:

Self employed

### What is the latest build you tested with? If possible, we recommend testing with the latest nightly build.

I have tested with a stable release

### Did you include all relevant data sets for reproducing the issue?

Yes

### Did you include all code required to reproduce the issue?

- [x] Yes, I have

### Did you include all relevant configuration (e.g., CPU architecture, Python version, Linux distribution) to reproduce the issue?

- [ ] Yes, I have

## Comments

**liznear:**
I thought adding a `ReorderTableEntries` at https://github.com/duckdb/duckdb/blob/43c5f3489858c0377d4a6e6d6e7ed8d0502ba1df/src/planner/binder/statement/bind_copy_database.cpp#L54 is enough. I tried and the SQL here did work. However, I think I miss something since this change could not fix [copy_database_fk.test](https://github.com/duckdb/duckdb/blob/43c5f3489858c0377d4a6e6d6e7ed8d0502ba1df/test/sql/copy_database/copy_database_fk.test#L11).

**its-felix:**
As a workaround, temporarily setting the threads to `1` to perform the copy seems to work for me:
```golang
queries := []string{
			`SET threads TO 1`,
			`COPY FROM DATABASE src_db TO dst_db`,
			`SET threads TO 6`,
}
```

**bubnov:**
Unfortunately, the workaround doesn't work for me. I still get the same error.

**its-felix:**
I updated my schema and now the workaround with setting the threads to `1` doesn't work anymore, unless I remove one of my foreign key constraints.

In my case, this is a foreign key constraint referencing the same table and this is reproducible with a single table:
```sql
ATTACH 'copy_src.db' AS copy_src ;
ATTACH 'copy_dst.db' AS copy_dst ;
USE copy_src ;
```

```sql
CREATE TABLE example (
  id INT NOT NULL,
  parent_id INT,
  PRIMARY KEY (id),
  FOREIGN KEY (parent_id) REFERENCES example (id)
) ;

INSERT INTO example 
(id, parent_id)
VALUES
(1, NULL),
(2, NULL);

INSERT INTO example
(id, parent_id)
VALUES
(10, 1),
(20, 2);
```

```sql
USE memory ;
SET threads TO 1 ;
COPY FROM DATABASE copy_src TO copy_dst ;
-- > Constraint Error:
-- Violates foreign key constraint because key "id: 1" does not exist in the referenced table
```

**its-felix:**
Reproduced in DuckDB v1.3.0 (Ossivalis) 71c5c07cdd

**its-felix:**
@bubnov I found a hacky workaround, in case you're interested.

You can export the database as parquet, then attach a new (empty) DB file and import the database from parquet:

Example:

### Create source Database
```sql
ATTACH 'copy_src.db' AS copy_src ;
USE copy_src ;

CREATE TABLE example (
  id INT NOT NULL,
  parent_id INT,
  PRIMARY KEY (id),
  FOREIGN KEY (parent_id) REFERENCES example (id)
) ;

INSERT INTO example 
(id, parent_id)
VALUES
(1, NULL),
(2, NULL);

INSERT INTO example
(id, parent_id)
VALUES
(10, 1),
(20, 2);
```

### Export and Import
```sql
EXPORT DATABASE 'dummyexport' (
  FORMAT parquet,
  COMPRESSION gzip
);

ATTACH 'copy_dst.db' AS copy_dst ;
USE copy_dst ;

IMPORT DATABASE 'dummyexport' ;
```

**bubnov:**
Thanks for the suggestion, @its-felix! The issue is no longer blocking me since I switched to a different database, as DuckDB wasn't the best fit for my product. The main problem I faced was frequent out-of-memory errors.

I'm confident the repo maintainers will address this properly in time, so these kinds of workarounds won't be necessary.

**its-felix:**
Reproduced in DuckDB v1.3.1 (Ossivalis) 2063dda3e6

**its-felix:**
Reproduced in DuckDB v1.4.2 (Andium) 68d7555f68

**its-felix:**
Possibly related to https://github.com/duckdb/duckdb/issues/7168
