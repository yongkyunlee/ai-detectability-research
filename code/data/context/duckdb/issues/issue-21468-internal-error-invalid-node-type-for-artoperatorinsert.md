# INTERNAL Error: Invalid node type for ARTOperator::Insert

**Issue #21468** | State: open | Created: 2026-03-18 | Updated: 2026-03-18
**Author:** andyreimann
**Labels:** needs triage

### What happens?

Got this error after I added an index to my table:
```
[Flush] TRANSACTION FAILED for 23 filings: INTERNAL Error: Invalid node type for ARTOperator::Insert.
Stack Trace:
/usr/src/app/node_modules/@duckdb/node-bindings-linux-x64/libduckdb.so(_ZN6duckdb9Exception6ToJSONENS_13ExceptionTypeERKNSt7__cxx1112basic_stringIcSt11char_traitsIcESaIcEEE+0x5b) [0x7f7885d9824b]
/usr/src/app/node_modules/@duckdb/node-bindings-linux-x64/libduckdb.so(_ZN6duckdb9ExceptionC2ENS_13ExceptionTypeERKNSt7__cxx1112basic_stringIcSt11char_traitsIcESaIcEEE+0x14) [0x7f7885d98304]
/usr/src/app/node_modules/@duckdb/node-bindings-linux-x64/libduckdb.so(_ZN6duckdb17InternalExceptionC1ERKNSt7__cxx1112basic_stringIcSt11char_traitsIcESaIcEEE+0x11) [0x7f7885d9b371]
/usr/src/app/node_modules/@duckdb/node-bindings-linux-x64/libduckdb.so(+0xa6dfd0) [0x7f7884fecfd0]
/usr/src/app/node_modules/@duckdb/node-bindings-linux-x64/libduckdb.so(+0x1b8f3f5) [0x7f788610e3f5]
/usr/src/app/node_modules/@duckdb/node-bindings-linux-x64/libduckdb.so(_ZN6duckdb3ART10InsertKeysERNS_14ArenaAllocatorERNS_6vectorINS_6ARTKeyELb0ESaIS4_EEES7_mRKNS_15DeleteIndexInfoENS_15IndexAppendModeENS_12optional_ptrINS_9DataChunkELb1EEE+0x88) [0x7f7886111588]
/usr/src/app/node_modules/@duckdb/node-bindings-linux-x64/libduckdb.so(_ZN6duckdb3ART6InsertERNS_9IndexLockERNS_9DataChunkERNS_6VectorERNS_15IndexAppendInfoE+0x1a8) [0x7f7886113348]
/usr/src/app/node_modules/@duckdb/node-bindings-linux-x64/libduckdb.so(_ZN6duckdb3ART6AppendERNS_9IndexLockERNS_9DataChunkERNS_6VectorERNS_15IndexAppendInfoE+0x7b) [0x7f78860fb75b]
/usr/src/app/node_modules/@duckdb/node-bindings-linux-x64/libduckdb.so(_ZN6duckdb10BoundIndex6AppendERNS_9DataChunkERNS_6VectorERNS_15IndexAppendInfoE+0xb5) [0x7f7886122a35]
/usr/src/app/node_modules/@duckdb/node-bindings-linux-x64/libduckdb.so(_ZN6duckdb9DataTable15AppendToIndexesERNS_14TableIndexListENS_12optional_ptrIS1_Lb1EEERNS_9DataChunkES6_RKNS_6vectorINS_12StorageIndexELb1ESaIS8_EEElNS_15IndexAppendModeENS_12optional_idxE+0x255) [0x7f78864670c5]
/usr/src/app/node_modules/@duckdb/node-bindings-linux-x64/libduckdb.so(_ZN6duckdb17LocalTableStorage15AppendToIndexesERNS_15DuckTransactionERNS_18RowGroupCollectionERNS_14TableIndexListERKNS_6vectorINS_11LogicalTypeELb1ESaIS8_EEERl+0x6b2) [0x7f7886487b92]
/usr/src/app/node_modules/@duckdb/node-bindings-linux-x64/libduckdb.so(_ZN6duckdb17LocalTableStorage15AppendToIndexesERNS_15DuckTransactionERNS_16TableAppendStateE+0x10d) [0x7f788648817d]
/usr/src/app/node_modules/@duckdb/node-bindings-linux-x64/libduckdb.so(_ZN6duckdb12LocalStorage5FlushERNS_9DataTableERNS_17LocalTableStorageENS_12optional_ptrINS_18StorageCommitStateELb1EEE+0xbe) [0x7f78864883ae]
/usr/src/app/node_modules/@duckdb/node-bindings-linux-x64/libduckdb.so(_ZN6duckdb12LocalStorage6CommitENS_12optional_ptrINS_18StorageCommitStateELb1EEE+0x69) [0x7f78864884e9]
/usr/src/app/node_modules/@duckdb/node-bindings-linux-x64/libduckdb.so(_ZN6duckdb15DuckTransaction10WriteToWALERNS_13ClientContextERNS_16AttachedDatabaseERNS_10unique_ptrINS_18StorageCommitStateESt14default_deleteIS6_ELb1EEE+0xfb) [0x7f78864ad42b]
/usr/src/app/node_modules/@duckdb/node-bindings-linux-x64/libduckdb.so(_ZN6duckdb22DuckTransactionManager17CommitTransactionERNS_13ClientContextERNS_11TransactionE+0xa2d) [0x7f78864ae0fd]
/usr/src/app/node_modules/@duckdb/node-bindings-linux-x64/libduckdb.so(_ZN6duckdb15MetaTransaction6CommitEv+0xe5) [0x7f78864a9bc5]
/usr/src/app/node_modules/@duckdb/node-bindings-linux-x64/libduckdb.so(_ZN6duckdb18TransactionContext6CommitEv+0x4d) [0x7f78864aa02d]
/usr/src/app/node_modules/@duckdb/node-bindings-linux-x64/libduckdb.so(_ZNK6duckdb19PhysicalTransaction15GetDataInternalERNS_16ExecutionContextERNS_9DataChunkERNS_19OperatorSourceInputE+0x241) [0x7f788602ad21]
/usr/src/app/node_modules/@duckdb/node-bindings-linux-x64/libduckdb.so(_ZN6duckdb16PipelineExecutor15FetchFromSourceERNS_9DataChunkE+0x7d) [0x7f78862a20dd]
/usr/src/app/node_modules/@duckdb/node-bindings-linux-x64/libduckdb.so(_ZN6duckdb16PipelineExecutor7ExecuteEm+0xda) [0x7f78862ab10a]
/usr/src/app/node_modules/@duckdb/node-bindings-linux-x64/libduckdb.so(_ZN6duckdb12PipelineTask11ExecuteTaskENS_17TaskExecutionModeE+0xd2) [0x7f78862ab462]
/usr/src/app/node_modules/@duckdb/node-bindings-linux-x64/libduckdb.so(_ZN6duckdb12ExecutorTask7ExecuteENS_17TaskExecutionModeE+0xd6) [0x7f78862a3426]
/usr/src/app/node_modules/@duckdb/node-bindings-linux-x64/libduckdb.so(_ZN6duckdb13TaskScheduler14ExecuteForeverEPSt6atomicIbE+0x126) [0x7f78862accb6]
/lib/x86_64-linux-gnu/libstdc++.so.6(+0xd44a3) [0x7f78c0bce4a3]
/lib/x86_64-linux-gnu/libc.so.6(+0x891f5) [0x7f78c089a1f5]
/lib/x86_64-linux-gnu/libc.so.6(__clone+0x40) [0x7f78c0919b40]
This error signals an assertion failure within DuckDB. This usually occurs due to unexpected conditions or errors in the program's logic.
```

The table schema:
```
    await connection.run("CREATE TABLE IF NOT EXISTS filings (" +
        "cik INTEGER, " +
        "type VARCHAR, " +
        "accessionNumber VARCHAR, " +
        "url VARCHAR, " +
        "date_filed TIMESTAMP, " +
        "period_end_date TIMESTAMP, " +
        "xbrl BOOLEAN, " +
        "attempts INTEGER DEFAULT 0, " + // number of processing attempts (give up after 5)
        "documents VARCHAR[], " + // ordered list of slide/exhibit filenames from index.json
        "amendment BOOLEAN, " + // true if form ends with "/A"
        "title VARCHAR, " + // descriptive title from primaryDocDescription (filtered)
        "items VARCHAR[], " + // 8-K item codes (e.g. ['2.02', '9.01']), null for non-8-K
        "completed_processors VARCHAR[], " + // processor names that ran successfully
        "processed_at TIMESTAMP, " + // when last successfully processed
        "last_error VARCHAR, " + // last error message (truncated)
        "PRIMARY KEY (cik, accessionNumber)" +
        ");");
```

The indexes I added:
```
    await connection.run(`CREATE INDEX IF NOT EXISTS idx_filings_cik_date ON filings (cik, date_filed);`);
    await connection.run(`CREATE INDEX IF NOT EXISTS idx_filings_date ON filings (date_filed);`);
```

Adding these indexes was already painful and only worked on my windows machine using @duckdb/node-api 1.5.0-r.1.
With the @duckdb/node-api 1.3.2-alpha.24 version I was using before, I wasn't even able to add that index and instead I got this error:
```
Creating idx_facts_cik on facts(cik)...
  Done in 9.0s

Creating idx_filings_cik_date on filings(cik, date_filed)...
  Done in 2.6s

Creating idx_filings_date on filings(date_filed)...
[Error: INTERNAL Error: node without metadata in ARTOperator::Insert
This error signals an assertion failure within DuckDB. This usually occurs due to unexpected conditions or errors in the program's logic.
For more information, see https://duckdb.org/docs/stable/dev/internal_errors]
```

Trying to add the index on a linux machine just ends with `free(): corrupted unsorted chunks`

### To Reproduce

Create the table and the indices and insert into that table + update existing rows. The inserts and updates are producing this error on a linux machine for me.
The filings table in my case is filled with ~5.6 million entries, so it isn't easily shareable here.

### OS:

Linux x86_64 and NodeJS running inside a node:20-bookworm-slim based docker image

### DuckDB Version:

1.5.0-r.1

### DuckDB Client:

NodeJS

### Hardware:

_No response_

### Full Name:

Andy Reimann

### Affiliation:

personal

### Did you include all relevant configuration (e.g., CPU architecture, Linux distribution) to reproduce the issue?

- [x] Yes, I have

### Did you include all code required to reproduce the issue?

- [x] Yes, I have

### Did you include all relevant data sets for reproducing the issue?

No - I cannot easily share my data sets due to their large size

## Comments

**szarnyasg:**
@andyreimann would it be possible for you to upload the data somewhere? If so, please reach out to gabor@duckdblabs.com and I'll try to arrange something, so we can reproduce and fix this. Thanks!
