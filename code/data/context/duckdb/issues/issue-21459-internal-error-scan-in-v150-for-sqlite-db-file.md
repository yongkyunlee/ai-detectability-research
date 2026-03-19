# INTERNAL Error: Scan in v1.5.0 for sqlite db file

**Issue #21459** | State: open | Created: 2026-03-18 | Updated: 2026-03-18
**Author:** cmdlineluser
**Labels:** reproduced

### What happens?

I passed the wrong filename which happened to be an SQLite database.

1.4.4 raises a regular error:

```
Binder Error:
No extension found that is capable of reading the file "duckdb-crash.db"
```

### To Reproduce

```shell
sqlite3 duckdb-crash.db 'create table tbl as select 1'
```
```shell
duckdb -c 'from "duckdb-crash.db"'   
```

  Stack Trace 

```
INTERNAL Error:
Scan

Stack Trace:

0        _ZN6duckdb9ExceptionC2ENS_13ExceptionTypeERKNSt3__112basic_stringIcNS2_11char_traitsIcEENS2_9allocatorIcEEEE + 52
1        _ZN6duckdb17InternalExceptionC1ERKNSt3__112basic_stringIcNS1_11char_traitsIcEENS1_9allocatorIcEEEE + 20
2        _ZN6duckdb17SQLiteSchemaEntry4ScanENS_11CatalogTypeERKNSt3__18functionIFvRNS_12CatalogEntryEEEE + 68
3        std::__1::__function::__func, void (duckdb::SchemaCatalogEntry&)>::operator()(duckdb::SchemaCatalogEntry&) + 112
4        duckdb::DuckDBReader::DuckDBReader(duckdb::ClientContext&, duckdb::OpenFileInfo, duckdb::DuckDBFileReaderOptions const&) + 376
5        void std::__1::allocator::construct[abi:ne190102](duckdb::DuckDBReader*, duckdb::ClientContext&, duckdb::OpenFileInfo const&, duckdb::DuckDBFileReaderOptions&) + 104
6        duckdb::shared_ptr duckdb::make_shared_ptr(duckdb::ClientContext&, duckdb::OpenFileInfo const&, duckdb::DuckDBFileReaderOptions&) + 112
7        duckdb::DuckDBMultiFileInfo::CreateReader(duckdb::ClientContext&, duckdb::OpenFileInfo const&, duckdb::BaseFileReaderOptions&, duckdb::MultiFileOptions const&) + 40
8        duckdb::MultiFileReader::BindReader(duckdb::ClientContext&, duckdb::vector>&, duckdb::vector, std::__1::allocator>, true, std::__1::allocator, std::__1::allocator>>>&, duckdb::MultiFileList&, duckdb::MultiFileBindData&, duckdb::BaseFileReaderOptions&, duckdb::MultiFileOptions&) + 224
9        duckdb::DuckDBMultiFileInfo::BindReader(duckdb::ClientContext&, duckdb::vector>&, duckdb::vector, std::__1::allocator>, true, std::__1::allocator, std::__1::allocator>>>&, duckdb::MultiFileBindData&) + 132
10       duckdb::MultiFileFunction::MultiFileBindInternal(duckdb::ClientContext&, duckdb::unique_ptr, true>, duckdb::shared_ptr, duckdb::vector>&, duckdb::vector, std::__1::allocator>, true, std::__1::allocator, std::__1::allocator>>>&, duckdb::MultiFileOptions, duckdb::unique_ptr, true>, duckdb::unique_ptr, true>) + 1032
11       duckdb::MultiFileFunction::MultiFileBind(duckdb::ClientContext&, duckdb::TableFunctionBindInput&, duckdb::vector>&, duckdb::vector, std::__1::allocator>, true, std::__1::allocator, std::__1::allocator>>>&) + 820
12       duckdb::Binder::BindTableFunctionInternal(duckdb::TableFunction&, duckdb::TableFunctionRef const&, duckdb::vector>, std::__1::unordered_map, std::__1::allocator>, duckdb::Value, duckdb::CaseInsensitiveStringHashFunction, duckdb::CaseInsensitiveStringEquality, std::__1::allocator, std::__1::allocator> const, duckdb::Value>>>, duckdb::vector>, duckdb::vector, std::__1::allocator>, true, std::__1::allocator, std::__1::allocator>>>) + 948
13       duckdb::Binder::Bind(duckdb::TableFunctionRef&) + 2552
14       duckdb::Binder::Bind(duckdb::TableRef&) + 360
15       duckdb::Binder::BindWithReplacementScan(duckdb::ClientContext&, duckdb::BaseTableRef&) + 1064
16       duckdb::Binder::Bind(duckdb::BaseTableRef&) + 3592
17       duckdb::Binder::Bind(duckdb::TableRef&) + 388
18       duckdb::Binder::BindNode(duckdb::SelectNode&) + 68
19       duckdb::Binder::BindNode(duckdb::QueryNode&) + 524
20       duckdb::Planner::CreatePlan(duckdb::SQLStatement&) + 160
21       duckdb::ClientContext::CreatePreparedStatementInternal(duckdb::ClientContextLock&, std::__1::basic_string, std::__1::allocator> const&, duckdb::unique_ptr, true>, duckdb::PendingQueryParameters) + 544
22       duckdb::ClientContext::CreatePreparedStatement(duckdb::ClientContextLock&, std::__1::basic_string, std::__1::allocator> const&, duckdb::unique_ptr, true>, duckdb::PendingQueryParameters, duckdb::PreparedStatementMode) + 1048
23       duckdb::ClientContext::PendingStatementInternal(duckdb::ClientContextLock&, std::__1::basic_string, std::__1::allocator> const&, duckdb::unique_ptr, true>, duckdb::PendingQueryParameters const&) + 128
24       duckdb::ClientContext::PendingStatementOrPreparedStatement(duckdb::ClientContextLock&, std::__1::basic_string, std::__1::allocator> const&, duckdb::unique_ptr, true>, duckdb::shared_ptr&, duckdb::PendingQueryParameters const&) + 276
25       duckdb::ClientContext::PendingStatementOrPreparedStatementInternal(duckdb::ClientContextLock&, std::__1::basic_string, std::__1::allocator> const&, duckdb::unique_ptr, true>, duckdb::shared_ptr&, duckdb::PendingQueryParameters const&) + 1876
26       duckdb::ClientContext::PendingQueryInternal(duckdb::ClientContextLock&, duckdb::unique_ptr, true>, duckdb::PendingQueryParameters const&, bool) + 132
27       duckdb::ClientContext::PendingQuery(duckdb::unique_ptr, true>, std::__1::unordered_map, std::__1::allocator>, duckdb::BoundParameterData, duckdb::CaseInsensitiveStringHashFunction, duckdb::CaseInsensitiveStringEquality, std::__1::allocator, std::__1::allocator> const, duckdb::BoundParameterData>>>&, duckdb::QueryParameters) + 220
28       duckdb::ClientContext::PendingQuery(duckdb::unique_ptr, true>, duckdb::QueryParameters) + 64
29       duckdb::ClientContext::Query(duckdb::unique_ptr, true>, duckdb::QueryParameters) + 56
30       duckdb::Connection::SendQuery(duckdb::unique_ptr, true>, duckdb::QueryParameters) + 64
31       duckdb_shell::ShellState::ExecuteStatement(duckdb::unique_ptr, true>) + 272
32       duckdb_shell::ShellState::ExecuteSQL(std::__1::basic_string, std::__1::allocator> const&) + 548
33       duckdb_shell::ShellState::RunInitialCommand(char const*, bool) + 416
34       duckdb_shell::MetadataResult duckdb_shell::RunCommand(duckdb_shell::ShellState&, duckdb::vector, std::__1::allocator>, true, std::__1::allocator, std::__1::allocator>>> const&) + 60
35       main + 2520
36       start + 2236

This error signals an assertion failure within DuckDB. This usually occurs due to unexpected conditions or errors in the program's logic.
For more information, see https://duckdb.org/docs/stable/dev/internal_errors
```

### OS:

macOS

### DuckDB Version:

v1.5.0 (Variegata) 3a3967aa81

### DuckDB Client:

CLI or Python

### Hardware:

_No response_

### Full Name:

Karl  Genockey

### Affiliation:

None

### Did you include all relevant configuration (e.g., CPU architecture, Linux distribution) to reproduce the issue?

- [x] Yes, I have

### Did you include all code required to reproduce the issue?

- [x] Yes, I have

### Did you include all relevant data sets for reproducing the issue?

Yes
