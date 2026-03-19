# Pattern for bulk insertions from python without column confusion

**Issue #3057** | State: closed | Created: 2022-02-09 | Updated: 2026-03-03
**Author:** rmcgibbo

#### What happens?
From reading other issues like https://github.com/duckdb/duckdb/issues/1293, and browsing github (e.g. https://github.com/MetaTypers/MetaTyping/blob/b7a52a6ceaea23d9a7f0546cc35da04535f61800/meta_typing/application/sql_queries.py#L37-L39), my understanding was that the recommended way to copy data from pandas into a database was to register the pandas dataframe as a view and then use a single statement like `INSERT INTO tbl SELECT * FROM view`.

I was having good luck with this pattern, until I started getting some messed up data and figured out that this pattern is prone to cause confusion between the columns, because this doesn't actually ensure that the order of the columns match up properly.

My questions / bug reports are:
1. Is there a better way to bulk-insert data from a pandas dataframe into an on-disk database?
2. Is there anything that could or should be done in the `INSERT INTO x SELECT * FROM y` pattern to prevent this foot-gun?

#### To Reproduce
````
> import duckdb
> df = pd.DataFrame(dict(foo=[1,2,3], bar=[7,8,9]))
> con = duckdb.connect(":memory:")
> con.execute("CREATE TABLE items(bar INTEGER, foo INTEGER);").fetchone()
> con.register("items_view", df)
> con.execute("INSERT INTO items SELECT * FROM items_view")
> con.unregister("items_view")
> con.execute("select * from items").fetchdf()
   bar  foo
0    1    7
1    2    8
2    3    9
# Look -- the two columns have been silently swapped!
````


#### Environment:
 - OS: Linux
 - DuckDB Version: 0.3.1
 - DuckDB Client: Python

## Comments

**l1t1:**
INSERT INTO items (foo,bar)SELECT foo,bar FROM items_view

**rmcgibbo:**
There are dedicated functions to insert into a table (rather than a view) for CSV and Parquet, right? It seems like something similar could be useful for python/pandas.

**Alex-Monahan:**
Hello!

Another option is:

```sql
CREATE TABLE items as
SELECT * FROM my_dataframe
```

No register is needed and no view creation is needed either!

**rmcgibbo:**
Wow, magic
```
In [15]: con = duckdb.connect(":memory:")

In [16]: df = pd.DataFrame(dict(foo=[1,2,3], bar=[7,8,9]))

In [17]: con.execute("CREATE TABLE items AS SELECT * FROM df")
Out[17]: 

In [18]: print(con.execute("select * from items").fetchdf())
   foo  bar
0    1    7
1    2    8
2    3    9
```

I didn't realize it could reach into my local variables like that!

Something for https://duckdb.org/docs/api/python

**dandavison:**
>  Look -- the two columns have been silently swapped!

For the record, it looks like what's going on is not that they have been swapped, but that it's ignoring the column names in the dataframe. E.g., a modification of your example
```
df = pd.DataFrame(dict(foo=[1,2,3], bar=[7,8,9]))
...
con.execute("CREATE TABLE items(xxx INTEGER, yyy INTEGER);").fetchone()
...
```

shows that the table created doesn't have any columns named foo or bar:

```
In [17]: con.execute("select * from items").fetchdf()
Out[17]:
   xxx  yyy
0    1    7
1    2    8
2    3    9
```

**joleczka1988:**
my_data = {
    "name": "Jolanta Korman",
    "location": "Poznań, Poland",
    "test_history": {
        "HLA-B27": "Unknown",
        "Haemoglobin (Hb)": "12.2 g/dL",
        "Hematocrit (Hct)": "36.7%",
        "Platelet Count": "1.1 million (High)"
    },
    "clinical_observations": [
        "Rouleaux formation (RBC stacking)",
        "Blue background on peripheral blood smear",
        "Elevated Serum Free Light Chain"
    ],
    "diagnostic_context": "Plasma cell disorder investigation (Multiple Myeloma)"
}
