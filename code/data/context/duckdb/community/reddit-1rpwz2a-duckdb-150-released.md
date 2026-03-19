# DuckDB 1.5.0 released

**r/Python** | Score: 143 | Comments: 9 | Date: 2026-03-10
**Author:** commandlineluser
**URL:** https://www.reddit.com/r/Python/comments/1rpwz2a/duckdb_150_released/

Looks like it was released yesterday:

- https://duckdb.org/2026/03/09/announcing-duckdb-150

Interesting features seem to be the `VARIANT` and `GEOMETRY` types.

Also, the new `duckdb-cli` module on pypi.

    % uv run -w duckdb-cli duckdb -c "from read_duckdb('https://blobs.duckdb.org/data/animals.db', table_name='ducks')"
    ┌───────┬──────────────────┬──────────────┐
    │  id   │       name       │ extinct_year │
    │ int32 │     varchar      │    int32     │
    ├───────┼──────────────────┼──────────────┤
    │     1 │ Labrador Duck    │         1878 │
    │     2 │ Mallard          │         NULL │
    │     3 │ Crested Shelduck │         1964 │
    │     4 │ Wood Duck        │         NULL │
    │     5 │ Pink-headed Duck │         1949 │
    └───────┴──────────────────┴──────────────┘

- https://pypi.org/project/duckdb-cli/
