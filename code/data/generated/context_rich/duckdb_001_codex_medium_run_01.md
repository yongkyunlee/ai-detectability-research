# Getting started with the DuckDB Python client

DuckDB’s Python client is useful when you want database-style analytics without setting up a database server. The project positions DuckDB as an embedded analytical database: you open a connection inside your Python process, query local files or in-memory objects with SQL, and fetch results back into Python-native data structures. That makes it a strong fit for notebooks, scripts, ETL helpers, test fixtures, and local analytics features inside applications.

The first thing to understand is that the Python client is not just a thin SQL wrapper. It gives you two complementary ways to work:

1. A SQL execution API built around `connect()`, `execute()`, and fetch methods.
2. A relation API that lets you build lazy query pipelines in Python before materializing results.

For most users, the easiest starting point is a plain connection:

```python
import duckdb

con = duckdb.connect()
```

With no path argument, DuckDB opens a temporary in-memory database. That is a good default for exploratory work, tests, and one-off scripts. If you want persistence, pass a database file path instead and DuckDB will store tables on disk.

Once connected, you can execute SQL immediately:

```python
con.execute("CREATE TABLE items(id INTEGER, name VARCHAR)")
con.execute("INSERT INTO items VALUES (1, 'apple')")
con.execute("INSERT INTO items VALUES (?, ?)", [2, "pear"])
con.executemany(
    "INSERT INTO items VALUES (?, ?)",
    [[3, "orange"], [4, "banana"]],
)
```

The Python example in the repository shows three patterns worth remembering. First, parameter binding is supported, so you do not need to interpolate values into SQL strings. Second, `executemany()` is available when you already have rows in Python form. Third, fetch methods are flexible: you can return a Pandas DataFrame with `fetchdf()`, NumPy-friendly arrays with `fetchnumpy()`, or row-oriented results with `fetchone()` and `fetchall()`.

Another strength of the client is how directly it connects SQL to Python data objects. The bundled examples and regression tests show several ways to expose a DataFrame to DuckDB. One is explicit registration:

```python
con.register("sales_df", sales_df)
result = con.execute("""
    SELECT region, sum(amount) AS total
    FROM sales_df
    GROUP BY region
""").fetchdf()
```

DuckDB can also discover a DataFrame from Python scope and query it directly with `SELECT * FROM df_name`. That shortcut is convenient, but explicit registration is usually clearer in production code.

There is an important foot-gun here. A long-running issue discussion shows that `INSERT INTO target SELECT * FROM some_dataframe_view` can silently misalign data when the destination table’s column order differs from the DataFrame’s column order. The safe pattern is to list columns explicitly, or create the table directly from the DataFrame with `CREATE TABLE ... AS SELECT * FROM df`.

If you prefer a more composable style than raw SQL strings, the relation API is worth learning early. In the project’s Python example, relations are described as lazily evaluated chains of relational operators. You can create one from a DataFrame, a CSV file, or an existing DuckDB table:

```python
rel = con.from_df(sales_df)
top_regions = (
    rel.filter("amount > 0")
       .aggregate("region, sum(amount) AS total")
       .order("total DESC")
       .limit(10)
)
df = top_regions.df()
```

This style is appealing when you want readable, incremental transformations without building one large SQL string. The same example covers familiar operations such as `project`, `filter`, `order`, `limit`, `aggregate`, `distinct`, `union`, and `join`. Because relations are lazy, computation happens when you materialize the result with methods like `df()`, `fetchall()`, `arrow()`, or `execute()`.

DuckDB’s file access story is another reason the Python client is easy to adopt. The main project README emphasizes that CSV and Parquet files can be queried directly in the `FROM` clause. In practice, that means you can start analyzing data before designing schemas or loading tables:

```python
result = con.execute("""
    SELECT customer_id, sum(amount) AS revenue
    FROM 'orders.parquet'
    GROUP BY customer_id
    ORDER BY revenue DESC
    LIMIT 20
""").fetchdf()
```

The repository examples also use `from_csv_auto`, which is a good reminder that DuckDB is comfortable treating files as queryable relations. Community discussions repeatedly point to this “SQL over files” workflow as a major strength, especially for medium-sized analysis and validation tasks that would otherwise strain Pandas memory.

A few operational caveats matter even for beginners. DuckDB is optimized for analytics, not for acting like a networked OLTP database. Community discussions regularly draw that line: it shines on single-node, read-heavy analytical work, but it is a weaker fit for high-concurrency read/write workloads. Python-specific issues reinforce that message. One recent bug report showed a crash on DuckDB 1.3.0 when two Python threads created cursors from the same connection and issued conflicting upserts. Maintainers noted that newer versions no longer reproduced the problem. The practical advice is straightforward: upgrade aggressively, and do not treat DuckDB as your default choice for heavily contended transactional writes.

Even in less dramatic cases, concurrency deserves care. The docs referenced in that issue recommend using `conn.cursor()` to create thread-local handles for multiple threads. That is useful guidance, but it should be read as “careful concurrent access for analytical workflows,” not “this is now a full multi-writer server database.”

The simplest way to get productive with DuckDB Python is to keep the boundary clear. Use SQL for scans, joins, and aggregation. Use DataFrames or Arrow tables at the edges when you need to interoperate with the rest of the Python ecosystem. Start with an in-memory connection, move to an on-disk file when persistence matters, and treat the relation API as an optional upgrade once you want more composable pipelines. If your workload is local, analytical, and centered on files or in-process data structures, DuckDB gives you a surprisingly capable database without leaving Python.
