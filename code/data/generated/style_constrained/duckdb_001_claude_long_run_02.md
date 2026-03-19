# Getting Started with DuckDB's Python Client

DuckDB is fast. That simple fact is what pulled me toward it when our team needed to crunch analytical queries against multi-gigabyte Parquet files without spinning up cloud infrastructure. The Python client makes it absurdly easy to get going-one `pip install` and you're running SQL against DataFrames, CSVs, and Parquet files in the same breath. But there are sharp edges you should know about before you commit to it for anything beyond throwaway scripts.

## Installation and First Connection

Getting DuckDB into your Python environment is a one-liner. Run `pip install duckdb --upgrade` to grab the latest stable release, which at the time of writing is part of the v1.4 LTS line. If you want to try the bleeding edge-v1.5.0 (codenamed "Variegata," released 2026-03-09)-you can install pre-release wheels with `python3 -m pip install "duckdb>=1.5.0.dev"`.

Once installed, connecting takes two lines:


import duckdb
conn = duckdb.connect()


That gives you an in-memory database. Pass a filename to `duckdb.connect("my_data.db")` if you want persistence. The connection object is your primary interface-you can call `conn.cursor()` to get a PEP 249 cursor, but the DuckDB example code itself describes the cursor as "fully redundant." I'd skip it and work directly with the connection.

## Running SQL and Fetching Results

The SQL API follows a pattern that'll feel natural if you've used `sqlite3`. You call `conn.execute()` with a query string and optionally bind parameters:


conn.execute("CREATE TABLE sensors (id INTEGER, reading DOUBLE, label STRING)")
conn.execute("INSERT INTO sensors VALUES (?, ?, ?)", [1, 23.5, 'temperature'])
conn.executemany("INSERT INTO sensors VALUES (?, ?, ?)", [
    [2, 45.1, 'humidity'],
    [3, 99.8, 'pressure']
])


Parameterized queries work exactly as you'd expect. Where DuckDB really shines is in how many ways it can hand results back to you. Calling `.fetchall()` returns plain Python tuples. But you probably don't want tuples. You want a DataFrame:


df = conn.execute("SELECT * FROM sensors").fetchdf()


That's it-one method call, and you've got a pandas DataFrame. There's also `.fetchnumpy()`, which returns masked NumPy arrays instead. The masked arrays handle NULLs more cleanly than pandas' default behavior, so they're worth considering if you're doing numerical work on columns with missing values.

## Querying DataFrames and Files Directly

This is the feature that hooked our team. DuckDB can query pandas DataFrames without importing them into a table first:


import pandas as pd
orders = pd.DataFrame({"product_id": [1, 2, 3], "quantity": [10, 20, 5]})
conn.register("orders", orders)
result = conn.execute("SELECT * FROM orders WHERE quantity > 8").fetchdf()


You register the DataFrame with a name and then reference it in SQL. And DuckDB's file reading is just as seamless-you can point SQL directly at files on disk:


SELECT * FROM 'transactions.csv';
SELECT * FROM 'warehouse.parquet';


Glob patterns work too. If you've got a directory of CSVs following a naming convention, `SELECT * FROM 'tsa20*.csv'` reads them all. For files with slightly different schemas, the `union_by_name` option reconciles columns across files. We stopped writing throwaway pandas scripts for ad-hoc data exploration after discovering this.

## The Relation API: Lazy and Chainable

Beyond raw SQL, DuckDB's Python client offers a Relation API that operates lazily. Nothing executes until you ask for results. You build up a query pipeline by chaining method calls:


rel = conn.from_df(orders)
result = rel.filter('quantity > 5').project('product_id, quantity').order('quantity').limit(10)
result.df()  # triggers execution, returns DataFrame


Each call-`.filter()`, `.project()`, `.order()`, `.limit()`-returns a new relation. You can also aggregate with `.aggregate("sum(quantity)")`, join relations with `.join(other_rel, 'product_id')`, and even run SQL against a relation using `.query('alias', 'SELECT * FROM alias WHERE ...')`. The shorthand `duckdb.df(my_dataframe)` creates a relation using the default connection, so you don't even need an explicit connection object for quick one-offs.

Relation objects expose useful metadata through `.columns`, `.types`, and `.alias` properties. And you can materialize results back into tables with `.create("new_table")` or `.insert_into("existing_table")`.

The Relation API is simpler than writing raw SQL for some transformations, but SQL gives you the full power of DuckDB's dialect-window functions, CTEs, correlated subqueries, and complex types like arrays, structs, and maps. For anything non-trivial, I'd stick with SQL and use the Relation API for quick DataFrame transformations.

## Performance: What the Numbers Say

A community benchmark comparing DuckDB against BigQuery and Athena on roughly 20GB of ZSTD-compressed Parquet data (57 queries, financial time-series) paints a clear picture. DuckDB running locally on an 8-thread machine with 16GB RAM hit a warm median query time of 881 milliseconds. The same workload on BigQuery clocked in at 2,775 ms and Athena at 4,211 ms. Scaling up to a 32-thread, 64GB machine dropped DuckDB's median to 284 ms.

So DuckDB on local storage runs 3-10x faster than managed cloud platforms for this class of query. That's the vectorized execution engine doing its job-processing data in batches that fit neatly in CPU caches.

But there's a caveat with remote storage. When reading from S3 or Cloudflare R2, cold start overhead jumps to 14-20 seconds because DuckDB needs to fetch file metadata over the network. Warm queries on remote storage are still fast-496 ms on the 32-thread machine with R2-but that first hit is painful. You can tune memory and thread usage with configuration settings like `SET memory_limit = '2GiB'` and `SET threads = 1`, which is helpful for constraining DuckDB in shared environments.

## Sharp Edges You'll Hit

DuckDB is excellent, but it has real limitations you need to understand before relying on it.

**Database file bloat** is the biggest one. If you're doing frequent updates or deletes on tables with UNIQUE or PRIMARY KEY constraints, the database file will grow without bound. `VACUUM` and `CHECKPOINT` don't reclaim space in this scenario. The root cause is that DuckDB's ART indexes-automatically created for unique/primary key columns-store row IDs that can't be rewritten during cleanup. One user reported a table with 1,500 rows growing to 1.2 GB in 24 hours with a UNIQUE constraint. The same table without the constraint stayed at 2.3 MB. The data itself was only 400 KB when exported as Parquet.

The workaround is to periodically compact your database by copying it to a fresh file:


with duckdb.connect(":memory:") as conn:
    conn.execute(f"ATTACH '{source_path}' AS source (READ_ONLY)")
    conn.execute(f"ATTACH '{compact_path}' AS target")
    conn.execute("COPY FROM DATABASE source TO target")


This reduced one user's database from 1.26 GB to 256 MB-an 80% reduction-in under 5 seconds.

**Concurrency is limited.** DuckDB follows a single-writer model. Multiple readers work fine, but concurrent writes to the same records can cause problems with DuckDB's MVCC implementation. An older bug in pre-1.4.3 versions could even cause a segfault (`Fatal Python error: Segmentation fault` inside `RowGroupCollection::~RowGroupCollection()`) when two threads using cursors from the same connection ran concurrent `INSERT ... ON CONFLICT DO UPDATE` statements. That specific bug is fixed, but the architectural constraint remains: DuckDB isn't built for high-concurrency write workloads.

**CSV type inference can surprise you.** The default `read_csv()` samples 20,480 rows to infer column types and quoting behavior. If the first quoted field appears beyond that sample window, you'll get a parse error: `CSV Error on Line: 20502 ... Expected Number of Columns: 2 Found: 3`. The fix is to pass `quote='"'` explicitly or set `sample_size=-1` to scan the entire file. Other tools like pandas and Polars handle this correctly by default, so it's an easy gotcha to run into.

## Configuring DuckDB for Your Workload

DuckDB exposes a handful of runtime settings worth knowing about:


SET memory_limit = '16GB';
SET threads = 8;
SET temp_directory = '/path/to/tmp.tmp';
SET preserve_insertion_order = false;


Disabling `preserve_insertion_order` can speed up bulk loads because DuckDB doesn't need to maintain row ordering during parallel inserts. If you're working with S3, v1.5.0 switched the default HTTP backend from httplib to curl, which you can also set explicitly with `SET httpfs_client_implementation = 'curl'`.

## The Ecosystem Around It

DuckDB doesn't exist in isolation. There's a Jupyter kernel, a dbt adapter, a Metabase driver maintained by MotherDuck, and MotherDuck itself if you want cloud-hosted DuckDB. The extension system adds capabilities like full-text search (`fts`), spatial queries (`spatial`), vector similarity search (`vss`), and connectors for Postgres, MySQL, and SQLite through scanner extensions. Community extensions like Flock even bring LLM operators into DuckDB SQL.

For a tool that ships as a 16 MB binary on desktop (and 2 MB in its WASM build), the reach is broad.

## Who Should Use This

DuckDB's Python client is the right tool if you're doing single-node, read-heavy analytical work-validating data, running ad-hoc queries against Parquet/CSV files, or embedding analytics into a Python application. It's dramatically simpler than setting up Spark or paying for BigQuery when your data fits on one machine.

But don't try to build a multi-user application with concurrent writes on top of it. DuckDB's single-writer architecture and file bloat behavior under update-heavy workloads mean you'll want a proper OLTP database for that. The trade-off is straightforward: DuckDB is simpler to set up and faster for analytics, but Postgres gives you the concurrency model and write durability that production transactional systems demand.

Start with `pip install duckdb`, point it at a Parquet file, and run a query. You'll understand the appeal in about thirty seconds.
