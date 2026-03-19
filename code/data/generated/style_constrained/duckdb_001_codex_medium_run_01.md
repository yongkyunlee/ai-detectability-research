# Getting Started with the DuckDB Python Client

DuckDB’s Python client is what an embedded analytical database should look like. You import a module, open a connection, and run SQL in the same process. No daemon to manage. No server bootstrap step. As of DuckDB 1.5.0, released on March 9, 2026, that model is still the point.

The project’s own Python example keeps the contract small. You call `duckdb.connect()`, execute SQL, and fetch results in the shape your pipeline needs.

Start with the connection, not with abstractions around it. The example in `examples/python/duckdb-python.py` opens an in-memory database with no arguments:

```python
import duckdb

con = duckdb.connect()
con.execute("CREATE TABLE test_table (i INTEGER, j STRING)")
con.execute("INSERT INTO test_table VALUES (?, ?)", [2, "two"])
con.executemany(
    "INSERT INTO test_table VALUES (?, ?)",
    [[3, "three"], [4, "four"]],
)
```

DuckDB isn’t asking Python developers to learn a separate client protocol. It’s an embedded engine with a Python API on top. The example also points out that `cursor()` exists for DB-API compatibility but is “fully redundant.” I’d treat that as guidance. Use a cursor when an integration layer requires it, not because normal DuckDB code needs one.

So the first mental model is simple: the connection is your execution context. Keep one when you want control over state, tables, and settings. Create a persistent database file when you need durability, or stay in memory when the job is transient. The regression script also sets connection-level options like `SET threads=...`, which is a reminder that execution policy lives there too.

The second thing to internalize is that DuckDB wants you to query data where it already is. The top-level README makes that explicit for files. For CSV and Parquet, import can be as simple as:

```sql
SELECT * FROM 'myfile.csv';
SELECT * FROM 'myfile.parquet';
```

That changes the shape of the program. You don’t have to load a file into pandas first just to make it queryable. Python can orchestrate. DuckDB can scan.

But the Python client doesn’t force you into file-first workflows either. The example registers a pandas DataFrame as a view with `con.register("test_df", test_df)` and then runs SQL against it. It also shows `con.from_df(test_df)` and the shorthand `duckdb.df(test_df)`, both of which return relations instead of immediate results.

Here there’s a real trade-off, and the project materials make it visible. Querying files directly is simpler when the source of truth is already a CSV or Parquet file. Registering a DataFrame or creating a relation gives you a stable bridge when the data already lives in Python memory. DuckDB can also reach into Python scope directly. In Issue #3057, a maintainer suggested `CREATE TABLE items AS SELECT * FROM df` without an explicit `register()`. That’s convenient for quick scripts. But I’d still prefer explicit registration in application code because the dependency is named instead of hidden in local variables.

Issue #3057 is also a good lesson in being explicit about inserts. The report showed a DataFrame with columns `foo` and `bar` being inserted into a table defined as `(bar INTEGER, foo INTEGER)`. The statement `INSERT INTO items SELECT * FROM items_view` loaded values by position, not by matching names, so the data landed in the wrong columns on DuckDB 0.3.1. If column order matters, say so:

```sql
INSERT INTO items (foo, bar)
SELECT foo, bar FROM items_view;
```

We’ve all seen bugs caused by “obvious” positional assumptions. This one is easy to avoid.

DuckDB’s relation API is the other half of the Python story. The example calls relations “lazily evaluated chains of relational operators,” and that description is accurate. You can build a query step by step with operations like `filter`, `project`, `order`, `limit`, and `join`, then execute at the end. For example:

```python
rel = con.from_df(test_df)
result = rel.filter("i > 1").project("i + 1, j").order("j").limit(2)
```

I wouldn’t force everything through relations. If the query is already natural SQL, `con.execute(...)` is simpler. But relations are useful when the query shape is assembled in code and you want something more structured than string concatenation.

Result conversion is where many first-time users leave performance on the table. The example exposes several options immediately: `fetchall()`, `fetchone()`, `fetchdf()`, `fetchnumpy()`, relation `.df()`, relation `.to_df()`, and Arrow output through `.arrow()`. That isn’t API clutter. It reflects a real design choice.

The repository’s Python regression benchmark reinforces that point. It compares native tuple fetching, pandas DataFrame conversion, and Arrow conversion on TPC-H data, with tests at 2,048, 50,000, and 2,500,000 rows. There’s also an Arrow dictionary benchmark that generates 10,000,000 values. The intent is obvious: the format you fetch into is part of query planning.

`fetchall()` is fine for small control-plane queries or test assertions. It’s the wrong default for large analytical outputs because you’re materializing a pile of Python tuples. If the next step is pandas, use `fetchdf()` or `.df()`. If the next step is Arrow-native tooling, fetch Arrow directly.

One more boundary is worth being blunt about. DuckDB’s Python client is for embedded analytics, not for pretending your process now contains a general-purpose OLTP server. A February 28, 2026 issue reported a crash in DuckDB 1.3.0 when two Python threads created cursors from the same connection and repeatedly executed `INSERT ... ON CONFLICT DO UPDATE`. Maintainers said they could no longer reproduce it on 1.4.3 LTS and 1.5.0-dev, which is a useful reminder to upgrade first and test your exact concurrency pattern.

And the community discussion around DuckDB still frames the workload fit the same way: excellent for single-node, read-heavy analytical work, weaker for high-concurrency read/write patterns. That doesn’t diminish the Python client. It just tells you where it’s strongest.

If you’re getting started, I’d keep the first version boring. Install with `pip install duckdb --upgrade`. Open a connection. Query a Parquet file directly. Register a DataFrame only when the data is already in memory. Prefer explicit column lists on inserts. And choose your fetch format on purpose. DuckDB’s Python client is good because it stays small, close to SQL, and honest about the job it’s built to do.
