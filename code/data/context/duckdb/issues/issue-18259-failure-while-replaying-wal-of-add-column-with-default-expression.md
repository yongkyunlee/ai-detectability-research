# Failure while replaying WAL of add column with default expression

**Issue #18259** | State: open | Created: 2025-07-15 | Updated: 2026-03-03
**Author:** baolinhuang
**Labels:** under review

### What happens?

duckdb failed to replay wal of  add column with default expression

duckdb cannot restart

### To Reproduce

```
$./duckdb db.duck
D create table t(id int); alter table t add c timestamp default now(); insert into t(id) values(1); select * from t;

$ps -elf | grep db.duck | grep -v grep | awk '{print "kill -9 " $4}' | sh -x 

$./duckdb db.duck
Error: unable to open database "db.duck": Binder Error: Failure while replaying WAL file "db.duck.wal": Catalog "db" does not exist!

```
$./duckdb db.duck
DuckDB v1.3.2 (Ossivalis) 0b83e5d2f6
Enter ".help" for usage hints.
D create table t(id int); alter table t add c timestamp default now(); insert into t(id) values(1); select * from t;

### OS:

linux

### DuckDB Version:

1.3.2

### DuckDB Client:

C++

### Hardware:

_No response_

### Full Name:

BaolinHuang

### Affiliation:

Alibaba Cloud

### What is the latest build you tested with? If possible, we recommend testing with the latest nightly build.

I have not tested with any build

### Did you include all relevant data sets for reproducing the issue?

No - Other reason (please specify in the issue body)

### Did you include all code required to reproduce the issue?

- [x] Yes, I have

### Did you include all relevant configuration (e.g., CPU architecture, Python version, Linux distribution) to reproduce the issue?

- [x] Yes, I have

## Comments

**stephen-etnz:**
We appear to be seeing the same behavior with the C API (v1.3.0). Have worked around by using the `CHECKPOINT` statement after we have initialized the tables.

https://duckdb.org/docs/stable/sql/statements/checkpoint.html

**Captain32:**
A few days ago, v1.4.0 was released. I can still reproduce this bug on the new version. I wrote a test case:

```cpp
TEST_CASE("Test6", "[zxz_test]") {
	std::remove("/flash1/xizhe.zxz/replay_fail");
	std::remove("/flash1/xizhe.zxz/replay_fail.wal");
	DuckDB* db = new DuckDB("/flash1/xizhe.zxz/replay_fail");
	Connection con1(*db);	
	con1.Query("create table t(id int);");
	con1.Query("alter table t add c timestamp default now();");
	delete db;

	Printer::Print("Press any key to continue");
	getchar();

	db = new DuckDB("/flash1/xizhe.zxz/replay_fail"); // Will fail when replaying WAL

	delete db;
}
```

After debugging, I found there are two problems.

### Problem 1

When running the above test case, you will encounter the following error:

```
/flash1/xizhe.zxz/duckdb/test/zxz_test/my_test.cpp:175: FAILED:
due to unexpected exception with message:
  {"exception_type":"INTERNAL","exception_message":"Failure while replaying WAL
  file \"/flash1/xizhe.zxz/replay_fail.wal\": Calling DatabaseManager::
  GetDefaultDatabase with no default database set","stack_trace_pointers":
  "..."}
```

This is because when Bind `now()`, `DatabaseManager::GetDefaultDatabase` will be called. However, the default catalog is not set in `context.client_data->catalog_search_path`. Also, because startup has not yet completed, the `DatabaseManager` has not set a `default_database`. This causes the function to throw an Exception.

```cpp
const string &DatabaseManager::GetDefaultDatabase(ClientContext &context) {
	auto &config = ClientData::Get(context);
	auto &default_entry = config.catalog_search_path->GetDefault(); // not set
	if (IsInvalidCatalog(default_entry.catalog)) {
		auto &result = DatabaseManager::Get(context).default_database; // not set
		if (result.empty()) {
			throw InternalException("Calling DatabaseManager::GetDefaultDatabase with no default database set");
		}
		return result;
	}
	return default_entry.catalog;
}
```

I solved this problem by setting the Default Catalog when constructing `ClientContext` before replaying WAL log:

```cpp
diff --git a/src/storage/wal_replay.cpp b/src/storage/wal_replay.cpp
index 77eca9cf79..5bd5b1ed9a 100644
--- a/src/storage/wal_replay.cpp
+++ b/src/storage/wal_replay.cpp
@@ -16,6 +16,7 @@
 #include "duckdb/execution/index/index_type_set.hpp"
 #include "duckdb/main/attached_database.hpp"
 #include "duckdb/main/client_context.hpp"
+#include "duckdb/main/client_data.hpp"
 #include "duckdb/main/config.hpp"
 #include "duckdb/main/connection.hpp"
 #include "duckdb/main/database.hpp"
@@ -274,6 +275,8 @@ unique_ptr WriteAheadLog::Replay(FileSystem &fs, AttachedDatabase
 }
 unique_ptr WriteAheadLog::ReplayInternal(AttachedDatabase &database, unique_ptr handle) {
        Connection con(database.GetDatabase());
+       CatalogSearchEntry search_entry(database.GetName(), DEFAULT_SCHEMA);
+       ClientData::Get(*con.context).catalog_search_path->Set(search_entry, CatalogSetPathType::SET_DIRECTLY);
        auto wal_path = handle->GetPath();
        BufferedFileReader reader(FileSystem::Get(database), std::move(handle));
        if (reader.Finished()) {
```

### Problem 2

After fixing problem 1, re-running the above test case will result in a new error:

```
/flash1/xizhe.zxz/duckdb/test/zxz_test/my_test.cpp:175: FAILED:
due to unexpected exception with message:
  {"exception_type":"Catalog","exception_message":"Failure while replaying WAL
  file \"/flash1/xizhe.zxz/replay_fail.wal\": Scalar Function with name \"now\"
  is not in the catalog, but it exists in the core_functions extension.\n\
  nPlease try installing and loading the core_functions extension by running:\
  nINSTALL core_functions;\nLOAD core_functions;\n\nAlternatively, consider
  enabling auto-install and auto-load by running:\nSET
  autoinstall_known_extensions=1;\nSET autoload_known_extensions=1;"}
```

Although the error message says that it can be solved by setting `autoinstall_known_extensions=1; SET autoload_known_extensions=1;`, it does not actually work. This is because the `core_functions` extension is not an external extension.

After debugging, I found that in the current implementation, `core_functions` is loaded after the WAL log is replayed:

```cpp
DuckDB::DuckDB(const char *path, DBConfig *new_config) : instance(make_shared_ptr()) {
	instance->Initialize(path, new_config); // replay WAL
	if (instance->config.options.load_extensions) {
		ExtensionHelper::LoadAllExtensions(*this); // load `core_functions`
	}
	instance->db_manager->FinalizeStartup();
}
```

So, I moved the loading of `core_functions` before replaying the WAL log, which solved the problem:

```cpp
diff --git a/src/include/duckdb/main/database.hpp b/src/include/duckdb/main/database.hpp
index 11936d5f74..a005119530 100644
--- a/src/include/duckdb/main/database.hpp
+++ b/src/include/duckdb/main/database.hpp
@@ -33,6 +33,7 @@ class DatabaseFileSystem;
 struct DatabaseCacheEntry;
 class LogManager;
 class ExternalFileCache;
+class DuckDB;
 
 class DatabaseInstance : public enable_shared_from_this {
        friend class DuckDB;
@@ -75,7 +76,7 @@ public:
                                                            AttachOptions &options);
 
 private:
-       void Initialize(const char *path, DBConfig *config);
+       void Initialize(const char *path, DBConfig *config, DuckDB &db);
        void LoadExtensionSettings();
        void CreateMainDatabase();
 
diff --git a/src/main/database.cpp b/src/main/database.cpp
index 419d3304ba..fad2e99433 100644
--- a/src/main/database.cpp
+++ b/src/main/database.cpp
@@ -266,7 +266,7 @@ static duckdb_ext_api_v1 CreateAPIv1Wrapper() {
        return CreateAPIv1();
 }
 
-void DatabaseInstance::Initialize(const char *database_path, DBConfig *user_config) {
+void DatabaseInstance::Initialize(const char *database_path, DBConfig *user_config, DuckDB &db) {
        DBConfig default_config;
        DBConfig *config_ptr = &default_config;
        if (user_config) {
@@ -318,6 +318,10 @@ void DatabaseInstance::Initialize(const char *database_path, DBConfig *user_conf
 
        LoadExtensionSettings();
 
+       if (config.options.load_extensions) {
+               ExtensionHelper::LoadAllExtensions(db);
+       }
+
        if (!db_manager->HasDefaultDatabase()) {
                CreateMainDatabase();
        }
@@ -328,10 +332,7 @@ void DatabaseInstance::Initialize(const char *database_path, DBConfig *user_conf
 }
 
 DuckDB::DuckDB(const char *path, DBConfig *new_config) : instance(make_shared_ptr()) {
-       instance->Initialize(path, new_config);
-       if (instance->config.options.load_extensions) {
-               ExtensionHelper::LoadAllExtensions(*this);
-       }
+       instance->Initialize(path, new_config, *this);
        instance->db_manager->FinalizeStartup();
 }
```

After these two fixes, running the test case again will succeed:

```
[1/1] (100%): Test6
===============================================================================
test cases: 1 | 1 passed
assertions: - none -
```

**meghdip-fenrir:**
> We appear to be seeing the same behavior with the C API (v1.3.0). Have worked around by using the `CHECKPOINT` statement after we have initialized the tables.
> 
> https://duckdb.org/docs/stable/sql/statements/checkpoint.html

Adding checkpoint statement gives this error:
`TransactionContext Error: Cannot CHECKPOINT: the current transaction has transaction local changes`
I am using duckdb node api for running the sql statements like this:
```
    await conn.run(`
      ALTER TABLE evals ADD COLUMN user_id UUID
     `);

    await conn.run(`
      CREATE INDEX IF NOT EXISTS idx_evals_user_id 
      ON evals(user_id)
    `);

    // Checkpoint to force WAL to disk
    await conn.run(`CHECKPOINT;`);
```

@stephen-etnz how did you exactly do it?

**txbm:**
Single-file Python repro (DuckDB 1.3.0):

```python
#!/usr/bin/env python3

import os
import signal
import subprocess
import sys
import time
from pathlib import Path

SQL = """
CREATE TABLE t (id INTEGER);
ALTER TABLE t ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP;

INSERT INTO t VALUES (1, NULL);
SELECT * FROM t;
"""

RUN_DIR = Path("/tmp/duckdb-wal-repro-run")
DB_PATH = RUN_DIR / "wal_repro.duckdb"
WAL_PATH = RUN_DIR / "wal_repro.duckdb.wal"

def _run_child() -> None:
    import duckdb

    db = duckdb.connect(str(DB_PATH))
    for stmt in SQL.split(";"):
        stmt = stmt.strip()
        if stmt:
            db.execute(stmt)
    while True:
        time.sleep(1)

def _wait_for_wal(timeout_s: float) -> bool:
    start = time.time()
    while time.time() - start  0:
            return True
        time.sleep(0.05)
    return False

def _run_parent() -> None:
    RUN_DIR.mkdir(parents=True, exist_ok=True)
    for path in (DB_PATH, WAL_PATH):
        if path.exists():
            path.unlink()

    proc = subprocess.Popen([sys.executable, __file__, "child"])

    if not _wait_for_wal(5.0):
        os.kill(proc.pid, signal.SIGKILL)
        proc.wait(timeout=5)
        raise SystemExit("wal file not found; repro did not start")

    os.kill(proc.pid, signal.SIGKILL)
    proc.wait(timeout=5)

    import duckdb

    try:
        db = duckdb.connect(str(DB_PATH))
        db.execute("SELECT 1")
        raise SystemExit("unexpected: reopen succeeded")
    except Exception as exc:
        msg = str(exc)
        if "Failure while replaying WAL" not in msg:
            raise SystemExit(f"unexpected error: {msg}") from exc
        print("repro confirmed: WAL replay failure")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "child":
        _run_child()
    else:
        _run_parent()
```
