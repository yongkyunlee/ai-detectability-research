# [Julia][Parquet] DuckDB blocks parquet file after reading

**Issue #18304** | State: open | Created: 2025-07-18 | Updated: 2026-03-12
**Author:** jhmenke
**Labels:** under review

### What happens?

After reading a parquet file, the file itself is blocked. It cannot be deleted oder overwritten. This happens regardless of copying to a table, closing the DuckDB connection and even using explicit garbage collection. 

Versions:
> [[deps.DuckDB]]
> deps = ["DBInterface", "Dates", "DuckDB_jll", "FixedPointDecimals", "Tables", "UUIDs", "WeakRefStrings"]
> git-tree-sha1 = "fac32a1e4c9e49886e41d82d9ad17fa5cf4161af"
> uuid = "d2f5444f-75bc-4fdf-ac35-56f514c445e1"
> version = "1.3.2"
> 
> [[deps.DuckDB_jll]]
> deps = ["Artifacts", "JLLWrappers", "Libdl"]
> git-tree-sha1 = "0e60dd625d6c4183b6256bd1614a1993f3581166"
> uuid = "2cbbab25-fc8b-58cf-88d4-687a02676033"
> version = "1.3.2+0"

I'd also be very happy if there would be a feasible workaround. Copying the file and reading the copy does work, but then the copied file is blocked for quite some time too.

### To Reproduce

```
using Revise
using DataFrames, DuckDB

f = "data.parquet"
if !isfile("data.parquet.backup")
    cp(f, "data.parquet.backup")
end

# ERROR: Execute of query "COPY df_temp TO 'data.parquet' (FORMAT 'parquet')" failed: IO Error: Failed to delete file "data.parquet":
con = DBInterface.connect(DuckDB.DB, ":memory:")
table = DBInterface.execute(con, "SELECT * FROM read_parquet('$f')")
df = DataFrame(table)
DuckDB.register_data_frame(con, df, "df_temp")
DBInterface.execute(con, "COPY df_temp TO '$(f)' (FORMAT 'parquet')")

# ERROR: DuckDB.QueryException("Execute of query \"COPY table_name TO 'data.parquet' (FORMAT 'parquet')\" failed: Invalid Input Error: Attempting to execute an unsuccessful or closed pending query result\nError: IO Error: Failed to delete file \"data.parquet\"
con = DBInterface.connect(DuckDB.DB, ":memory:")
table = DBInterface.execute(con, "CREATE TABLE table_name AS SELECT * FROM read_parquet('$f')")
DBInterface.execute(con, "COPY table_name TO '$(f)' (FORMAT 'parquet')")
DBInterface.close!(con)

# ERROR: DuckDB.QueryException("Execute of query \"COPY df_temp TO 'data.parquet' (FORMAT 'parquet')\" failed: IO Error: Failed to delete file \"data.parquet\": 
con = DBInterface.connect(DuckDB.DB, ":memory:")
table = DBInterface.execute(con, "SELECT * FROM read_parquet('$f')")
df = DataFrame(table)
DBInterface.close!(con)
con = DBInterface.connect(DuckDB.DB, ":memory:")
DuckDB.register_data_frame(con, df, "df_temp")
DBInterface.execute(con, "COPY df_temp TO '$(f)' (FORMAT 'parquet')")
DBInterface.close!(con)

# ERROR: DuckDB.QueryException("Execute of query \"COPY df_temp TO 'data.parquet' (FORMAT 'parquet')\" failed: IO Error: Failed to delete file \"data.parquet\":
con = DBInterface.connect(DuckDB.DB, ":memory:")
table = DBInterface.execute(con, "SELECT * FROM read_parquet('$f')")
df = DataFrame(table)
DBInterface.close!(con)
con = nothing
GC.gc()
con = DBInterface.connect(DuckDB.DB, ":memory:")
DuckDB.register_data_frame(con, df, "df_temp")
DBInterface.execute(con, "COPY df_temp TO '$(f)' (FORMAT 'parquet')")
DBInterface.close!(con)
```

data.parquet file for reproducing the issue: [data.zip](https://github.com/user-attachments/files/21313796/data.zip)

### OS:

Windows 10 (x86_64)

### DuckDB Version:

1.3.2

### DuckDB Client:

1.3.2

### Hardware:

_No response_

### Full Name:

Jan-Hendrik Menke

### Affiliation:

Amprion GmbH

### What is the latest build you tested with? If possible, we recommend testing with the latest nightly build.

I have tested with a stable release

### Did you include all relevant data sets for reproducing the issue?

Yes

### Did you include all code required to reproduce the issue?

- [x] Yes, I have

### Did you include all relevant configuration (e.g., CPU architecture, Python version, Linux distribution) to reproduce the issue?

- [x] Yes, I have

## Comments

**jhmenke:**
I should add that in the DuckDB command line, this simple code _does work_:

```
duckdb
DuckDB v1.3.2 (Ossivalis) 0b83e5d2f6
Enter ".help" for usage hints.
Connected to a transient in-memory database.
Use ".open FILENAME" to reopen on a persistent database.
D CREATE TABLE table_name AS SELECT * FROM read_parquet('data.parquet');
D COPY table_name TO 'data.parquet' (FORMAT 'parquet');
D
```

**jhmenke:**
So with the current DuckDB.jl version (1.4.1?), at least this seems to work reliably:

```
con = DBInterface.connect(DuckDB.DB, ":memory:")
table = DBInterface.execute(con, "SELECT * FROM read_parquet('$f')")
df = DataFrame(table)
DBInterface.close!(con)
con = DBInterface.connect(DuckDB.DB, ":memory:")
DuckDB.register_data_frame(con, df, "df_temp")
DBInterface.execute(con, "COPY df_temp TO '$(f)' (FORMAT 'parquet')")
DBInterface.close!(con)
```

They key seems to be that one needs to close the connection that read the parquet file and then open up a separate connection for (over)writing.
