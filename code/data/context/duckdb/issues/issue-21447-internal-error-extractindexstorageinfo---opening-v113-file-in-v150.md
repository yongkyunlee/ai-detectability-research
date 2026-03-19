# INTERNAL Error: ExtractIndexStorageInfo - Opening v1.1.3 file in v1.5.0

**Issue #21447** | State: open | Created: 2026-03-18 | Updated: 2026-03-18
**Author:** jimmycann
**Labels:** under review

### What happens?

I have encountered an issue when opening a database from DuckDB v1.1.3 in v1.5.0. When attempting to open the file in v1.5.0, the engine fails during the initial attachment/metadata load

Stack Trace
```
duckdb150 .db/broken.duckdb
INTERNAL Error:
ExtractIndexStorageInfo: index storage info with name 'idx_weekly_pricing_siteId_weekStartDate' not found
This error signals an assertion failure within DuckDB. This usually occurs due to unexpected conditions or errors in the program's logic.
For more information, see https://duckdb.org/docs/stable/dev/internal_errors

Stack Trace:

0        duckdb::Exception::Exception(duckdb::ExceptionType, std::__1::basic_string, std::__1::allocator> const&) + 52
1        duckdb::InternalException::InternalException(std::__1::basic_string, std::__1::allocator> const&) + 20
2        duckdb::InternalException::InternalException, std::__1::allocator>&>(std::__1::basic_string, std::__1::allocator> const&, std::__1::basic_string, std::__1::allocator>&) + 48
3        duckdb::DataTableInfo::ExtractIndexStorageInfo(std::__1::basic_string, std::__1::allocator> const&) + 472
4        duckdb::CheckpointReader::ReadIndex(duckdb::CatalogTransaction, duckdb::Deserializer&) + 636
5        duckdb::CheckpointReader::ReadEntry(duckdb::CatalogTransaction, duckdb::Deserializer&) + 520
6        duckdb::CheckpointReader::LoadCheckpoint(duckdb::CatalogTransaction, duckdb::MetadataReader&) + 296
7        duckdb::SingleFileCheckpointReader::LoadFromStorage() + 340
8        duckdb::SingleFileStorageManager::LoadDatabase(duckdb::QueryContext) + 2036
9        duckdb::StorageManager::Initialize(duckdb::QueryContext) + 120
10       duckdb::DatabaseManager::AttachDatabase(duckdb::ClientContext&, duckdb::AttachInfo&, duckdb::AttachOptions&) + 1524
11       duckdb::DatabaseInstance::CreateMainDatabase() + 348
12       duckdb::DatabaseInstance::Initialize(char const*, duckdb::DBConfig*) + 1520
13       duckdb::DuckDB::DuckDB(char const*, duckdb::DBConfig*) + 56
14       duckdb_shell::ShellState::OpenDB(duckdb_shell::ShellOpenFlags) + 292
15       main + 2276
16       start + 6076
```

This works fine in both v1.1.3 and v1.4.4 for the same file

```
duckdb .db/broken.duckdb
DuckDB v1.4.4 (Andium) 6ddac802ff
...
```
```
 duckdb113 .db/broken.duckdb
v1.1.3 19864453f7
...
```

This may prove to be a problem in the future as we try to open older duckdb files that are in persistent remote storage after migrating to v1.5.0

### To Reproduce

I am unable to provide a duckdb file that contains the issue, the file opened may contain sensitive information.

Making a modification to the database such as deleting an index, or updating/deleting a row fixes the issue and is subsequently able to be opened in v1.5.0, so I am unable to scrub the file

I performed a hex diff of the Master Block (offset 0x2000) between a "broken" file and a version "healed" by performing a write in v1.1.3.

The diff shows that in the broken state, the IndexStorageInfo map pointers are uninitialized (0xFF), whereas in the healed state, they point to valid block IDs.

Broken State (Offset 0x2010):
```
ff ff ff ff ff ff ff ff  ff ff ff ff ff ff ff ff
```

Healed State (Offset 0x2010):
```
18 00 00 00 00 00 00 06  18 00 00 00 00 00 00 0c
```

### OS:

MacOS ARM

### DuckDB Version:

1.5.0

### DuckDB Client:

CLI

### Hardware:

_No response_

### Full Name:

Jimmy Cann

### Affiliation:

N/A

### Did you include all relevant configuration (e.g., CPU architecture, Linux distribution) to reproduce the issue?

- [x] Yes, I have

### Did you include all code required to reproduce the issue?

- [x] Yes, I have

### Did you include all relevant data sets for reproducing the issue?

No - Other reason (please specify in the issue body)

## Comments

**noel-ooh:**
I'm the OP's colleague. 

Here are some additional details that might help:

* The broken duckdb file was created by a golang project using `marcboeker/go-duckdb v1.8.5`, which embeds `DuckDB v1.1.3`.
* I found the following old bugs that seem to be related and already fixed:
  - #14909
   - #15924
   - #15964

The creation of the duckdb file involved something like:

```sql
CREATE TABLE test (
	id VARCHAR,
	date DATE,
	value DECIMAL(8,4),
	
);
CREATE UNIQUE INDEX idx_id_date ON test (id, date);
INSERT INTO test
SELECT *
FROM read_json_auto(?);
ATTACH '%s' as test_database;
COPY FROM DATABASE memory TO test_database;
DETACH test_database;
CHECKPOINT;
```

My understanding from the above bug fixes is that `COPY FROM` doesn't work well with unique indexes. The bugs were from old versions of duckdb.  DuckDB v1.4.4 CLI tolerates it but DuckDB v1.5.0 asserts it.

So, I think we can do two things: 

1. Update our project to newer `duckdb` library versions. Then, new duckdb files should be fine moving forward.
2. Remove the `COPY FROM DATABASE`. Reviewing our project, I think we can work around it.
