# Getting Started with DuckDB's Python Client

DuckDB is an embedded analytical database. That single sentence undersells it. We've been reaching for pandas and Spark for years whenever someone says "process this CSV" or "aggregate that Parquet dump," and most of the time those tools are either too slow or too heavy for the job. DuckDB sits in a different spot entirely: it's an in-process OLAP engine that runs inside your Python program, requires no server, and handles surprisingly large datasets without breaking a sweat.

The Python client is where most people start. It installs with a single `pip install duckdb`, ships as a self-contained package, and gives you a SQL engine that can query pandas DataFrames, Parquet files on S3, and CSV files with glob patterns - all without standing up infrastructure. Here's what you need to know to get productive with it.

## Installation and First Connection

Installation is trivial. Run `pip install duckdb` and you're done. No compiler toolchain, no system dependencies, no config files. The package bundles everything.

Connecting is equally simple. Call `duckdb.connect()` and you get an in-memory database that lives for the duration of your process. If you want persistence, pass a filename instead:


import duckdb

# In-memory, ephemeral
conn = duckdb.connect()

# Persistent, written to disk
conn = duckdb.connect("my_analytics.duckdb")


That's it. No connection strings, no port numbers, no authentication dance. The database file is a single portable artifact you can move between machines. Version 1.5.0, released on March 9, 2026, is the latest stable release and the one I'd recommend starting with.

You can also pass configuration through the `config` dictionary at connection time for things like thread count and memory limits:


conn = duckdb.connect("analytics.duckdb", config={
    "threads": 8,
    "memory_limit": "16GB"
})


One thing to know: not every option works through the config dictionary yet. The `compress` option for in-memory databases, introduced in v1.4.0, currently only works through the `ATTACH` SQL command rather than `duckdb.connect()`. The DuckDB team has acknowledged this as a limitation they plan to address. So if you want in-memory compression, you'll need the two-step pattern: connect first, then run `ATTACH ':memory:' AS cdb (COMPRESS)` followed by `USE cdb`.

## Running Queries and Fetching Results

The API follows a straightforward execute-then-fetch pattern. You write SQL, execute it, and pull results in whatever format you need.


conn.execute("CREATE TABLE events (id INTEGER, name VARCHAR, ts TIMESTAMP)")
conn.execute("INSERT INTO events VALUES (1, 'signup', '2026-01-15 10:30:00')")
conn.execute("INSERT INTO events VALUES (?, ?, ?)", [2, 'purchase', '2026-01-15 11:00:00'])


Parameterized queries use `?` placeholders. For batch inserts, `executemany()` accepts a list of parameter lists:


conn.executemany("INSERT INTO events VALUES (?, ?, ?)", [
    [3, 'login', '2026-01-15 12:00:00'],
    [4, 'logout', '2026-01-15 13:00:00']
])


Results come back in several shapes. You pick the one that fits your downstream code. `.fetchall()` returns a list of tuples. `.fetchone()` grabs a single row. `.fetchdf()` hands you a pandas DataFrame. And `.fetchnumpy()` gives you masked numpy arrays, which handle NULLs more cleanly than pandas does in some cases. I tend to reach for `.fetchdf()` when exploring data interactively and `.fetchall()` when I need raw values in application code.

## The Pandas Integration That Actually Surprised Me

This is the part that shifts how you think about DuckDB. The Python client can query pandas DataFrames directly, without any explicit registration step. Just reference the variable name in your SQL:


import pandas as pd

df = pd.DataFrame({"user_id": [1, 2, 3], "spend": [50.0, 120.5, 30.0]})
result = conn.execute("SELECT * FROM df WHERE spend > 40").fetchdf()


DuckDB reaches into your local Python scope and treats the DataFrame as a virtual table. This feels like magic the first time you see it. And it's fast - DuckDB's vectorized execution engine processes data in batches optimized for CPU caches, which often outperforms pandas' row-at-a-time operations for analytical queries.

You can also go the explicit route with `conn.register()` if you prefer named views:


conn.register("spending_data", df)
result = conn.execute("SELECT avg(spend) FROM spending_data").fetchdf()
conn.unregister("spending_data")


But there's a gotcha with bulk inserts from DataFrames that bit at least one early user hard enough to file a GitHub issue about it. If you create a table with one column order and then `INSERT INTO ... SELECT * FROM` a DataFrame with a different column order, DuckDB will silently map columns by position, not by name. The fix is straightforward - use `CREATE TABLE ... AS SELECT * FROM df` instead, which preserves column names from the DataFrame. Or if the table already exists, spell out the column names explicitly in both the INSERT and SELECT clauses.

## Reading Files Directly

DuckDB doesn't need you to load data into a table first. You can query CSV, Parquet, and JSON files directly with SQL:


result = conn.execute("SELECT * FROM read_csv_auto('transactions.csv')").fetchdf()
result = conn.execute("SELECT * FROM read_parquet('events/*.parquet')").fetchdf()


That glob pattern support is genuinely useful. You can point DuckDB at a directory of hundreds of Parquet files and query them as if they were a single table. And if those files don't share an identical schema, the `union_by_name` option reconciles them by column name rather than position.

The CSV parser deserves a mention too. It auto-detects types, handles quoting, and generally does the right thing without you fiddling with format strings. For Parquet files, DuckDB applies column pruning and predicate pushdown, reading only the columns and row groups your query actually needs.

## The Relation API: Lazy, Chainable, Optional

Beyond raw SQL, DuckDB offers a "relation API" that gives you a programmatic, lazy query builder. Think of it as a middle ground between writing SQL strings and using a full ORM.


rel = conn.from_df(df)
result = rel.filter("spend > 40").project("user_id, spend").order("spend").limit(10)
print(result.fetchdf())


Relations are lazily evaluated - nothing executes until you call `.execute()`, `.fetchdf()`, or `.df()`. You can chain `.filter()`, `.project()`, `.aggregate()`, `.join()`, `.distinct()`, `.order()`, and `.limit()` in whatever combination makes sense. It's a nice API for building queries programmatically when the SQL string would get unwieldy with dynamic conditions.

I wouldn't say it replaces SQL for most use cases. SQL is still more expressive and more readable for anything moderately complex. But the relation API is handy for composing query fragments in library code where you don't want to be concatenating strings.

## Performance: What the Numbers Say

DuckDB's performance on single-node analytical workloads is hard to argue with. A community benchmark against BigQuery and Athena on 20GB of ZSTD-compressed Parquet data showed DuckDB Local hitting a warm median of 284 ms with 32 threads and 64GB RAM. BigQuery came in at 2,775 ms and Athena at 4,211 ms for the same 57 queries. That's roughly a 10x advantage over the cloud platforms.

The scaling behavior is predictable too. Going from 4 threads with 8GB RAM to 32 threads with 64GB RAM improved wide-scan performance from 4,971 ms to 995 ms - about a 5x gain for an 8x increase in resources. Not perfectly linear, but consistent enough for capacity planning.

Where DuckDB stumbles is remote storage. Querying Parquet files on Cloudflare R2 introduced cold start overhead of 14–20 seconds due to metadata fetching over the network. Warm queries still performed well (496 ms median on the XL config), but that first-query latency can be painful for interactive workloads. DuckDB is simpler to deploy than cloud query engines, but if your data lives in object storage and you need consistently low first-query latency, a serverless option like Athena avoids that cold start penalty entirely.

## Threading, Concurrency, and the Rough Edges

DuckDB supports multithreaded query execution out of the box, and it parallelizes well across cores. But when you're writing concurrent Python code that shares a connection, there are rules. Each thread should work with its own cursor via `conn.cursor()`. The Python client technically supports PEP 249 cursors, though the documentation calls them "fully redundant" for single-threaded use.

The bigger caveat is write concurrency. DuckDB's MVCC model handles concurrent reads well, but parallel writes to the same records run into limitations. If your workload is read-heavy analytics - aggregations, scans, joins, window functions - DuckDB is excellent. If you need high-concurrency read/write with frequent updates to overlapping rows, you probably want PostgreSQL or MySQL instead.

One more thing: DuckDB uses memory allocators (like jemalloc) that hold onto freed memory in pools for reuse rather than returning it to the OS immediately. This can look like a memory leak in monitoring tools but it's expected behavior. The allocator anticipates future allocations and avoids the cost of repeated system calls to release and reclaim pages.

## Where DuckDB Fits and Where It Doesn't

DuckDB occupies a specific niche well: single-node, read-heavy analytical processing of medium-to-large datasets. Data validation pipelines that used to choke pandas with memory pressure. Ad-hoc exploration of Parquet dumps. Embedded analytics inside applications - the CLI is only 16 MB and the WebAssembly build is 2 MB, small enough to ship inside a product.

So what doesn't it do well? Distributed computing is out of scope. High-concurrency transactional workloads aren't its strength. And if you're managing tables with unique constraints or primary keys, know that DuckDB's ART indexes can cause database file sizes to grow substantially even after deletes - space reclamation with these indexes in place is a known design limitation.

For a getting-started experience, though, the Python client is about as frictionless as it gets. One pip install, one function call to connect, and you're writing SQL against DataFrames, CSVs, and Parquet files. No YAML. No Docker. No cluster. Just a database engine that runs where your code runs and gets out of your way.

That's the pitch, and for once I think the pitch matches reality.
