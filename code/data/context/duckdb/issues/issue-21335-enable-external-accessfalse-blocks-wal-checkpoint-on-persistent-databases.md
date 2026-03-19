# `enable_external_access=false` blocks WAL checkpoint on persistent databases

**Issue #21335** | State: closed | Created: 2026-03-12 | Updated: 2026-03-15
**Author:** NoaZetterman-Skovik
**Labels:** reproduced

### What happens?

When opening a persistent database with `enable_external_access=false`, checkpoint operations fail with a permission error.

#### The error
```
FATAL Error: Failed to create checkpoint because of error: Permission Error: Cannot access file "/tmp/access_mode.duckdb.wal.checkpoint" - file system operations are disabled by configuration
```

#### Potential Solution
Modifying this code: https://github.com/duckdb/duckdb/blob/55b94c48018e1571ae6c513769bf49cd00b63bd4/src/main/database.cpp#L445-L451
to:
```c
	if (database_path && !Settings::Get(*this)) {
		config.AddAllowedPath(database_path);
		config.AddAllowedPath(database_path + string(".wal"));
		config.AddAllowedPath(database_path + string(".wal.checkpoint"));
		if (!config.options.temporary_directory.empty()) {
			config.AddAllowedDirectory(config.options.temporary_directory);
		}
	}
```
fixes the issue locally for me when testing it against latest master. But I'm unsure if this is the correct solution or a workaround to get it to work, since it worked in older versions of DuckDB. Perhaps adding `.wal.recovery` is also something that must be considered, but it is not directly relevant to the error.

### To Reproduce

```c
#include "duckdb.h"
#include 
#include 

int main(void) {
    duckdb_database db;
    duckdb_connection con;
    duckdb_config config;

    // First, create the database file
    duckdb_create_config(&config);
    char *err = NULL;
    if (duckdb_open_ext("/tmp/db.duckdb", &db, config, &err) == DuckDBError) {
        fprintf(stderr, "Create error: %s\n", err);
        duckdb_free(err);
        duckdb_destroy_config(&config);
        return 1;
    }
    duckdb_destroy_config(&config);
    duckdb_close(&db);

    // Now reopen with enable_external_access=false
    duckdb_create_config(&config);
    duckdb_set_config(config, "enable_external_access", "false");

    err = NULL;
    if (duckdb_open_ext("/tmp/db.duckdb", &db, config, &err) == DuckDBError) {
        fprintf(stderr, "Open error: %s\n", err);
        duckdb_free(err);
        duckdb_destroy_config(&config);
        return 1;
    }
    duckdb_destroy_config(&config);
    duckdb_connect(db, &con);

    duckdb_result res;
    duckdb_state state = duckdb_query(con, "CREATE TABLE t1 (i INTEGER)", &res);
    printf("CREATE TABLE: %s\n", state == DuckDBError ? duckdb_result_error(&res) : "OK");
    duckdb_destroy_result(&res);

    state = duckdb_query(con, "CHECKPOINT", &res);
    printf("CHECKPOINT: %s\n", state == DuckDBError ? duckdb_result_error(&res) : "OK");
    duckdb_destroy_result(&res);

    duckdb_disconnect(&con);
    duckdb_close(&db);
    remove("/tmp/db.duckdb");
    remove("/tmp/db.duckdb.wal");
    return 0;
}
```
Output:

```
CREATE TABLE: OK
CHECKPOINT: FATAL Error: Failed to create checkpoint because of error: Permission Error: Cannot access file "/tmp/access_mode.duckdb.wal.checkpoint" -
```

### OS:

macOS 15.7.4

### DuckDB Version:

1.5.0

### DuckDB Client:

C

### Hardware:

_No response_

### Full Name:

Noa Zetterman

### Affiliation:

Skovik

### Did you include all relevant configuration (e.g., CPU architecture, Linux distribution) to reproduce the issue?

- [x] Yes, I have

### Did you include all code required to reproduce the issue?

- [x] Yes, I have

### Did you include all relevant data sets for reproducing the issue?

Yes

## Comments

**Mytherin:**
Thanks for the report! Your suggested fix is correct - I've pushed it in https://github.com/duckdb/duckdb/pull/21379
