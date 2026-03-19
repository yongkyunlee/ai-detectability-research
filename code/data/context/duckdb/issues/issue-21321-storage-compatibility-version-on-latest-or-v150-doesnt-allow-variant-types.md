# storage_compatibility_version on 'latest' or 'v1.5.0' doesn't allow variant types

**Issue #21321** | State: closed | Created: 2026-03-11 | Updated: 2026-03-13
**Author:** BigRedAye
**Labels:** needs triage, Needs Documentation, expected behavior

### What happens?

Setting the storage_compatibility_version to 'latest' or 'v1.5.0' doesn't allow tables with variant types to be created. And the setting doesn't stick across sessions.

I can't believe this is a bug - but I can't find any issues with my approach...

### To Reproduce

```shell
rm -f /scratch/duckdb_work.db
duckdb /scratch/duckdb_work.db
```

```sql
--  DuckDB v1.5.0 (Variegata)
--  Enter ".help" for usage hints.

SET storage_compatibility_version = 'latest'; --also tried 'v1.5.0'
SELECT current_setting('storage_compatibility_version');
-- ┌──────────────────────────────────────────────────┐
-- │ current_setting('storage_compatibility_version') │
-- │                     varchar                      │
-- ├──────────────────────────────────────────────────┤
-- │ latest                                           │
-- └──────────────────────────────────────────────────┘

CREATE TABLE events (id INTEGER, data VARIANT);
-- Invalid Input Error:
-- VARIANT columns are not supported in storage versions prior to v1.5.0 (database "duckdb_work" is using storage version v1.0.0+)
```
And it doesn't take???

```shell
duckdb /scratch/duckdb_work.db
```

```sql
-- DuckDB v1.5.0 (Variegata)
-- Enter ".help" for usage hints.
SELECT current_setting('storage_compatibility_version');
-- ┌──────────────────────────────────────────────────┐
-- │ current_setting('storage_compatibility_version') │
-- │                     varchar                      │
-- ├──────────────────────────────────────────────────┤
-- │ v0.10.2                                          │
-- └──────────────────────────────────────────────────┘

-- I think it is the right setting because it won't take arbitrary versions.
SET storage_compatibility_version = 'goose';
-- Invalid Input Error:
-- The version string 'goose' is not a known DuckDB version, valid options are: v0.10.0, v0.10.1, v0.10.2, v0.10.3, v1.0.0, v1.1.0, v1.1.1, v1.1.2, v1.1.3, v1.2.0, v1.2.1, v1.2.2, v1.3.0, v1.3.1, v1.3.2, v1.4.0, v1.4.1, v1.4.2, v1.4.3, v1.4.4, 
```

### OS:

Ubuntu 2024 x86, Windows 11 x86

### DuckDB Version:

v1.5.0

### DuckDB Client:

cli (same in python)

### Hardware:

_No response_

### Full Name:

Jonathan Trumbull

### Affiliation:

AbbVie

### Did you include all relevant configuration (e.g., CPU architecture, Linux distribution) to reproduce the issue?

- [x] Yes, I have

### Did you include all code required to reproduce the issue?

- [x] Yes, I have

### Did you include all relevant data sets for reproducing the issue?

Not applicable - the reproduction does not require a data set

## Comments

**szarnyasg:**
Hi @BigRedAye, thanks for flagging this. This is a _documentation issue_ and I'll amend the docs but let me explain the issue here first.

Once you create a database, its storage version is fixed. So

```sql
SET storage_compatibility_version = 'latest';
```

only sets the compatibility of the session but does not affect the database. The way you can create a database that can store `VARIANT`s is:

```bash
# launch in-memory duckdb
duckdb
```
```sql
ATTACH '/scratch/duckdb_work.db' AS duckdb_work (STORAGE_VERSION 'v1.5.0');
USE duckdb_work;
CREATE TABLE events (id INTEGER, data VARIANT);
```

This works just fine.

**BigRedAye:**
Awesome, I know I was missing something!

**szarnyasg:**
No problem. There's an even more succinct syntax:

```bash
duckdb --storage-version 'v1.5.0' /scratch/duckdb_work.db
```
