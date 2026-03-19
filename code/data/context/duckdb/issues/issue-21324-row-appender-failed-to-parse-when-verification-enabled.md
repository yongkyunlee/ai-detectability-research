# Row appender failed to parse when verification enabled

**Issue #21324** | State: open | Created: 2026-03-12 | Updated: 2026-03-12
**Author:** dentiny
**Labels:** under review

### What happens?

Hi team, I was generating some random sql for my extension, and I met some unexpected issues on appender when verification enabled.

### To Reproduce

```cpp
TEST_CASE("Test append", "[appender]") {
	DuckDB db(nullptr);
	Connection conn(db);
	conn.EnableQueryVerification(); // disable verification seems to work without problem

	auto result = conn.Query("CREATE TABLE test_table (col_smallint SMALLINT, col_int INTEGER, col_bigint BIGINT)");
	if (result->HasError()) {
		cerr GetError() HasError()) {
		cerr GetError() Print();	
}
```

The error message I get is
```sh
[Thread 0xfff8e900c500 (LWP 97036) exited]
due to unexpected exception with message:
  {"exception_type":"Parser","exception_message":"Failed to append: syntax
  error at or near \"-\"","error_subtype":"SYNTAX_ERROR","position":"93"}
```

I tried to use gdb to get some basic stacktrace
```sh
(gdb) bt
#0  0x0000fffff7ca99a0 in __cxa_throw () from /lib/aarch64-linux-gnu/libstdc++.so.6
#1  0x0000aaaaad0b47f4 [PAC] in duckdb_libpgquery::ereport (code=)
    at /home/vscode/duckdb/third_party/libpg_query/pg_functions.cpp:125
#2  0x0000aaaaad0b6df0 in duckdb_libpgquery::base_yyerror (base_yylloc=0xffffffff9b7c, 
    yyscanner=0xaaaaad89e1a8, msg=0xaaaaab2b0178 "syntax error")
    at third_party/libpg_query/grammar/grammar.cpp:9
#3  duckdb_libpgquery::base_yyparse (yyscanner=yyscanner@entry=0xaaaaad89e1a8)
    at third_party/libpg_query/grammar/grammar_out.cpp:33018
#4  0x0000aaaaad0b547c in duckdb_libpgquery::raw_parser (str=)
    at /home/vscode/duckdb/third_party/libpg_query/src_backend_parser_parser.cpp:60
#5  0x0000aaaaad0b4638 in duckdb_libpgquery::pg_parser_parse (query=, res=0xffffffffd398)
    at /home/vscode/duckdb/third_party/libpg_query/pg_functions.cpp:104
#6  0x0000aaaaad0b40b8 in duckdb::PostgresParser::Parse (this=this@entry=0xffffffffd5b0, 
    query="WITH __duckdb_internal_appended_data AS NOT MATERIALIZED (SELECT * FROM ColumnDataCollection ---Type  for more, q to quit, c to continue without paging--c
 [1 Chunks, 1 Rows]\nChunk 0 - [Rows 0 - 1]\nChunk - [3 Columns]\n- FLAT SMALLINT: 1 = [ -22983]\n- FLAT INTEG"...) at /home/vscode/duckdb/third_party/libpg_query/postgres_parser.cpp:15
#7  0x0000aaaaac0f5b1c in duckdb::Parser::ParseQuery (this=this@entry=0xffffffffd800, 
    query="WITH __duckdb_internal_appended_data AS NOT MATERIALIZED (SELECT * FROM ColumnDataCollection - [1 Chunks, 1 Rows]\nChunk 0 - [Rows 0 - 1]\nChunk - [3 Columns]\n- FLAT SMALLINT: 1 = [ -22983]\n- FLAT INTEG"...) at /home/vscode/duckdb/src/parser/parser.cpp:310
#8  0x0000aaaaace459d4 in duckdb::ClientContext::PendingStatementOrPreparedStatementInternal (
    this=this@entry=0xaaaaad75fa90, lock=..., 
    query="INSERT INTO main.test_table FROM __duckdb_internal_appended_data", statement=..., 
    prepared=..., parameters=...) at /home/vscode/duckdb/src/main/client_context.cpp:926
#9  0x0000aaaaace463b0 in duckdb::ClientContext::PendingQueryInternal (this=this@entry=0xaaaaad75fa90, 
    lock=..., statement=..., parameters=..., verify=verify@entry=true)
    at /usr/include/c++/14/bits/unique_ptr.h:191
#10 0x0000aaaaace48ea4 in duckdb::ClientContext::PendingQuery (this=this@entry=0xaaaaad75fa90, 
    statement=..., values=std::unordered_map with 0 elements, parameters=...)
    at /usr/include/c++/14/bits/unique_ptr.h:191
#11 0x0000aaaaace49018 in duckdb::ClientContext::PendingQuery (this=this@entry=0xaaaaad75fa90, 
    statement=..., parameters=...) at /home/vscode/duckdb/src/main/client_context.cpp:1102
#12 0x0000aaaaace49144 in duckdb::ClientContext::Query (this=this@entry=0xaaaaad75fa90, statement=..., 
    parameters=..., parameters@entry=...) at /usr/include/c++/14/bits/unique_ptr.h:191
#13 0x0000aaaaace49434 in duckdb::ClientContext::Append (this=this@entry=0xaaaaad75fa90, stmt=...)
    at /home/vscode/duckdb/src/include/duckdb/main/query_parameters.hpp:22
#14 0x0000aaaaace496c4 in duckdb::Appender::FlushInternal (this=, collection=...)
    at /usr/include/c++/14/bits/unique_ptr.h:191
#15 0x0000aaaaacdf4bcc in duckdb::BaseAppender::Flush (this=0xffffffffdf18)
    at /home/vscode/duckdb/src/main/appender.cpp:415
#16 duckdb::BaseAppender::Flush (this=0xffffffffdf18) at /home/vscode/duckdb/src/main/appender.cpp:404
#17 0x0000aaaaab650e08 in ____C_A_T_C_H____T_E_S_T____50 ()
    at /home/vscode/duckdb/test/appender/test_appender.cpp:921
```
As you could tell from the gdb printout, the parser takes an unexpected string, which could explain the parsing error.
```sql
WITH __duckdb_internal_appended_data AS NOT MATERIALIZED (SELECT * FROM ColumnDataCollection - [1 Chunks, 1 Rows]
Chunk 0 - [Rows 0 - 1]
Chunk - [3 Columns]
- FLAT SMALLINT: 1 = [ -22983]
- FLAT INTEGER: 1 = [ -500]
- FLAT BIGINT: 1 = [ -10000]
 AS __duckdb_internal_appended_data)INSERT INTO main.test_table SELECT * FROM __duckdb_internal_appended_data
```

### OS:

ubuntu

### DuckDB Version:

88277463aa86b998f241a0cd0f87ea647e749576

### DuckDB Client:

C++

### Hardware:

_No response_

### Full Name:

dentiny

### Affiliation:

N/A

### Did you include all relevant configuration (e.g., CPU architecture, Linux distribution) to reproduce the issue?

- [x] Yes, I have

### Did you include all code required to reproduce the issue?

- [x] Yes, I have

### Did you include all relevant data sets for reproducing the issue?

Yes

## Comments

**Mytherin:**
Thanks for reporting - this is caused by `ColumnDataRef::ToString` not emitting a round-trippable representation of the data. In order to fix it this should emit a `VALUES` clause. This is mostly a debug / dev issue.
